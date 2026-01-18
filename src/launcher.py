# launcher.py
from __future__ import annotations

import multiprocessing as mp
import os
import sys
import time

# QtWebEngine GPU disable (macOS bazı sistemlerde siyah ekran fix)
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-software-rasterizer"
)


# --------------------------------------------------
# Qt Window Process
# --------------------------------------------------
def run_window(exit_event) -> None:
    """
    Child process: runs Qt main window.
    Window kapanınca sadece exit_event set edilir.
    """
    from main_window import run_main_window

    try:
        run_main_window()
    finally:
        # 🔴 EN ÖNEMLİ NOKTA:
        # Qt kapanınca SADECE sinyal veriyoruz
        try:
            exit_event.set()
        except Exception:
            pass


# --------------------------------------------------
# Menu Bar (OWNER process)
# --------------------------------------------------
def run_menubar(exit_event, window_process: mp.Process) -> None:
    import rumps
    from app import ZinkxDevAssistant

    app = ZinkxDevAssistant()
    shutting_down = False

    def shutdown() -> None:
        """
        Tek ve güvenli kapanış noktası
        """
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True

        try:
            exit_event.set()
        except Exception:
            pass

        # ❗ terminate / kill YOK
        # Qt zaten kendi kapanmış oluyor veya kapanıyor

        try:
            rumps.quit_application()
        except Exception:
            pass

    def watchdog(_):
        """
        Qt pencere kapandı mı?
        """
        if exit_event.is_set():
            shutdown()

    # Qt state poll (hafif, güvenli)
    rumps.Timer(watchdog, 0.5).start()

    try:
        app.run()
    finally:
        shutdown()


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------
def main() -> None:
    # macOS + PySide6 için en stabil
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    exit_event = mp.Event()

    window_process = mp.Process(
        target=run_window,
        args=(exit_event,),
        name="ZinkxDevAssistantWindow",
        daemon=False,  # ❗ daemon OLMAMALI
    )

    window_process.start()

    run_menubar(exit_event, window_process)

    # 🔚 Buraya gelindiyse her şey kapanmıştır
    window_process.join(timeout=3)


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] != "--ui":
        from cli import run_cli
        run_cli()
    else:
        run_menubar()
