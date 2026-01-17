import sys
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem,
    QStackedWidget, QProgressBar, QCheckBox,
    QComboBox, QSlider, QFormLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView

import qtawesome as qta
from qt_material import apply_stylesheet

from ipc import send_command, read_status, read_command, clear_command
from config import load_config, save_config, APP_META
from PySide6.QtGui import QPalette


def apply_theme(app, theme: str):
    if theme == "light":
        apply_stylesheet(app, theme="light_blue.xml")
    else:
        apply_stylesheet(app, theme="dark_teal.xml")


UI = {
    "radius_sm": "10px",
    "radius_md": "14px",
    "radius_lg": "20px",
}

# ==================================================
# Main Window
# ==================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --------------------------------------------------
        # Config
        # --------------------------------------------------
        self.cfg = load_config()

        # --------------------------------------------------
        # Window
        # --------------------------------------------------
        self.setWindowTitle(
            f"{APP_META['name']} v{APP_META['version']}"
        )
        self.setMinimumSize(1050, 650)

        base_dir = os.path.dirname(__file__)
        self.reports_dir = os.path.join(base_dir, "..", "reports")

        icon_path = os.path.join(base_dir, "..", "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))


        # --------------------------------------------------
        # State
        # --------------------------------------------------
        self.project_path = None
        self._last_status_hash = None
        # UI tokens (instance scope)
        self.UI = UI

        # Toast system
        self._toast_queue = []
        self._toast_active = False
        self._scan_history = self.cfg.get("scan_history", [])
        self._top_risky_files = []

    
        # --------------------------------------------------
        # Root
        # --------------------------------------------------
        root = QWidget(self)
        root.setObjectName("appRoot")  # tema / stylesheet için hook
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)      # sidebar + content arası net çizgi


        # ==================================================
        # Sidebar
        # ==================================================
        self.sidebar = QWidget()
        sidebar = self.sidebar
        self.apply_sidebar_style()
        sidebar.setFixedWidth(240)

        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(20, 26, 20, 20)
        sb.setSpacing(10)

        # --------------------------------------------------
        # Brand / Header
        # --------------------------------------------------
        brand = QLabel("<h2 style='margin:0'>Zinkx</h2>")
        subtitle = QLabel("Dev Assistant")
        subtitle.setStyleSheet("color:#94a3b8;font-size:12px;")

        sb.addWidget(brand)
        sb.addWidget(subtitle)
        sb.addSpacing(28)

        # --------------------------------------------------
        # Navigation button factory
        # --------------------------------------------------
        def nav(text, icon):
            b = QPushButton(text)
            b._icon_name = icon
            self.update_nav_icon(b)
            b.setIconSize(QSize(18, 18))
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(48)
            return b


        # --------------------------------------------------
        # Nav buttons
        # --------------------------------------------------
        self.btn_dashboard = nav("Dashboard", "mdi.view-dashboard-outline")
        self.btn_scan = nav("Scan", "mdi.magnify")
        self.btn_reports = nav("Reports", "mdi.file-document-outline")
        self.btn_settings = nav("Settings", "mdi.cog-outline")

        self.navs = [
            self.btn_dashboard,
            self.btn_scan,
            self.btn_reports,
            self.btn_settings,
        ]

        self.btn_dashboard.setChecked(True)

        for b in self.navs:
            sb.addWidget(b)

        sb.addStretch()


        # --------------------------------------------------
        # Sidebar footer (App info + Icon)
        # --------------------------------------------------
        self.status_chip = QLabel("● Idle")
        self.status_chip.setStyleSheet("""
            QLabel {
                color:#22c55e;
                font-size:11px;
                padding:6px 10px;
                border-radius:999px;
                background:rgba(34,197,94,0.15);
            }
        """)
        sb.addWidget(self.status_chip)

        # --- Footer container
        footer_wrap = QWidget()
        footer_layout = QHBoxLayout(footer_wrap)
        footer_layout.setContentsMargins(0, 10, 0, 0)
        footer_layout.setSpacing(10)

        # --- App icon
        base_dir = os.path.dirname(__file__)
        icon_path = os.path.join(base_dir, "..", "assets", "icon.png")

        icon_label = QLabel()
        if os.path.exists(icon_path):
            icon_label.setPixmap(QIcon(icon_path).pixmap(28, 28))
        icon_label.setFixedSize(28, 28)

        # --- App info text
        footer_text = QLabel(
            f"""
            <div style='line-height:1.4'>
                <b>{APP_META['name']}</b><br>
                <span style='color:#94a3b8;font-size:11px'>
                    v{APP_META['version']} · Security Scanner
                </span>
            </div>
            """
        )


        footer_layout.addWidget(icon_label)
        footer_layout.addWidget(footer_text)
        footer_layout.addStretch()

        sb.addWidget(footer_wrap)


        root_layout.addWidget(sidebar)


        # ==================================================
        # Pages
        # ==================================================
        self.pages = QStackedWidget()
        root_layout.addWidget(self.pages)

        self.page_dashboard = QWidget()
        self.page_scan = QWidget()
        self.page_reports = QWidget()
        self.page_settings = QWidget()

        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_scan)
        self.pages.addWidget(self.page_reports)
        self.pages.addWidget(self.page_settings)

        self.build_dashboard()
        self.build_scan()
        self.build_reports()
        self.build_settings()

        for i, b in enumerate(self.navs):
            b.clicked.connect(lambda _, x=i: self.switch_page(x))

        # --------------------------------------------------
        # IPC Timers
        # --------------------------------------------------
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.poll_status)
        self.status_timer.start(500)

        self.cmd_timer = QTimer(self)
        self.cmd_timer.timeout.connect(self.poll_commands)
        self.cmd_timer.start(500)

        self.load_reports()

    def apply_sidebar_style(self):
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #020617;
                border-right: 1px solid #1f2937;
            }

            QLabel {
                color: #e5e7eb;
            }

            QPushButton {
                text-align: left;
                padding: 12px 14px;
                border-radius: 12px;
                border: none;
                color: #cbd5f5;
            }

            QPushButton:hover {
                background-color: rgba(56,189,248,0.12);
            }

            QPushButton:checked {
                background-color: rgba(56,189,248,0.22);
                color: white;
            }
        """)


    def _show_next_toast(self):
        if not self._toast_queue:
            self._toast_active = False
            return

        self._toast_active = True
        message, type = self._toast_queue.pop(0)

        colors = {
            "info":    "#1e293b",
            "success": "#064e3b",
            "warning": "#78350f",
            "error":   "#7f1d1d",
        }

        self._toast = Toast(
            message=message,
            bg=colors.get(type, "#1e293b")
        )

        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen().availableGeometry()

        margin = 20
        x = screen.right() - self._toast.width() - margin
        y = screen.bottom() - self._toast.height() - margin


        self._toast.move(x, y)
        self._toast.show()
        self._toast.raise_()

        QTimer.singleShot(3000, self._toast_finished)

    def show_toast(self, message: str, type: str = "info"):
        """
        Public toast API
        """
        self._toast_queue.append((message, type))

        if not self._toast_active:
            self._show_next_toast()

    def _toast_finished(self):
        self._toast_active = False
        self._show_next_toast()

    # ==================================================
    # Pages
    # ==================================================
    def build_dashboard(self):
        # ==================================================
        # Root layout (dashboard)
        # ==================================================
        page_layout = QVBoxLayout(self.page_dashboard)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea(self.page_dashboard)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        page_layout.addWidget(scroll)

        content = QWidget(scroll)
        scroll.setWidget(content)

        l = QVBoxLayout(content)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)


        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        l.addWidget(QLabel("<h1>Dashboard</h1>"))

        subtitle = QLabel("Overview of last scan & project status")
        subtitle.setStyleSheet("color:#9ca3af;")
        l.addWidget(subtitle)

        # --------------------------------------------------
        # Stat cards
        # --------------------------------------------------
        cards = QHBoxLayout()
        cards.setSpacing(16)

        def card(title, icon, subtitle):
            w = QWidget()
            pal = QApplication.palette()
            bg = pal.color(QPalette.Base).name()
            border = pal.color(QPalette.Mid).name()

            w.setStyleSheet("""
                QWidget {
                    background: rgba(15,23,42,0.75);
                    border-radius: 16px;
                    border: 1px solid rgba(148,163,184,0.12);
                }
            """)


            from PySide6.QtWidgets import QGraphicsDropShadowEffect

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(28)
            shadow.setOffset(0, 8)
            shadow.setColor(Qt.black)
            w.setGraphicsEffect(shadow)
            lay = QVBoxLayout(w)
            lay.setSpacing(4)

            top = QHBoxLayout()
            top.addWidget(QLabel(f"<b>{title}</b>"))
            top.addStretch()
            top.addWidget(QLabel(icon))
            lay.addLayout(top)

            value = QLabel("0")
            value.setStyleSheet("font-size:32px;font-weight:700;")
            lay.addWidget(value)

            hint = QLabel(subtitle)
            hint.setStyleSheet("color:#9ca3af;font-size:11px;")
            lay.addWidget(hint)

            return w, value


        card_risk, self.lbl_risk = card("Risks", "⚠️", "Potential security issues")
        card_todo, self.lbl_todo = card("TODOs", "📝", "Code comments & notes")


        cards.addWidget(card_risk)
        cards.addWidget(card_todo)
        cards.addStretch()

        l.addLayout(cards)

        # --------------------------------------------------
        # Health Score (Enhanced)
        # --------------------------------------------------
        health = QWidget()
        self.health_card = health  # 🔴 ÖNEMLİ: dışarıdan style değiştireceğiz

        pal = QApplication.palette()
        bg = pal.color(QPalette.Base).name()
        border = pal.color(QPalette.Mid).name()

        self.health_card.setStyleSheet("""
            QWidget {
                background: rgba(15,23,42,0.75);
                border-radius: 20px;
                padding: 18px;
                border: 1px solid rgba(148,163,184,0.12);
            }
        """)




        hl = QVBoxLayout(health)
        hl.setSpacing(6)

        hl.addWidget(QLabel("<b>Scan Health</b>"))

        # Büyük skor
        self.lbl_health = QLabel("—")
        self.lbl_health.setStyleSheet("""
            font-size:34px;
            font-weight:900;
            letter-spacing:-1px;
            color:#94a3b8;
        """)
        hl.addWidget(self.lbl_health)

        # Badge (HEALTHY / WARNING / CRITICAL)
        self.lbl_health_badge = QLabel("")
        self.lbl_health_badge.setStyleSheet("""
            QLabel{
                padding:6px 10px;
                border-radius:999px;
                font-size:11px;
                font-weight:800;
                letter-spacing:0.4px;
                background:rgba(148,163,184,0.15);
                color:#94a3b8;
                max-width:160px;
            }
        """)
        hl.addWidget(self.lbl_health_badge)

        # Açıklama metni
        self.lbl_health_hint = QLabel("")
        self.lbl_health_hint.setStyleSheet("color:#9ca3af;font-size:12px;")
        hl.addWidget(self.lbl_health_hint)

        l.addWidget(health)


        # --------------------------------------------------
        # Project info panel
        # --------------------------------------------------
        project_box = QWidget()
        project_box.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        pb = QVBoxLayout(project_box)
        pb.setSpacing(6)

        pb.addWidget(QLabel("<b>Last Project</b>"))

        self.lbl_project = QLabel("No project selected")
        self.lbl_project.setStyleSheet("color:#9ca3af;")
        pb.addWidget(self.lbl_project)

        l.addWidget(project_box)

        # --------------------------------------------------
        # Current Project Status
        # --------------------------------------------------
        status_box = QWidget()
        status_box.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        sl = QVBoxLayout(status_box)
        sl.setSpacing(6)

        sl.addWidget(QLabel("<b>Project Status</b>"))

        self.lbl_project_status = QLabel("No scan yet.")
        self.lbl_project_status.setStyleSheet(
            "color:#9ca3af; font-size:12px; line-height:1.5"
        )

        self.lbl_project_status.setText("No scan yet.")


        sl.addWidget(self.lbl_project_status)
        l.addWidget(status_box)

        # --------------------------------------------------
        # Last scan summary
        # --------------------------------------------------
        summary = QWidget()
        summary.setStyleSheet("""
            QWidget {
                background: rgba(15,23,42,0.6);
                border-radius: 14px;
                padding: 16px;
                border: 1px solid rgba(148,163,184,0.08);
            }
        """)
        sl = QVBoxLayout(summary)
        sl.setSpacing(6)

        sl.addWidget(QLabel("<b>Last Scan Summary</b>"))

        self.lbl_dash = QLabel("No scan performed yet.")
        pal = QApplication.palette()
        self.lbl_dash.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()};"
        )

        sl.addWidget(self.lbl_dash)

        l.addWidget(summary)

        # --------------------------------------------------
        # Last Scan Details
        # --------------------------------------------------
        details = QWidget()
        details.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        dl = QVBoxLayout(details)
        dl.setSpacing(6)

        dl.addWidget(QLabel("<b>Last Scan Details</b>"))

        self.lbl_scan_details = QLabel(
            "No scan data available."
        )
        self.lbl_scan_details.setStyleSheet(
            "color:#9ca3af; font-size:12px; line-height:1.5"
        )
        dl.addWidget(self.lbl_scan_details)

        l.addWidget(details)

        # --------------------------------------------------
        # Scan Performance
        # --------------------------------------------------
        perf = QWidget()
        perf.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.03);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        pl = QVBoxLayout(perf)
        pl.setSpacing(6)

        pl.addWidget(QLabel("<b>Scan Performance</b>"))

        self.lbl_perf = QLabel("No data.")
        self.lbl_perf.setStyleSheet(
            "color:#9ca3af;font-size:12px;"
        )

        pl.addWidget(self.lbl_perf)
        l.addWidget(perf)

        # --------------------------------------------------
        # Scan History (Last 5)
        # --------------------------------------------------
        history = QWidget()
        history.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        hl = QVBoxLayout(history)
        hl.setSpacing(6)

        hl.addWidget(QLabel("<b>Last 5 Scans</b>"))

        self.lbl_history = QLabel("No scan history.")
        pal = QApplication.palette()
        self.lbl_history.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()}; font-size:12px; line-height:1.6"
        )



        hl.addWidget(self.lbl_history)
        l.addWidget(history)
        # --------------------------------------------------
        # Top 5 Risky Files
        # --------------------------------------------------
        risky = QWidget()
        risky.setStyleSheet("""
            QWidget {
                background: rgba(239,68,68,0.08);
                border-radius: 12px;
                padding: 16px;
            }
        """)

        rl = QVBoxLayout(risky)
        rl.setSpacing(6)

        rl.addWidget(QLabel("<b>Top 5 Risky Files</b>"))

        self.list_risky = QListWidget()
        self.list_risky.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background: rgba(239,68,68,0.15);
            }
        """)

        self.list_risky.itemClicked.connect(self.copy_risky_path)

        rl.addWidget(self.list_risky)
        l.addWidget(risky)

        # --------------------------------------------------
        # Hint / help text
        # --------------------------------------------------
        hint = QLabel(
            "• Use the Scan tab to analyze your project\n"
            "• Dev mode shows INFO, Prod mode focuses on RISK\n"
            "• Reports are generated after each scan"
        )
        pal = QApplication.palette()
        hint.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()};"
        )


        l.addWidget(hint)

        # --------------------------------------------------
        # Load existing scan history on startup
        # --------------------------------------------------
        if self._scan_history:
            history_text = "\n".join(
                f"• {h['date']} | {h['mode']} | {h['risks']} risks"
                for h in self._scan_history
            )
            self.lbl_history.setText(history_text)

        l.addStretch()

        # --------------------------------------------------
        # Quick Actions
        # --------------------------------------------------
        qa = QHBoxLayout()

        btn_dev = QPushButton("Scan (Dev)")
        btn_prod = QPushButton("Scan (Prod)")
        btn_clean = QPushButton("Clean Project")

        btn_dev.clicked.connect(lambda: self.start_scan("dev"))
        btn_prod.clicked.connect(lambda: self.start_scan("prod"))
        btn_clean.clicked.connect(self.clean_project)

        btn_clean.setStyleSheet("""
            QPushButton {
                background: rgba(239,68,68,0.15);
                border: 1px solid rgba(239,68,68,0.35);
                color: #fecaca;
            }
            QPushButton:hover {
                background: rgba(239,68,68,0.25);
                border-color: #ef4444;
                color: white;
            }
        """)

        qa.addWidget(btn_dev)
        qa.addWidget(btn_prod)
        qa.addWidget(btn_clean)
        qa.addStretch()

        l.addLayout(qa)


    def copy_risky_path(self, item):
        path = item.text()
        QApplication.clipboard().setText(path)
        self.show_toast("File path copied", type="info")

    def build_scan(self):
        l = QVBoxLayout(self.page_scan)
        l.setContentsMargins(32, 32, 32, 32)
        l.setSpacing(20)

        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        l.addWidget(QLabel("<h1>Scan Project</h1>"))

        subtitle = QLabel("Select a project folder and start scanning")
        pal = QApplication.palette()
        subtitle.setStyleSheet(f"color:{pal.color(QPalette.Text).name()};")
        l.addWidget(subtitle)

        # --------------------------------------------------
        # Action buttons (cards style)
        # --------------------------------------------------
        actions = QHBoxLayout()
        actions.setSpacing(16)

        def scan_card(title, desc, icon_path, bg, fg):
            w = QWidget()
            w.setCursor(Qt.PointingHandCursor)
            w.setStyleSheet("""
                QWidget {
                    background: rgba(15,23,42,0.75);
                    border-radius: 18px;
                    padding: 18px;
                    border: 1px solid rgba(148,163,184,0.12);
                }
                QWidget:hover {
                    border-color: #38bdf8;
                    background: rgba(56,189,248,0.08);
                }
            """)


            lay = QVBoxLayout(w)
            lay.setSpacing(8)

            icon = QLabel()
            icon.setPixmap(QIcon(icon_path).pixmap(28, 28))
            lay.addWidget(icon)

            lay.addWidget(QLabel(f"<b>{title}</b>"))

            d = QLabel(desc)
            pal = QApplication.palette()
            d.setStyleSheet(
                f"color:{pal.color(QPalette.Text).name()}; font-size:12px;"
            )


            lay.addWidget(d)

            return w

        base_dir = os.path.dirname(__file__)
        icon_dir = os.path.join(base_dir, "..", "assets", "icons")

        self.card_choose = scan_card(
            "Choose Project",
            "Select root folder",
            os.path.join(icon_dir, "folder.svg"),
            "rgba(255,255,255,0.05)",
            "#fff"
        )

        self.card_dev = scan_card(
            "Scan (Dev)",
            "Development scan",
            os.path.join(icon_dir, "play-dev.svg"),
            "rgba(37,99,235,0.25)",
            "#fff"
        )

        self.card_prod = scan_card(
            "Scan (Prod)",
            "Strict production scan",
            os.path.join(icon_dir, "alert-prod.svg"),
            "rgba(185,28,28,0.25)",
            "#fff"
        )

        actions.addWidget(self.card_choose)
        actions.addWidget(self.card_dev)
        actions.addWidget(self.card_prod)
        actions.addStretch()

        l.addLayout(actions)

        # --------------------------------------------------
        # Status & Progress
        # --------------------------------------------------
        self.scan_status = QLabel("No project selected.")
        self.scan_status.setStyleSheet("color:#9ca3af;")
        l.addWidget(self.scan_status)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
        QProgressBar {
            background: rgba(255,255,255,0.08);
            border-radius: 3px;
        }
        QProgressBar::chunk {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #3b82f6,
                stop:1 #22d3ee
            );
            border-radius: 3px;
        }
        """)
        self.progress.hide()
        l.addWidget(self.progress)

        self.btn_cancel = QPushButton("Cancel Scan")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background:#7f1d1d;
                color:white;
                padding:8px 14px;
                border-radius:8px;
            }
            QPushButton:disabled {
                background:#374151;
                color:#9ca3af;
            }
        """)

        self.btn_cancel.clicked.connect(self.cancel_scan)
        l.addWidget(self.btn_cancel)


        # --------------------------------------------------
        # Click bindings
        # --------------------------------------------------
        self.card_choose.mousePressEvent = lambda e: self.choose_project()
        self.card_dev.mousePressEvent = lambda e: self.start_scan("dev")
        self.card_prod.mousePressEvent = lambda e: self.start_scan("prod")

        l.addStretch()


    def build_reports(self):
        wrapper = QHBoxLayout(self.page_reports)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(0)

        # ==================================================
        # LEFT – Report List (Enhanced)
        # ==================================================
        left = QWidget()
        left.setFixedWidth(360)
        pal = QApplication.palette()
        left.setStyleSheet(f"""
            QWidget {{
                background: {pal.color(QPalette.Window).name()};
                border-right: 1px solid {pal.color(QPalette.Mid).name()};
            }}
        """)


        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 20, 16, 16)
        ll.setSpacing(12)

        title = QLabel("<h2>Reports</h2>")
        subtitle = QLabel("Latest scan results")
        pal = QApplication.palette()
        subtitle.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()}; font-size:12px;"
        )



        ll.addWidget(title)
        ll.addWidget(subtitle)

        self.reports_list = QListWidget()
        self.reports_list.setSpacing(8)
        pal = QApplication.palette()
        bg = pal.color(QPalette.Base).name()
        border = pal.color(QPalette.Mid).name()

        self.reports_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
            }}
            QListWidget::item {{
                background: {bg};
                border-radius: {self.UI["radius_md"]};
                padding: 12px;
                border: 1px solid {border};
            }}
            QListWidget::item:selected {{
                background: {pal.color(QPalette.Highlight).name()};
                color: white;
            }}
        """)
        self.reports_list.itemClicked.connect(self.open_report)

        ll.addWidget(self.reports_list)
        wrapper.addWidget(left)

        # ==================================================
        # RIGHT – Report Viewer
        # ==================================================
        self.report_view = QWebEngineView()
        pal = QApplication.palette()
        self.report_view.setStyleSheet(
            f"background:{pal.color(QPalette.Base).name()};"
        )


        wrapper.addWidget(self.report_view)

    def build_settings(self):
        self.page_settings.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        # --- page_settings sadece scroll taşır
        page_layout = QVBoxLayout(self.page_settings)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        page_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(28)

        # ---------------- Header ----------------
        content_layout.addWidget(QLabel("<h1>Settings</h1>"))

        subtitle = QLabel("Customize scanning behavior & application preferences")
        pal = QApplication.palette()
        subtitle.setStyleSheet(f"color:{pal.color(QPalette.Text).name()};")
        content_layout.addWidget(subtitle)

        # ---------------- Card helper ----------------
        def card(title):
            w = QWidget()

            w.setStyleSheet("""
                QWidget {
                    background: rgba(15,23,42,0.75);
                    border-radius: 16px;
                    border: 1px solid rgba(148,163,184,0.12);
                }
            """)

            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(24)
            shadow.setOffset(0, 8)
            shadow.setColor(Qt.black)
            w.setGraphicsEffect(shadow)

            v = QVBoxLayout(w)
            v.setContentsMargins(20, 20, 20, 20)
            v.setSpacing(14)

            lbl = QLabel(title)
            lbl.setStyleSheet("""
                font-weight:800;
                font-size:14px;
                color:#e5e7eb;
            """)
            v.addWidget(lbl)

            return w, v



        # ---------------- Appearance ----------------
        appearance, al = card("Appearance")

        row = QHBoxLayout()
        row.addWidget(QLabel("Theme"))
        row.addStretch()

        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["dark", "light", "system"])
        self.cmb_theme.setCurrentText(self.cfg.get("theme", "dark"))
        self.cmb_theme.setMinimumWidth(180)
        row.addWidget(self.cmb_theme)

        al.addLayout(row)

        desc = QLabel("Change application theme (restart not required)")
        desc.setStyleSheet("""
            color: palette(mid);
            font-size:12px;
        """)
        al.addWidget(desc)

        content_layout.addWidget(appearance)

        # ---------------- Notifications ----------------
        notify, nl = card("Notifications")

        self.chk_notify = QCheckBox("Enable notifications")
        self.chk_notify.setChecked(self.cfg.get("enable_notifications", True))

        nl.addWidget(self.chk_notify)

        self.chk_notify.stateChanged.connect(self.save_settings)

        desc = QLabel("Show toast notifications when scan completes or fails.")
        desc.setStyleSheet("color:#94a3b8;font-size:12px;")
        nl.addWidget(desc)

        content_layout.addWidget(notify)


        # ---------------- Scan Defaults ----------------
        scan, sl = card("Scan Defaults")

        row = QHBoxLayout()
        row.addWidget(QLabel("Default Scan Mode"))
        row.addStretch()

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["dev", "prod"])
        self.cmb_mode.setCurrentText(self.cfg.get("default_mode", "dev"))
        self.cmb_mode.setMinimumWidth(180)
        row.addWidget(self.cmb_mode)

        sl.addLayout(row)

        sl.addWidget(QLabel("Risk Threshold"))

        self.slider_risk = QSlider(Qt.Horizontal)
        self.slider_risk.setRange(0, 10)
        self.slider_risk.setValue(self.cfg.get("risk_threshold", 0))
        self.slider_risk.setFixedHeight(22)
        sl.addWidget(self.slider_risk)

        risk_desc = QLabel("Minimum risk count to highlight warnings")
        pal = QApplication.palette()
        risk_desc.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()}; font-size:12px;"
        )


        sl.addWidget(risk_desc)

        content_layout.addWidget(scan)

        # ---------------- Ignore Rules ----------------
        ignore, il = card("Ignore Rules")

        self.chk_env = QCheckBox("Ignore .env files")
        self.chk_node = QCheckBox("Ignore node_modules directory")

        self.chk_env.setChecked(self.cfg.get("ignore_env", True))
        self.chk_node.setChecked(self.cfg.get("ignore_node_modules", True))

        il.addWidget(self.chk_env)
        il.addWidget(self.chk_node)

        ignore_desc = QLabel("Ignored files and folders will be skipped during scan.")
        pal = QApplication.palette()
        ignore_desc.setStyleSheet(
            f"color:{pal.color(QPalette.Text).name()}; font-size:12px;"
        )


        il.addWidget(ignore_desc)

        content_layout.addWidget(ignore)

        # ---------------- Application Info ----------------
        info, inf = card("Application")
        inf.addWidget(QLabel(
            f"""
            <span style='color:#94a3b8;font-size:12px'>
                {APP_META['name']} v{APP_META['version']}<br>
                Local static code & security analyzer
            </span>
            """
        ))


        content_layout.addWidget(info)
        content_layout.addStretch()

        # ---------------- Bindings ----------------
        self.cmb_theme.currentTextChanged.connect(self.save_settings)
        self.cmb_mode.currentTextChanged.connect(self.save_settings)
        self.slider_risk.valueChanged.connect(self.save_settings)
        self.chk_env.stateChanged.connect(self.save_settings)
        self.chk_node.stateChanged.connect(self.save_settings)

    def refresh_theme(self):
        pal = QApplication.palette()

        card_bg = pal.color(QPalette.Base).name()
        border = pal.color(QPalette.Mid).name()
        text = pal.color(QPalette.Text).name()

        self.apply_sidebar_style()

        for b in self.navs:
            self.update_nav_icon(b)

        # ⛔ Scan yapıldıysa health card'a DOKUNMA
        if hasattr(self, "health_card") and not self._last_status_hash:
            self.health_card.setStyleSheet(f"""
                QWidget {{
                    background: {card_bg};
                    border-radius: {self.UI["radius_lg"]};
                    padding: 18px;
                    border: 1px solid {border};
                }}
            """)

        for lbl in [
            getattr(self, "lbl_dash", None),
            getattr(self, "lbl_history", None),
            getattr(self, "lbl_perf", None),
            getattr(self, "lbl_project", None),
            getattr(self, "lbl_scan_details", None),
        ]:
            if lbl:
                lbl.setStyleSheet(f"color:{text};")

        if hasattr(self, "report_view"):
            self.report_view.setStyleSheet(f"background:{card_bg};")

        if hasattr(self, "reports_list"):
            self.reports_list.update()




    # ==================================================
    # Actions
    # ==================================================
    def switch_page(self, index):
        for b in self.navs:
            b.setChecked(False)

        self.navs[index].setChecked(True)
        self.pages.setCurrentIndex(index)

        # 🔥 ikon renklerini güncelle
        for b in self.navs:
            self.update_nav_icon(b)


    def update_nav_icon(self, btn):
        if btn.isChecked():
            color = "#38bdf8"   # aktif → accent
        else:
            color = "#94a3b8"   # pasif → muted

        btn.setIcon(qta.icon(btn._icon_name, color=color))


    def choose_project(self):
        p = QFileDialog.getExistingDirectory(self, "Choose Project")
        if p:
            self.project_path = p
            self.scan_status.setText(p)
        if hasattr(self, "lbl_project"):
            self.lbl_project.setText(p)


    def start_scan(self, mode):
        if not self.project_path:
            self.scan_status.setText("Choose a project first.")
            return

        self.progress.show()
        self.progress.setValue(10)
        self.scan_status.setText("Scanning…")
        self.show_toast("Scan started…", type="info")
        self.btn_cancel.setEnabled(True)

        # Sidebar status → Scanning
        self.status_chip.setText("● Scanning")
        self.status_chip.setStyleSheet("""
            QLabel {
                color:#facc15;
                background:rgba(250,204,21,0.15);
            }
        """)

        send_command({
            "action": "scan",
            "mode": mode,
            "project": self.project_path,
        })

    def cancel_scan(self):
        send_command({"action": "cancel_scan"})

        self.progress.setValue(0)
        self.progress.hide()
        self.scan_status.setText("Scan cancelled.")
        self.btn_cancel.setEnabled(False)

        self.status_chip.setText("● Cancelled")
        self.status_chip.setStyleSheet("""
            QLabel {
                color:#f97316;
                background:rgba(249,115,22,0.15);
            }
        """)

        self.show_toast("Scan cancelled", type="warning")

    def clean_project(self):
        import subprocess

        base_dir = os.path.dirname(__file__)
        script_path = os.path.join(base_dir, "..", "tools", "clean_project.py")

        if not os.path.exists(script_path):
            self.show_toast("Clean script not found", type="error")
            return

        try:
            subprocess.run(
                ["python3", script_path],
                cwd=os.path.join(base_dir, ".."),
                check=True
            )
            self.show_toast("Project cleaned successfully", type="success")
        except Exception as e:
            self.show_toast(f"Clean failed: {e}", type="error")




    def save_settings(self):
        old_theme = self.cfg.get("theme", "dark")
        new_theme = self.cmb_theme.currentText()

        self.cfg.update({
            "default_mode": self.cmb_mode.currentText(),
            "risk_threshold": self.slider_risk.value(),
            "ignore_env": self.chk_env.isChecked(),
            "ignore_node_modules": self.chk_node.isChecked(),
            "theme": new_theme,
            "enable_notifications": self.chk_notify.isChecked(),
        })

        save_config(self.cfg)

        if new_theme != old_theme:
            self.theme = new_theme
            self.UI = UI

        apply_theme(QApplication.instance(), new_theme)
        QTimer.singleShot(0, self.refresh_theme)




    # ==================================================
    # Reports
    # ==================================================
    def load_reports(self):
        self.reports_list.clear()

        if not os.path.isdir(self.reports_dir):
            return

        base_dir = os.path.dirname(__file__)
        icon_dir = os.path.join(base_dir, "..", "assets", "icons")

        for f in sorted(os.listdir(self.reports_dir), reverse=True):
            if not f.endswith(".html"):
                continue

            # filename örnek: 2026-01-15_myproject_prod.html
            parts = f.replace(".html", "").split("_")

            date = parts[0] if len(parts) > 0 else "Unknown date"
            project = parts[1] if len(parts) > 1 else "Unknown project"
            mode = parts[2].upper() if len(parts) > 2 else "SCAN"

            item = QListWidgetItem()
            item.setSizeHint(QSize(320, 74))
            item.setData(Qt.UserRole, f)

            widget = QWidget()
            v = QVBoxLayout(widget)
            v.setContentsMargins(8, 6, 8, 6)
            v.setSpacing(4)

            # ---- Title row
            t = QHBoxLayout()
            icon = QLabel()
            icon.setPixmap(QIcon(os.path.join(icon_dir, "report.svg")).pixmap(18, 18))
            t.addWidget(icon)

            t.addWidget(QLabel(f"<b>{project}</b>"))
            t.addStretch()
            t.addWidget(QLabel(f"<span style='color:#60a5fa'>{mode}</span>"))
            v.addLayout(t)

            # ---- Meta row
            meta = QHBoxLayout()

            clock = QLabel()
            clock.setPixmap(QIcon(os.path.join(icon_dir, "clock.svg")).pixmap(14, 14))
            meta.addWidget(clock)
            meta.addWidget(QLabel(f"<span style='color:#94a3b8;font-size:11px'>{date}</span>"))

            meta.addSpacing(10)

            folder = QLabel()
            folder.setPixmap(QIcon(os.path.join(icon_dir, "folder.svg")).pixmap(14, 14))
            meta.addWidget(folder)
            meta.addWidget(QLabel("<span style='color:#94a3b8;font-size:11px'>Project root</span>"))

            meta.addStretch()
            v.addLayout(meta)

            self.reports_list.addItem(item)
            self.reports_list.setItemWidget(item, widget)


    def open_report(self, item):
        filename = item.data(Qt.UserRole)
        path = os.path.join(self.reports_dir, filename)
        self.report_view.setUrl(QUrl.fromLocalFile(path))


    # ==================================================
    # IPC
    # ==================================================
    def poll_status(self):
        st = read_status()
        if not st:
            return
        # ❌ Scan error
        if st.get("type") == "error" or st.get("error"):
            self.progress.hide()
            self.progress.setValue(0)
            self.scan_status.setText("Scan failed.")
            self.btn_cancel.setEnabled(False)

            self.status_chip.setText("● Error")
            self.status_chip.setStyleSheet("""
                QLabel {
                    color:#ef4444;
                    background:rgba(239,68,68,0.15);
                }
            """)

            self.show_toast(
                st.get("message", "Scan failed"),
                type="error"
            )
            return


        # Progress update
        if st.get("type") == "progress":
            self.progress.show()
            self.progress.setValue(st.get("percent", 0))
            return

        key = f"{st.get('finished_at')}|{st.get('last_risks')}|{st.get('last_todos')}|{st.get('mode')}"
        if key == self._last_status_hash:
            return

        self._last_status_hash = key
        self.progress.setValue(100)

        # ===============================
        # 📜 AŞAMA 2.3 — SAVE SCAN HISTORY
        # ===============================
        self._scan_history.insert(0, {
            "mode": st["mode"].upper(),
            "risks": st["last_risks"],
            "date": st.get("finished_at", "")
        })

        # sadece son 5 scan kalsın
        self._scan_history = self._scan_history[:5]
        self.cfg["scan_history"] = self._scan_history
        save_config(self.cfg)

        history_text = "\n".join(
            f"• {h['date']} | {h['mode']} | {h['risks']} risks"
            for h in self._scan_history
        )

        # Dashboard label güncelle
        if hasattr(self, "lbl_history"):
            self.lbl_history.setText(history_text)

        # ✅ Scan completed toast
        self.show_toast(
            f"Scan completed ({st['mode'].upper()})",
            type="success"
        )

        # ⚠️ Risk varsa ekstra uyarı
        if st.get("last_risks", 0) > 0:
            self.show_toast(
                f"{st['last_risks']} risks found",
                type="warning"
            )

        self.lbl_risk.setText(str(st["last_risks"]))
        self.lbl_todo.setText(str(st["last_todos"]))
        # ---- Top risky files (if provided)
        files = st.get("top_risky_files", [])

        self._top_risky_files = files[:5]

        if hasattr(self, "list_risky"):
            self.list_risky.clear()

            if not self._top_risky_files:
                self.list_risky.addItem("✔ No risky files detected")
            else:
                for f in self._top_risky_files:
                    self.list_risky.addItem(f)


        # ---- Health score (Enhanced UI)
        score = max(0, 100 - (st["last_risks"] * 15) - (st["last_todos"] * 5))
        self.lbl_health.setText(f"{score} / 100")

        if score >= 80:
            tone = {
                "color": "#22c55e",
                "bg": "rgba(34,197,94,0.18)",
                "border": "rgba(34,197,94,0.35)",
                "badge": "HEALTHY",
                "hint": "Nice! Your project looks clean."
            }
        elif score >= 50:
            tone = {
                "color": "#facc15",
                "bg": "rgba(250,204,21,0.18)",
                "border": "rgba(250,204,21,0.35)",
                "badge": "NEEDS REVIEW",
                "hint": "Some issues found. Review risks & TODOs."
            }
        else:
            tone = {
                "color": "#ef4444",
                "bg": "rgba(239,68,68,0.18)",
                "border": "rgba(239,68,68,0.35)",
                "badge": "CRITICAL",
                "hint": "High risk detected. Fix issues before release."
            }


        # Badge
        self.lbl_health_badge.setText(tone["badge"])
        self.lbl_health_badge.setStyleSheet(f"""
            QLabel{{
                padding:6px 10px;
                border-radius:999px;
                font-size:11px;
                font-weight:800;
                letter-spacing:0.4px;
                background:{tone["bg"]};
                border:1px solid {tone["border"]};
                color:{tone["color"]};
                max-width:160px;
            }}
        """)

        # Hint
        self.lbl_health_hint.setText(tone["hint"])

        # Kart arkaplanı (premium dokunuş)
        self.health_card.setStyleSheet(f"""
            QWidget {{
                border-radius: 20px;
                padding: 18px;
                border: 1px solid {tone["border"]};
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {tone["bg"]},
                    stop:1 rgba(255,255,255,0.03)
                );
            }}
        """)



        self.lbl_dash.setText(
            f"✔ Last scan ({st['mode'].upper()}) completed"
        )

        # ---- Dashboard: last scan details
        if hasattr(self, "lbl_project_status"):
            self.lbl_project_status.setText(
                f"Path: {self.project_path}\n"
                f"Last scan: {st.get('finished_at','-')}\n"
                f"Mode: {st.get('mode','').upper()}\n"
                f"Status: {'⚠ Issues found' if st['last_risks'] > 0 else '✔ Clean'}"
            )

        mode = st.get("mode", "-").upper()
        files = st.get("files_scanned", "?")
        duration = st.get("duration", "?")
        date = st.get("finished_at", "")

        details_text = (
            f"Mode: {mode}\n"
            f"Files scanned: {files}\n"
            f"Duration: {duration}s\n"
            f"Date: {date}"
        )

        # ---- Scan performance
        files = int(st.get("files_scanned", 0))
        duration = float(st.get("duration", 0.0))

        if duration > 0:
            speed = int(files / duration)
        else:
            speed = 0

        if hasattr(self, "lbl_perf"):
            self.lbl_perf.setText(
                f"Files scanned: {files}\n"
                f"Duration: {duration}s\n"
                f"Speed: ~{speed} files/sec"
            )

        if hasattr(self, "lbl_scan_details"):
            self.lbl_scan_details.setText(details_text)


        self.scan_status.setText("Scan completed.")
        if hasattr(self, "btn_cancel"):
            self.btn_cancel.setEnabled(False)

        # Sidebar status → Ready
        self.status_chip.setText("● Ready")
        self.status_chip.setStyleSheet("""
            QLabel {
                color:#22c55e;
                background:rgba(34,197,94,0.15);
            }
        """)

        QTimer.singleShot(1500, lambda: self.scan_status.setText("Ready"))
        QTimer.singleShot(800, self.progress.hide)
        self.load_reports()
 

    def poll_commands(self):
        cmd = read_command()
        if not cmd:
            return

        if cmd.get("action") == "focus":
            self.raise_()
            self.activateWindow()

        clear_command()


# ==================================================
# Toast Notification
# ==================================================
class Toast(QWidget):
    def __init__(self, message: str, bg: str):
        super().__init__(None)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                color: #e5e7eb;
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # ---------------- Icon by toast type (bg color)
        icon_map = {
            "#064e3b": "✔",  # success
            "#78350f": "⚠",  # warning
            "#7f1d1d": "✖",  # error
            "#1e293b": "ℹ",  # info
        }

        icon = QLabel(icon_map.get(bg, "ℹ"))
        icon.setStyleSheet("font-size:14px;")

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("font-size:12px;")

        layout.addWidget(icon)
        layout.addWidget(label)

        self.adjustSize()
        QTimer.singleShot(3000, self.close)



# ==================================================
# Entrypoint
# ==================================================
def run_main_window():
    app = QApplication(sys.argv)
    cfg = load_config()
    apply_theme(app, cfg.get("theme", "dark"))

    app.setStyleSheet("""
    QComboBox, QSlider, QCheckBox {
        background-color: rgba(15,23,42,0.6);
        border: 1px solid rgba(148,163,184,0.15);
        border-radius: 8px;
        padding: 6px;
    }
    QWidget {
        background-color: #0b1220;
        color: #e5e7eb;
        font-family: Inter, system-ui;
        font-size: 13px;
    }

    QLabel {
        color: #e5e7eb;
    }

    QLabel[muted="true"] {
        color: #9ca3af;
    }

    QPushButton {
        background-color: rgba(15,23,42,0.8);
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 10px 14px;
    }

    QPushButton:hover {
        background-color: rgba(56,189,248,0.12);
        border-color: #38bdf8;
    }


    QPushButton:hover {
        background-color: rgba(56,189,248,0.12);
        border-color: #38bdf8;
    }

    QPushButton:checked {
        background-color: rgba(56,189,248,0.22);
        border-color: #38bdf8;
        color: white;
    }

    QScrollArea {
        border: none;
    }

    QProgressBar {
        background: #020617;
        border-radius: 4px;
        height: 6px;
    }

    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #38bdf8,
            stop:1 #22d3ee
        );
        border-radius: 4px;
    }
    """)


    win = MainWindow()
    win.show()

    sys.exit(app.exec())




if __name__ == "__main__":
    run_main_window()

