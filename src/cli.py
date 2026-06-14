import argparse
import json
from datetime import datetime
from pathlib import Path

from scanner import scan_project, SCAN_DEV, SCAN_PROD
from report_html import write_html_report


def export_json(findings, project_root, scan_mode):
    output = {
        "meta": {
            "project_root": project_root,
            "scan_mode": scan_mode,
            "generated_at": datetime.now().isoformat(),
        },
        "summary": {
            "risks": sum(1 for f in findings if f.kind == "RISK"),
            "todos": sum(1 for f in findings if f.kind == "TODO"),
        },
        "findings": [
            {
                "kind": f.kind,
                "severity": f.severity,
                "score": f.score,
                "title": f.title,
                "detail": f.detail,
                "path": f.path,
                "line": f.line,
                "explanation": f.explanation,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
    }

    out_path = Path(project_root) / "scan_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return out_path


def run_cli():
    parser = argparse.ArgumentParser(
        prog="New Dev Assistant",
        description="CLI interface for scanning projects"
    )

    parser.add_argument(
        "path",
        type=str,
        help="Path to the project directory to scan"
    )

    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Scan mode (default: dev)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Export scan results as JSON"
    )

    args = parser.parse_args()
    project_path = Path(args.path).expanduser().resolve()

    if not project_path.exists():
        raise SystemExit(f"[!] Path not found: {project_path}")

    scan_mode = SCAN_PROD if args.mode == "prod" else SCAN_DEV

    print(f"[+] Scanning project: {project_path}")
    print(f"[+] Mode: {args.mode}")

    findings = scan_project(
        root=str(project_path),
        mode=scan_mode
    )

    report_path = write_html_report(
        findings,
        project_root=str(project_path)
    )

    json_path = None
    if args.json:
        json_path = export_json(
            findings=findings,
            project_root=str(project_path),
            scan_mode=args.mode,
        )

    # ---- CLI summary ----
    risks = sum(1 for f in findings if f.kind == "RISK")
    todos = sum(1 for f in findings if f.kind == "TODO")

    print("\n=== Scan Summary ===")
    print(f"Risks found       : {risks}")
    print(f"TODOs found       : {todos}")
    print(f"Scan mode         : {args.mode}")
    print(f"Scanned directory : {project_path}")
    print(f"HTML report       : {report_path}")

    if json_path:
        print(f"JSON report       : {json_path}")

    print("\n[✓] Scan completed successfully")
