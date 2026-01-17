from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import load_config
from ipc import write_status   # 👈 progress IPC
import time
from datetime import datetime


# --------------------------------------------------
# Scan modes
# --------------------------------------------------
SCAN_DEV = "dev"
SCAN_PROD = "prod"

# --------------------------------------------------
# File handling
# --------------------------------------------------
TEXT_EXTS = {
    ".php", ".js", ".ts", ".vue", ".html", ".css",
    ".json", ".md", ".py", ".env", ".yml", ".yaml",
    ".ini", ".conf",
}

IGNORE_DIRS = {
    ".git", "vendor", ".venv",
    "dist", "build", ".next", ".nuxt",
    ".idea", ".vscode", "__pycache__", ".pytest_cache",
}

# --------------------------------------------------
# Security patterns
# --------------------------------------------------
SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]+['\"]", re.I),
    re.compile(r"(api[_-]?key|secret|token|password)\s*:\s*['\"][^'\"]+['\"]", re.I),
]

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

IGNORE_FILE_MARKER = "@zinkx-ignore-security"
DANGEROUS_FUNCS = [
    "eval(",
    "exec(",
    "shell_exec(",
    "system(",
    "passthru(",
]
DEBUG_ARTIFACTS = [
    "var_dump(",
    "print_r(",
    "die(",
    "dd(",
]
SEVERITY_SCORES = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MEDIUM": 8,
    "LOW": 3,
}



# --------------------------------------------------
# Models
# --------------------------------------------------
@dataclass
class Finding:
    kind: str                    # RISK | TODO | INFO
    severity: str                # CRITICAL | HIGH | MEDIUM | LOW
    score: int                   # risk score impact

    title: str
    detail: str
    path: str
    line: int | None = None

    explanation: str | None = None
    recommendation: str | None = None


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _is_ignored_dir(p: Path, cfg) -> bool:
    if cfg.get("ignore_node_modules", True) and "node_modules" in p.parts:
        return True
    return any(part in IGNORE_DIRS for part in p.parts)


def _safe_read_text(path: Path, limit_bytes: int = 400_000) -> str:
    try:
        if path.stat().st_size > limit_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _emit_progress(percent: int, mode: str):
    """
    UI için progress IPC
    """
    write_status({
        "type": "progress",
        "percent": percent,
        "mode": mode,
    })


