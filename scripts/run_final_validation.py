"""
Executes the full required validation suite and writes VALIDATION_LOG.txt
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

COMMANDS = [
    ("python -m pytest -rs -v tests", ["python", "-m", "pytest", "-rs", "-v", "tests"]),
    ("python -m compileall -q api.py database.py evaluator.py evaluation logic_engine.py providers.py settings_config.py tests",
     ["python", "-m", "compileall", "-q", "api.py", "database.py", "evaluator.py", "evaluation", "logic_engine.py", "providers.py", "settings_config.py", "tests"]),
    ("npm run lint", ["npm.cmd", "run", "lint"]),
    ("npx tsc --noEmit", ["npx.cmd", "tsc", "--noEmit"]),
    ("npm run build", ["npm.cmd", "run", "build"]),
    ("git diff --check", ["git", "diff", "--check"]),
]

def main():
    log_lines = [
        f"CiteFirst Phase 4 Final Validation Log",
        f"Timestamp: {datetime.now().isoformat()}",
        f"Workspace Root: {ROOT}",
        "=" * 80,
        ""
    ]

    all_passed = True

    for cmd_str, cmd_args in COMMANDS:
        log_lines.append(f"COMMAND: {cmd_str}")
        print(f"Running: {cmd_str}...")
        res = subprocess.run(cmd_args, cwd=str(ROOT), capture_output=True, text=True)
        log_lines.append(f"EXIT CODE: {res.returncode}")
        if res.stdout:
            log_lines.append("STDOUT:")
            log_lines.append(res.stdout.strip())
        if res.stderr:
            log_lines.append("STDERR:")
            log_lines.append(res.stderr.strip())
        log_lines.append("-" * 80)
        log_lines.append("")

        print(f"  Exit code: {res.returncode}")
        if res.returncode != 0:
            all_passed = False

    summary = "ALL 6 VALIDATION CHECKS PASSED (EXIT CODE 0)" if all_passed else "VALIDATION FAILED"
    log_lines.insert(4, f"OVERALL STATUS: {summary}\n")
    print(f"\n{summary}")

    out_file = ROOT / "VALIDATION_LOG.txt"
    out_file.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote validation log to {out_file}")

if __name__ == "__main__":
    main()
