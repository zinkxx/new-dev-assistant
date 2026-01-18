import argparse
from pathlib import Path

from scanner import scan_project, SCAN_DEV, SCAN_PROD
from report_html import write_html_report


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

    # ---- CLI summary ----
    risks = sum(1 for f in findings if f.kind == "RISK")
    todos = sum(1 for f in findings if f.kind == "TODO")

    print("\n=== Scan Summary ===")
    print(f"Risks found : {risks}")
    print(f"TODOs found : {todos}")
    print(f"Report path : {report_path}")

    print("\n[✓] Scan completed successfully")
