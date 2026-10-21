"""
Creates the safe CiteFirst Phase 4 review bundle ZIP and verifies all contents.
Generates:
1. final_unified_patch.patch relative to base commit 36d088f6799b6fa357cdc96fb50a5310b78844aa
2. Tested git apply in an isolated checkout of base commit
3. Full replacement_files/ directory
4. Programmatic MANIFEST.txt with SHA-256 digests
5. CiteFirst_Phase4_Safe_Review_Bundle.zip
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_COMMIT = "36d088f6799b6fa357cdc96fb50a5310b78844aa"

TRACKED_FILES = [
    "README.md",
    "components/settings/SettingsPanel.tsx",
    "database.py",
    "docs/evaluation/methodology.md",
    "logic_engine.py",
]

NEW_FILES = [
    "PHASE4_EXECUTION_REPORT_CORRECTED.md",
    "docs/evaluation/corrective_decision_fixtures.json",
    "docs/evaluation/decision_record_phase4_baseline.md",
    "docs/evaluation/phase4.md",
    "docs/evaluation/phase4_generation_worksheet.json",
    "docs/evaluation/phase4_new_questions.json",
    "docs/evaluation/phase4_new_questions.schema.json",
    "docs/evaluation/phase4_relevance.json",
    "docs/evaluation/phase4_relevance.schema.json",
    "docs/evaluation/phase4_split_manifest.json",
    "phase4_diagnostics.py",
    "scripts/capture_generation_worksheet.py",
    "scripts/capture_normal_production_path.py",
    "scripts/evaluate_corrective_decision.py",
    "scripts/generate_report_tables.py",
    "scripts/inspect_priority_cases.py",
    "scripts/package_review_bundle.py",
    "scripts/run_final_validation.py",
    "scripts/run_real_pipeline_evaluation.py",
    "scripts/summarize_generation_runs.py",
    "scripts/verify_frozen_30_rerank.py",
    "tests/test_phase4_diagnostics.py",
    "tests/test_phase4_live_capture.py",
]

EVAL_OUTPUTS = [
    "evaluation_results/phase4-hybrid.json",
    "evaluation_results/phase4-dense-only.json",
    "evaluation_results/phase4-bm25-only.json",
    "evaluation_results/phase4-hybrid-rerank-30-final.json",
    "evaluation_results/frozen_30_rerank_audit.json",
    "evaluation_results/normal_production_path_trace.json",
    "evaluation_results/corrective_decision_run.json",
    "evaluation_results/phase4_dev_generation_results.json",
    "evaluation_results/phase4_held_out_generation_results.json",
]

def git_blob_sha(content_bytes: bytes) -> str:
    header = f"blob {len(content_bytes)}\0".encode()
    return hashlib.sha1(header + content_bytes).hexdigest()[:7]

def generate_unified_patch() -> Path:
    print(f"Generating unified patch relative to base commit {BASE_COMMIT}...")
    patch_lines = []

    # 1. Diff for tracked modified files
    for tf in TRACKED_FILES:
        res = subprocess.run(
            ["git", "diff", BASE_COMMIT, "--", tf],
            cwd=str(ROOT),
            capture_output=True
        )
        if res.returncode == 0 and res.stdout.strip():
            clean_diff = res.stdout.decode("utf-8").replace("\r\n", "\n")
            patch_lines.append(clean_diff)
            if not clean_diff.endswith("\n"):
                patch_lines.append("\n")

    # 2. Diff for new files
    for nf in NEW_FILES:
        file_path = ROOT / nf
        if not file_path.exists():
            print(f"Warning: {nf} does not exist, skipping in patch")
            continue
        raw_bytes = file_path.read_bytes()
        sha = git_blob_sha(raw_bytes)
        posix_path = nf.replace("\\", "/")

        text = raw_bytes.decode("utf-8")
        lines = text.splitlines(keepends=True)
        count = len(lines)

        patch_lines.append(f"diff --git a/{posix_path} b/{posix_path}\n")
        patch_lines.append("new file mode 100644\n")
        patch_lines.append(f"index 0000000..{sha}\n")
        patch_lines.append("--- /dev/null\n")
        patch_lines.append(f"+++ b/{posix_path}\n")
        patch_lines.append(f"@@ -0,0 +1,{count} @@\n")
        for line in lines:
            if not line.endswith("\n"):
                line += "\n"
            patch_lines.append("+" + line)

    full_patch = "".join(patch_lines)
    patch_path = ROOT / "final_unified_patch.patch"
    patch_path.write_text(full_patch, encoding="utf-8", newline="\n")
    print(f"Wrote {patch_path} ({len(full_patch.splitlines())} lines)")
    return patch_path

def test_patch_in_isolated_dir(patch_path: Path):
    print("Testing patch application in an isolated git worktree / checkout...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Initialize a temporary git repo at BASE_COMMIT
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
        subprocess.run(["git", "remote", "add", "origin", str(ROOT)], cwd=str(tmp_path), capture_output=True, check=True)
        subprocess.run(["git", "fetch", "origin", BASE_COMMIT, "--depth=1"], cwd=str(tmp_path), capture_output=True, check=True)
        subprocess.run(["git", "checkout", "FETCH_HEAD"], cwd=str(tmp_path), capture_output=True, check=True)

        # Apply patch
        apply_res = subprocess.run(
            ["git", "apply", "--check", "--whitespace=nowarn", str(patch_path.resolve())],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )
        if apply_res.returncode != 0:
            print(f"[FAIL] Patch failed in isolated checkout:\n{apply_res.stderr}")
            sys.exit(1)
        print("[SUCCESS] Patch cleanly verified with `git apply --check` in isolated checkout!")

def build_zip_and_manifest(patch_path: Path):
    zip_path = ROOT / "CiteFirst_Phase4_Safe_Review_Bundle.zip"
    staging_dir = ROOT / "scratch" / "_bundle_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy patch
    shutil.copy(patch_path, staging_dir / "final_unified_patch.patch")

    # 2. Copy report
    report_src = ROOT / "PHASE4_EXECUTION_REPORT_CORRECTED.md"
    shutil.copy(report_src, staging_dir / "PHASE4_EXECUTION_REPORT_CORRECTED.md")

    # 3. Copy validation log if present
    val_log = ROOT / "VALIDATION_LOG.txt"
    if val_log.exists():
        shutil.copy(val_log, staging_dir / "VALIDATION_LOG.txt")

    # 4. Copy evaluation results
    eval_dst = staging_dir / "evaluation_results"
    eval_dst.mkdir(parents=True, exist_ok=True)
    for eo in EVAL_OUTPUTS:
        p = ROOT / eo
        if p.exists():
            shutil.copy(p, eval_dst / p.name)
        else:
            print(f"Warning: {eo} does not exist yet")

    # 5. Populate replacement_files directory
    repl_dir = staging_dir / "replacement_files"
    repl_dir.mkdir(parents=True, exist_ok=True)

    all_source_files = TRACKED_FILES + NEW_FILES
    for rel_f in all_source_files:
        src = ROOT / rel_f
        dst = repl_dir / rel_f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    # 6. Safety check: scan staging dir for forbidden files
    forbidden_exts = {".pdf", ".sqlite3", ".bin", ".env", ".pem", ".key", ".pyc"}
    forbidden_names = {"bm25_corpus.json"}
    for f in staging_dir.rglob("*"):
        if f.is_file():
            if f.suffix.lower() in forbidden_exts or f.name in forbidden_names:
                raise RuntimeError(f"Forbidden file detected in bundle: {f}")
            if "vector_vault" in f.parts:
                raise RuntimeError(f"Vector vault detected in bundle: {f}")
            # Check for file:///c: links in portable files
            if f.suffix.lower() in {".md", ".json", ".txt"}:
                text = f.read_text(encoding="utf-8", errors="ignore")
                if "file:///c:" in text.lower() or "file:///c%3a" in text.lower():
                    raise RuntimeError(f"Machine-specific file:///c: URL detected in {f.relative_to(staging_dir)}")

    # 7. Generate programmatic MANIFEST.txt
    manifest_entries = []
    for f in sorted(staging_dir.rglob("*")):
        if f.is_file():
            rel_p = f.relative_to(staging_dir).as_posix()
            sha256 = hashlib.sha256(f.read_bytes()).hexdigest()
            size = f.stat().st_size
            manifest_entries.append((rel_p, sha256, size))

    manifest_lines = [
        "# CiteFirst Phase 4 Safe Review Bundle Manifest",
        f"# Base Commit: {BASE_COMMIT}",
        "# SHA-256 Digest List",
        "",
    ]
    for rel_p, sha256, size in manifest_entries:
        manifest_lines.append(f"{sha256}  {rel_p}  ({size} bytes)")

    manifest_text = "\n".join(manifest_lines) + "\n"
    (staging_dir / "MANIFEST.txt").write_text(manifest_text, encoding="utf-8", newline="\n")
    (ROOT / "MANIFEST.txt").write_text(manifest_text, encoding="utf-8", newline="\n")

    # 8. Create ZIP archive
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(staging_dir.rglob("*")):
            if f.is_file():
                arcname = f.relative_to(staging_dir).as_posix()
                zf.write(f, arcname)

    print(f"\n[SUCCESS] Created {zip_path.name} ({zip_path.stat().st_size / 1024:.1f} KB)")
    print(f"Total files in bundle: {len(manifest_entries) + 1}")

if __name__ == "__main__":
    patch = generate_unified_patch()
    test_patch_in_isolated_dir(patch)
    build_zip_and_manifest(patch)