# --------------------------------------------------
# Main scanner
# --------------------------------------------------
def scan_project(
    root: str,
    mode: str = SCAN_DEV,
    only_files: list[str] | None = None,
) -> list[Finding]:

    cfg = load_config()

    ignore_markers = tuple(cfg.get("ignore_inline_markers", []))
    progress_steps = cfg.get("scan_progress_steps", [20, 50, 80, 100])
    show_progress = cfg.get("show_scan_progress", True)

    rootp = Path(root).expanduser().resolve()
    findings: list[Finding] = []
    start_ts = time.perf_counter()
    scanned_files = 0

    if not rootp.exists() or not rootp.is_dir():
        return findings

    # --------------------------------------------------
    # File iterator
    # --------------------------------------------------
    if only_files:
        file_iter = [Path(p) for p in only_files if Path(p).is_file()]
    else:
        file_iter = list(rootp.rglob("*"))

    total_files = len(file_iter) or 1
    next_progress_index = 0

    def update_progress(done: int):
        nonlocal next_progress_index
        if not show_progress:
            return
        percent = int((done / total_files) * 100)
        if next_progress_index < len(progress_steps):
            if percent >= progress_steps[next_progress_index]:
                _emit_progress(progress_steps[next_progress_index], mode)
                next_progress_index += 1

    # --------------------------------------------------
    # 1️⃣ .env git ignore check
    # --------------------------------------------------
    if cfg.get("ignore_env", True):
        env_file = rootp / ".env"
        if env_file.exists():
            gitignore = rootp / ".gitignore"
            gi = _safe_read_text(gitignore) if gitignore.exists() else ""
            if ".env" not in gi:
                findings.append(Finding(
                    kind="RISK",
                    severity="CRITICAL",
                    score=SEVERITY_SCORES["CRITICAL"],

                    title=".env may be tracked",
                    detail="Project has .env but .gitignore does not mention it.",
                    path=str(env_file),

                    explanation=(
                        ".env files usually contain secrets such as database "
                        "credentials or API keys."
                    ),
                    recommendation=(
                        "Add `.env` to your .gitignore file and rotate exposed secrets."
                    ),
                ))

    # --------------------------------------------------
    # 1B) Project structure checks (root-level hygiene)
    # --------------------------------------------------
    # README / LICENSE / requirements.txt / .gitignore gibi temel dosyalar
    root_checks = [
        ("README.md", "INFO", "Missing README.md",
         "README helps others understand and use the project.",
         "Create a README.md explaining setup, usage, and features."),
        ("LICENSE", "INFO", "Missing LICENSE",
         "A license clarifies how others can use your code.",
         "Add a LICENSE file (e.g., MIT) to define usage rights."),
        (".gitignore", "INFO", "Missing .gitignore",
         "Without .gitignore, sensitive or bulky files may be committed.",
         "Add a .gitignore suitable for your stack (Python, Node, etc.)."),
        ("requirements.txt", "INFO", "Missing requirements.txt",
         "Dependencies are unclear without a requirements file.",
         "Add requirements.txt (pip freeze) or use pyproject.toml."),
    ]

    for filename, kind, title, explanation, recommendation in root_checks:
        f = rootp / filename
        if not f.exists():
            findings.append(Finding(
                kind=kind,
                severity="LOW",
                score=SEVERITY_SCORES["LOW"],

                title=title,
                detail=f"{filename} not found in project root.",
                path=str(f),

                explanation=explanation,
                recommendation=recommendation,
            ))



    # --------------------------------------------------
    # 2️⃣ File scanning
    # --------------------------------------------------
    for idx, p in enumerate(file_iter, start=1):
        update_progress(idx)

        if p.is_dir():
            continue
        if _is_ignored_dir(p, cfg):
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        
        scanned_files += 1

        text = _safe_read_text(p)
        if not text:
            continue

        if IGNORE_FILE_MARKER in text:
            continue

        lines = text.splitlines()
        # ----------------------------------------------
        # General checks (language-agnostic)
        # ----------------------------------------------
        # Çok uzun satır / trailing whitespace gibi hijyen kontrolleri
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            if any(m in low for m in ignore_markers):
                continue

            # Long line (readability)
            if len(line) > 240:
                findings.append(Finding(
                    kind="INFO",
                    severity="LOW",
                    score=SEVERITY_SCORES["LOW"],

                    title="Long line",
                    detail=line.strip()[:240],
                    path=str(p),
                    line=i,

                    explanation="Very long lines reduce readability and make reviews harder.",
                    recommendation="Consider wrapping the line or refactoring into smaller pieces.",
                ))


            # Trailing whitespace (cleanliness)
            if line.rstrip("\n\r") != line.rstrip("\n\r ").rstrip("\t"):
                findings.append(Finding(
                    kind="INFO",
                    severity="LOW",
                    score=SEVERITY_SCORES["LOW"],

                    title="Trailing whitespace",
                    detail=line.strip()[:240],
                    path=str(p),
                    line=i,

                    explanation="Trailing whitespace creates noisy diffs and reduces code clarity.",
                    recommendation="Trim trailing spaces/tabs (editor setting: trim on save).",
                ))


        # ----------------------------------------------
        # TODO / FIXME
        # ----------------------------------------------
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            if any(m in low for m in ignore_markers):
                continue

            tags = ["todo", "fixme", "hack", "bug", "xxx", "note", "optimize"]
            if any(t in low for t in tags):

                findings.append(Finding(
                    kind="TODO",
                    severity="LOW",
                    score=SEVERITY_SCORES["LOW"],

                    title="Dev note found (TODO/FIXME/HACK/BUG)",
                    detail=line.strip()[:240],
                    path=str(p),
                    line=i,

                    explanation=(
                        "TODO or FIXME comments indicate unfinished or temporary "
                        "code that may be forgotten over time."
                    ),
                    recommendation=(
                        "Review this comment and either complete the implementation "
                        "or remove the TODO/FIXME if it is no longer needed."
                    ),
                ))

        

        # ----------------------------------------------
        # PHP specific checks
        # ----------------------------------------------
        if p.suffix.lower() == ".php":
            for i, line in enumerate(lines, start=1):
                low = line.lower()
                if any(m in low for m in ignore_markers):
                    continue

                for pat in SECRET_PATTERNS:
                    if pat.search(line):
                        findings.append(Finding(
                            kind="RISK",
                            severity="CRITICAL" if mode == SCAN_PROD else "HIGH",
                            score=SEVERITY_SCORES["CRITICAL" if mode == SCAN_PROD else "HIGH"],

                            title="Hardcoded secret",
                            detail=line.strip()[:240],
                            path=str(p),
                            line=i,

                            explanation="Hardcoded secrets can be exposed through version control.",
                            recommendation="Move secrets to environment variables or a secret manager.",
                        ))

                        break
                
                # ----------------------------------------------
                # Debug artifacts (var_dump, print_r, die, dd)
                # ----------------------------------------------
                for dbg in DEBUG_ARTIFACTS:
                    if dbg in low:
                        findings.append(Finding(
                            kind="RISK",
                            severity="HIGH" if mode == SCAN_PROD else "MEDIUM",
                            score=SEVERITY_SCORES["HIGH" if mode == SCAN_PROD else "MEDIUM"],

                            title="Debug artifact found",
                            detail=line.strip()[:240],
                            path=str(p),
                            line=i,

                            explanation="Debug calls left in code can expose data and break execution flow.",
                            recommendation="Remove debug calls or guard them behind a debug flag.",
                        ))

                        break

                # ----------------------------------------------
                # Dangerous functions (eval/system/exec etc.)
                # ----------------------------------------------
                for fn in DANGEROUS_FUNCS:
                    if fn in low:
                        severity = "RISK"  # her zaman risk
                        findings.append(Finding(
                            kind="RISK",
                            severity="CRITICAL",
                            score=SEVERITY_SCORES["CRITICAL"],

                            title="Dangerous function usage",
                            detail=line.strip()[:240],
                            path=str(p),
                            line=i,

                            explanation=(
                                "Functions like eval/exec/system can lead to remote code execution "
                                "if input is not strictly controlled."
                            ),
                            recommendation=(
                                "Avoid these functions entirely. If unavoidable, strictly validate "
                                "input and restrict execution scope."
                            ),
                        ))
                        break


                if EMAIL_PATTERN.search(line):
                    if ".env" not in p.name.lower():
                        findings.append(Finding(
                            kind="INFO",
                            severity="LOW",
                            score=SEVERITY_SCORES["LOW"],

                            title="Hardcoded email",
                            detail=line.strip()[:240],
                            path=str(p),
                            line=i,

                            explanation=(
                                "Email addresses hardcoded in source files may expose "
                                "personal data or become outdated."
                            ),
                            recommendation=(
                                "Move email addresses to configuration files or "
                                "environment variables if possible."
                            ),
                        ))



                if "display_errors" in low and "ini_set" in low:
                    sev = "CRITICAL" if mode == SCAN_PROD else "MEDIUM"

                    findings.append(Finding(
                        kind="RISK",
                        severity=sev,
                        score=SEVERITY_SCORES[sev],

                        title="display_errors enabled",
                        detail=line.strip()[:240],
                        path=str(p),
                        line=i,

                        explanation=(
                            "display_errors enabled may expose stack traces or "
                            "sensitive application details to users."
                        ),
                        recommendation=(
                            "Disable display_errors in production and log errors "
                            "to a secure location instead."
                        ),
                    ))




                if "error_reporting" in low and "e_all" in low:
                    sev = "CRITICAL" if mode == SCAN_PROD else "LOW"

                    findings.append(Finding(
                        kind="RISK",
                        severity=sev,
                        score=SEVERITY_SCORES[sev],

                        title="error_reporting(E_ALL)",
                        detail=line.strip()[:240],
                        path=str(p),
                        line=i,

                        explanation=(
                            "error_reporting(E_ALL) may expose notices and warnings "
                            "that are not intended for end users."
                        ),
                        recommendation=(
                            "Limit error reporting in production environments "
                            "and use logging for diagnostics."
                        ),
                    ))



        # ----------------------------------------------
        # Large file warning
        # ----------------------------------------------
        try:
            size = p.stat().st_size
            if size > 700_000:
                findings.append(Finding(
                    kind="INFO",
                    severity="LOW",
                    score=SEVERITY_SCORES["LOW"],

                    title="Large file",
                    detail=f"File is {size / 1024:.0f} KB",
                    path=str(p),

                    explanation=(
                        "Very large source files can negatively impact "
                        "readability, maintainability, and performance."
                    ),
                    recommendation=(
                        "Consider splitting this file into smaller modules "
                        "with clear responsibilities."
                    ),
                ))
        except Exception:
            pass

    # --------------------------------------------------
    # Final progress
    # --------------------------------------------------
    if show_progress:
        _emit_progress(100, mode)

    # --------------------------------------------------
    # Risk summary (by severity)
    # --------------------------------------------------
    risk_summary = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for f in findings:
        if f.kind == "RISK" and f.severity in risk_summary:
            risk_summary[f.severity] += 1

    # --------------------------------------------------
    # Overall risk level
    # --------------------------------------------------
    if risk_summary["CRITICAL"] > 0:
        risk_level = "CRITICAL"
    elif risk_summary["HIGH"] >= 3:
        risk_level = "WARNING"
    elif sum(risk_summary.values()) > 0:
        risk_level = "REVIEW"
    else:
        risk_level = "SAFE"

    # --------------------------------------------------
    # Human recommendation
    # --------------------------------------------------
    if risk_level == "CRITICAL":
        recommendation = "Fix CRITICAL issues before production deployment."
    elif risk_level == "WARNING":
        recommendation = "High-risk issues detected. Review before release."
    elif risk_level == "REVIEW":
        recommendation = "Minor risks found. Consider cleanup."
    else:
        recommendation = "No significant risks detected. Safe to proceed."





    # --------------------------------------------------
    # Risk score calculation
    # --------------------------------------------------
    total_risk_score = sum(
        f.score for f in findings if f.kind == "RISK"
    )



    # --------------------------------------------------
    # Top risky files
    # --------------------------------------------------
    file_risk_map: dict[str, int] = {}

    for f in findings:
        if f.kind == "RISK":
            file_risk_map[f.path] = file_risk_map.get(f.path, 0) + f.score

    top_risky_files = [
        path for path, _ in sorted(
            file_risk_map.items(),
            key=lambda x: x[1],
            reverse=True
        )
    ][:5]

    # --------------------------------------------------
    # Done status (for Dashboard "Last Scan Details")
    # --------------------------------------------------
    duration = time.perf_counter() - start_ts

    # count risks / todos for quick UI summary
    last_risks = sum(1 for f in findings if f.kind == "RISK")
    last_todos = sum(1 for f in findings if f.kind == "TODO")

    write_status({
        "type": "done",
        "mode": mode,

        "last_risks": last_risks,
        "last_todos": last_todos,
        "risk_score": total_risk_score,

        "risk_summary": risk_summary,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "top_risky_files": top_risky_files,

        "files_scanned": scanned_files,
        "duration": round(duration, 2),
        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })



    # --------------------------------------------------
    # Sort results
    # --------------------------------------------------
    severity_order = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    findings.sort(
        key=lambda f: (
            severity_order.get(f.severity, 9),
            f.path,
            f.line or 0,
        )
    )


    return findings
