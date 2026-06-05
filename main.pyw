import sys

from recap_reloaded.gui.application import Application

if __name__ == "__main__":
    app = Application()
    if not app.should_run:
        sys.exit(app.startup_exit_code)

    sys.exit(app.exec())
