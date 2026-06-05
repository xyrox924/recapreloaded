from PySide6.QtCore import QSharedMemory, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from recap_reloaded.config import ICON_PATH
from recap_reloaded.gui.mainwindow import MainWindow


class Application(QApplication):
    def __init__(self):
        super().__init__()
        self.should_run = True
        self.startup_exit_code = 0
        self._memory = QSharedMemory("recap_reloaded_singleton_key")
        self._setup()

    def _setup(self):
        if self._memory.attach():
            print("another instance is already running")
            self.should_run = False
            self.startup_exit_code = 0
            return

        if not self._memory.create(1):
            print("critical error can't start application")
            self.should_run = False
            self.startup_exit_code = 1
            return

        self.setQuitOnLastWindowClosed(False)
        self.aboutToQuit.connect(self._on_about_to_quit)

        self.win = MainWindow()

        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("recap.rebooted.1")
        except Exception:
            pass

        icon = QIcon(str(ICON_PATH))
        self.setWindowIcon(icon)
        self.win.setWindowIcon(icon)

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(icon)
        self.tray.setVisible(True)
        self.tray.activated.connect(self._tray_on_clicked)

        self.menu = QMenu()
        self.quit_action = QAction("quit")
        self.quit_action.triggered.connect(self._on_quit)
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)

    def _on_about_to_quit(self):
        if hasattr(self, "win"):
            self.win.cleanup()

    def _on_quit(self):
        self.quit()

    def _tray_on_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            QTimer.singleShot(0, self.win._refresh_game_banner)
            QTimer.singleShot(10, lambda: self.win.resizeEvent(None))
            self.win.show()
            self.win.raise_()
            self.win.activateWindow()
