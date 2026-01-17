import os
import subprocess
import rumps

from macos_picker import pick_folder
from scanner import scan_project, SCAN_DEV, SCAN_PROD
from report_html import write_html_report
from install_hook import install_precommit_hook
from datetime import datetime
from settings_ui import (
    open_general_settings,
    open_ignore_settings,
)
from config import load_config
from ipc import (
    read_command,
    clear_command,
    write_status,
    send_command,   # 👈 EKLENDİ
)

def section(title: str):
    item = rumps.MenuItem(title)
    item.enabled = False
    return item


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def open_path(path: str):
    try:
        subprocess.run(["open", path], check=False)
    except Exception as e:
        rumps.alert("Open failed", str(e))


# --------------------------------------------------
# App (Menu Bar)
# --------------------------------------------------
class ZinkxDevAssistant(rumps.App):
    def __init__(self):
        super().__init__(
            "Zinkx",
            icon="assets/icon.png",
            quit_button=None,
        )
        # Header
        header = rumps.MenuItem("🛠 Zinkx Dev Assistant")
        header.enabled = False
        self.menu.add(header)
        self.menu.add(None)
        self.mi_status = rumps.MenuItem("Status: Idle")
        self.mi_status.enabled = False
        self.menu.add(self.mi_status)
        self.menu.add(None)


        # Settings submenu (ÖNCE!)
        settings_menu = rumps.MenuItem("Settings")
        settings_menu.add(rumps.MenuItem("General…", callback=self.open_general_settings))
        settings_menu.add(rumps.MenuItem("Ignore Rules…", callback=self.open_ignore_settings))

        self.menu.add(rumps.MenuItem("🖥 Open Dashboard", callback=self.show_main_window, key="d"))


        self.menu.add(None)
        self.menu.add(section("📁 Project"))
        self.mi_project_info = rumps.MenuItem("No project selected")
        self.mi_project_info.enabled = False
        self.menu.add(self.mi_project_info)
        self.menu.add(rumps.MenuItem("Choose Project Folder…", callback=self.choose_project))

        self.menu.add(None)
        self.menu.add(section("🔍 Scan"))

        self.mi_scan_default = rumps.MenuItem("Scan (Default Mode)", callback=self.scan_default)
        self.mi_scan_dev     = rumps.MenuItem("Scan (Dev Mode)", callback=self.scan_dev)
        self.mi_scan_prod    = rumps.MenuItem("Scan (Prod Mode)", callback=self.scan_prod)

        self.menu.add(self.mi_scan_default)
        self.menu.add(self.mi_scan_dev)
        self.menu.add(self.mi_scan_prod)

        self.menu.add(None)
        self.mi_last_scan = rumps.MenuItem("Last Scan: —")
        self.mi_last_scan.enabled = False
        self.menu.add(self.mi_last_scan)
        self.menu.add(section("📊 Reports"))
        self.mi_open_report = rumps.MenuItem("Open Last Report", callback=self.open_last_report)
        self.mi_open_report.enabled = False
        self.menu.add(self.mi_open_report)


        self.menu.add(None)
        self.menu.add(section("🛠 Tools"))
        self.menu.add(settings_menu)
        self.menu.add(rumps.MenuItem("Install Git Pre-commit Hook", callback=self.install_hook))
        self.menu.add(rumps.MenuItem("Quick Note", callback=self.quick_note))

        self.menu.add(None)
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))


        # macOS hybrid app uyumu
        self.application_supports_secure_restorable_state = True

        # --------------------------------------------------
        # State
        # --------------------------------------------------
        self.state_dir = os.path.expanduser("~/.zinkx_dev_assistant")
        os.makedirs(self.state_dir, exist_ok=True)

        self.project_path_file = os.path.join(self.state_dir, "last_project.txt")
        self.last_report_file = os.path.join(self.state_dir, "last_report.txt")

        self.project_root = self._load_last_project()

        # Scan summary (badge için)
        self.last_risks = 0
        self.last_todos = 0


        # Initial UI state
        self._update_title_badge()
        self._refresh_mode_checks()

        # --------------------------------------------------
        # IPC command listener (Qt → Menu Bar)
        # --------------------------------------------------
        self._cmd_timer = rumps.Timer(self._poll_commands, 1)
        self._cmd_timer.start()

    # --------------------------------------------------
    # IPC
    # --------------------------------------------------
    def _poll_commands(self, _):
        cmd = read_command()
        if not cmd:
            return

        clear_command()

        action = cmd.get("action")
        mode = cmd.get("mode")
        project = cmd.get("project")

        if action == "scan" and project:
            self.project_root = project
            self._save_last_project(project)

            self._scan_with_mode(
                SCAN_PROD if mode == "prod" else SCAN_DEV
            )

            write_status({
                "last_risks": self.last_risks,
                "last_todos": self.last_todos,
                "mode": mode,
            })

    # --------------------------------------------------
    # Menu → Qt
    # --------------------------------------------------
    def show_main_window(self, _):
        send_command({
            "action": "show_window"
        })

    # --------------------------------------------------
    # Badge / Menu State
    # --------------------------------------------------
    def _update_title_badge(self):
        cfg = load_config()
        threshold = int(cfg.get("risk_threshold", 0))

        if self.last_risks > threshold:
            self.title = f"Zinkx  🚨 {self.last_risks}"
        elif self.last_todos > 0:
            self.title = f"Zinkx  ⚠️ {self.last_todos}"
        else:
            self.title = "Zinkx  ✔︎"


    def _refresh_mode_checks(self):
        cfg = load_config()
        mode = cfg.get("default_mode", "dev")

        self.mi_scan_dev.state = 0
        self.mi_scan_prod.state = 0

        if mode == "prod":
            self.mi_scan_prod.state = 1
        else:
            self.mi_scan_dev.state = 1


    # --------------------------------------------------
    # State helpers
    # --------------------------------------------------
    def _load_last_project(self) -> str | None:
        try:
            if os.path.exists(self.project_path_file):
                p = open(self.project_path_file, "r", encoding="utf-8").read().strip()
                return p if p else None
        except Exception:
            pass
        return None

    def _save_last_project(self, path: str):
        with open(self.project_path_file, "w", encoding="utf-8") as f:
            f.write(path)

    def _save_last_report(self, path: str):
        with open(self.last_report_file, "w", encoding="utf-8") as f:
            f.write(path)

    def _load_last_report(self) -> str | None:
        try:
            if os.path.exists(self.last_report_file):
                p = open(self.last_report_file, "r", encoding="utf-8").read().strip()
                return p if p else None
        except Exception:
            pass
        return None

    # --------------------------------------------------
    # Menu actions
    # --------------------------------------------------
    def choose_project(self, _):
        chosen = pick_folder("Choose a project folder to scan")
        if not chosen:
            return

        self.project_root = chosen
        self._save_last_project(chosen)
        rumps.notification("Zinkx", "Project Selected", chosen)

    def scan_default(self, _):
        cfg = load_config()
        mode = cfg.get("default_mode", "dev")
        self._scan_with_mode(SCAN_PROD if mode == "prod" else SCAN_DEV)

    def scan_dev(self, _):
        self._scan_with_mode(SCAN_DEV)

    def scan_prod(self, _):
        self._scan_with_mode(SCAN_PROD)

    # --------------------------------------------------
    # Core scan
    # --------------------------------------------------
    def _scan_with_mode(self, mode: str):
        if not self.project_root or not os.path.isdir(self.project_root):
            rumps.notification(
                "Zinkx",
                "No project selected",
                "Choose a project folder first",
            )
            return

        # 🟢 Scan başladı
        self.mi_status.title = "Status: Scanning…"
        self.mi_last_scan.title = "Last Scan: running…"

        self.mi_scan_default.enabled = False
        self.mi_scan_dev.enabled = False
        self.mi_scan_prod.enabled = False

        findings = scan_project(self.project_root, mode=mode)
        report_path = write_html_report(
            findings,
            self.project_root,
            out_dir="reports",
        )
        self._save_last_report(str(report_path))

        risks = sum(1 for f in findings if f.kind == "RISK")
        todos = sum(1 for f in findings if f.kind == "TODO")

        self.last_risks = risks
        self.last_todos = todos

        # 🟢 Scan bitti
        self.mi_status.title = f"Status: {risks} risks · {todos} todos"
        self.mi_last_scan.title = f"Last Scan: {datetime.now().strftime('%H:%M')}"
        self.mi_open_report.enabled = True

        self._update_title_badge()
        self._refresh_mode_checks()

        # 🟢 Butonları geri aç
        self.mi_scan_default.enabled = True
        self.mi_scan_dev.enabled = True
        self.mi_scan_prod.enabled = True

        label = "PROD" if mode == SCAN_PROD else "DEV"

        rumps.notification(
            "Zinkx Dev Assistant",
            f"Scan completed · {label}",
            f"🚨 Risks: {risks}   📝 TODO: {todos}",
        )

        open_path(str(report_path))


    # --------------------------------------------------
    # Other actions
    # --------------------------------------------------
    def open_last_report(self, _):
        p = self._load_last_report()
        if not p or not os.path.exists(p):
            rumps.alert("No report yet", "Run a scan first.")
            return
        open_path(p)

    def open_general_settings(self, _):
        open_general_settings()
        self._update_title_badge()
        self._refresh_mode_checks()

    def open_ignore_settings(self, _):
        open_ignore_settings()

    def install_hook(self, _):
        if not self.project_root or not os.path.isdir(self.project_root):
            rumps.alert("No project selected", "Choose Project Folder first.")
            return

        try:
            hook = install_precommit_hook(self.project_root)
            rumps.notification(
                "Zinkx",
                "Pre-commit Hook Installed",
                str(hook),
            )
        except Exception as e:
            rumps.alert("Hook install failed", str(e))

    def quick_note(self, _):
        win = rumps.Window(
            title="Quick Note",
            message="Quick developer note (saved locally):",
            default_text="• ",
            ok="Save Note",
            cancel="Cancel",
            dimensions=(420, 160),
        )
        resp = win.run()
        if not resp.clicked:
            return

        note = resp.text.strip()
        if not note:
            return

        notes_file = os.path.join(self.state_dir, "notes.txt")
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(note + "\n")

        rumps.notification("Zinkx", "Saved", "Not kaydedildi ✅")


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------
if __name__ == "__main__":
    ZinkxDevAssistant().run()
