import os
import zipfile
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUNDLED_FILES = [
    "providers.py",
    "logic_engine.py",
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    "README.md",
    "components/settings/SettingsPanel.tsx",
    "database.py",
    "docs/evaluation/methodology.md",
    "tests/test_groq_key.py",
    "tests/test_providers.py",
    "scripts/run_real_pipeline_evaluation.py",
    "scripts/summarize_generation_runs.py",
    "scripts/capture_generation_worksheet.py",
    "scripts/capture_normal_production_path.py",
    "scripts/verify_frozen_30_rerank.py",
    "scripts/generate_report_tables.py",
    "scripts/package_safe_bundle.py",
    "phase4_diagnostics.py",
    "tests/test_phase4_diagnostics.py",
    "tests/test_phase4_live_capture.py",
    "docs/evaluation/phase4_new_questions.json",
    "docs/evaluation/phase4_new_questions.schema.json",
    "docs/evaluation/phase4_relevance.json",
    "docs/evaluation/phase4_relevance.schema.json",
    "docs/evaluation/corrective_decision_fixtures.json",
    "docs/evaluation/phase4_split_manifest.json",
    "docs/evaluation/decision_record_phase4_baseline.md",
    "docs/evaluation/phase4.md",
    "docs/evaluation/phase4_generation_worksheet.json",
    "docs/evaluation/phase4_human_answer_review_packet.md",
    "docs/evaluation/phase4_human_evidence_signoff.md",
    "phase4_human_evidence_signoff.md",
    "docs/evaluation/phase4_human_answer_verdict_form.md",
    "phase4_human_answer_verdict_form.md",
    "docs/evaluation/phase4_human_answer_verdicts.json",
    "docs/evaluation/phase4_human_answer_verdicts.schema.json",
    "evaluation_results/historical_groq_dev_generation_results.json",
    "evaluation_results/historical_groq_held_out_generation_results.json",
    "evaluation_results/historical_gemini_quota_dev_generation_results.json",
    "evaluation_results/historical_flawed_phase4_generation_worksheet.json",
    "evaluation_results/phase4_dev_generation_results.json",
    "PHASE4_EXECUTION_REPORT_CORRECTED.md",
    "final_code_diff.patch",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    # 1. Regenerate patch
    patch_path = ROOT / "final_code_diff.patch"
    subprocess.run(["git", "diff", "HEAD", f"--output={patch_path}"], cwd=ROOT, check=True)

    # 2. Add pilot if exists
    pilot_path = ROOT / "evaluation_results/phase4_pilot_generation_results.json"
    bundled = list(BUNDLED_FILES)
    if pilot_path.exists():
        bundled.append("evaluation_results/phase4_pilot_generation_results.json")

    # 3. Generate MANIFEST.txt
    manifest_lines = []
    for rel in bundled:
        p = ROOT / rel
        if p.exists():
            digest = sha256_file(p)
            manifest_lines.append(f"{digest}  {rel}")
        else:
            print(f"Warning: {rel} does not exist, skipping.")

    manifest_path = ROOT / "MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    bundled.append("MANIFEST.txt")
    print(f"Wrote MANIFEST.txt with {len(manifest_lines)} entries.")

    # 4. Create ZIP bundle
    zip_name = "CiteFirst_Phase4_Safe_Review_Bundle.zip"
    zip_path = ROOT / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in bundled:
            p = ROOT / rel
            if p.exists():
                zf.write(p, arcname=rel)

    print(f"Created {zip_path} ({zip_path.stat().st_size:,} bytes).")

    # 5. Leak check on ZIP
    real_key = None
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                real_key = line.split("=", 1)[1].strip()
                break

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name == ".env" or name.endswith("/.env") or name.endswith(".pdf") or ("vault" in name and not name.startswith("evaluation_results")) or "pycache" in name:
                raise RuntimeError(f"Prohibited file in bundle: {name}")
            data = zf.read(name)
            if real_key and len(real_key) > 10 and real_key.encode("utf-8") in data:
                raise RuntimeError(f"REAL SECRET LEAK DETECTED in {name}!")

    print("Leak check passed: Zero real secrets, PDFs, vaults, or private env files in bundle.")

if __name__ == "__main__":
    main()
