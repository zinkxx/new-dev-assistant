import rumps
from config import load_config, save_config


APP_NAME = "Zinkx Dev Assistant"


# ==================================================
# General Settings (Quick / Menubar)
# ==================================================
def open_general_settings():
    cfg = load_config()

    message = (
        "Quick scan preferences (menubar)\n\n"
        "Line 1 → Default scan mode:\n"
        "   • dev  = development scan\n"
        "   • prod = strict production scan\n\n"
        "Line 2 → Risk threshold:\n"
        "   • 0 = any risk triggers warning\n"
        "   • Higher = more tolerant\n"
    )

    default_text = (
        f"{cfg.get('default_mode', 'dev')}\n"
        f"{cfg.get('risk_threshold', 0)}"
    )

    win = rumps.Window(
        title="General Settings",
        message=message,
        default_text=default_text,
        ok="Save",
        cancel="Cancel",
        dimensions=(460, 220),
    )

    resp = win.run()
    if not resp.clicked:
        return

    try:
        lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
        if len(lines) < 2:
            raise ValueError("Please provide both scan mode and risk threshold.")

        mode = lines[0].lower()
        threshold = int(lines[1])

        if mode not in ("dev", "prod"):
            raise ValueError("Scan mode must be 'dev' or 'prod'.")

        if threshold < 0:
            raise ValueError("Risk threshold must be 0 or higher.")

        cfg["default_mode"] = mode
        cfg["risk_threshold"] = threshold
        save_config(cfg)

        rumps.notification(
            APP_NAME,
            "Settings Saved",
            f"Default mode: {mode.upper()}\nRisk threshold: {threshold}"
        )

    except Exception as e:
        rumps.alert(
            "Invalid Settings",
            str(e)
        )


# ==================================================
# Ignore Rules (Inline markers)
# ==================================================
def open_ignore_settings():
    cfg = load_config()

    markers = cfg.get("ignore_inline_markers", [])
    default_text = "\n".join(markers)

    message = (
        "Inline ignore markers\n\n"
        "• One marker per line\n"
        "• Used to suppress findings in code\n\n"
        "Example:\n"
        "  zinkx-ignore\n"
        "  nosec\n"
    )

    win = rumps.Window(
        title="Ignore Rules",
        message=message,
        default_text=default_text,
        ok="Save",
        cancel="Cancel",
        dimensions=(460, 300),
    )

    resp = win.run()
    if not resp.clicked:
        return

    markers = [
        l.strip()
        for l in resp.text.splitlines()
        if l.strip()
    ]

    cfg["ignore_inline_markers"] = markers
    save_config(cfg)

    rumps.notification(
        APP_NAME,
        "Ignore Rules Updated",
        f"{len(markers)} marker(s) active"
    )


# ==================================================
# Settings Root (Info only)
# ==================================================
def open_settings_root():
    rumps.alert(
        "Settings",
        "Choose a category from the menu:\n\n"
        "• General Settings\n"
        "• Ignore Rules\n\n"
        "Advanced settings are available\n"
        "inside the main application."
    )
