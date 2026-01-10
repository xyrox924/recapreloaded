from PySide6.QtCore import Qt, QSortFilterProxyModel, QSize, Signal, QObject
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTreeView, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy, QSystemTrayIcon, QMenu

from gui.addgamedialog import AddGameDialog

from config import *

# container, layout, then widgets, then add widgets and layouts to the layout of the container
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("recap rebooted")
        self.resize(1000, 600)

        self.splitter = QSplitter(Qt.Horizontal) # type: ignore
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #000000;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)

        # left side
        self.tree_container = QWidget()
        self.tree_container.setStyleSheet("background-color: #191919;")
        self.tree_container.setMinimumWidth(200)
        self.tree_container.setMaximumWidth(310)

        self.tree_layout = QVBoxLayout(self.tree_container)
        self.tree_layout.setContentsMargins(0, 0, 0, 0)
        self.tree_layout.setSpacing(0)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("search games...")
        self.search_bar.setFrame(False)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #4C5C56;
                font-family: 'Raleway';
                font-size: 10pt;
                background-color: #2C2D2C;
                color: white;
                /*border: 1px solid #4C5C56;*/
                margin: 4px 2px;
                padding: 4px 6px;
                selection-background-color: #658076;
            }
            /*QLineEdit:focus {
                border: 1px solid #658076;
            }*/
        """)

        self.tree = QTreeView()
        self.tree.setUniformRowHeights(True)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setStyleSheet("""
            QTreeView {
                font-family: 'Raleway';
                font-size: 10pt;
                background-color: #191919;
                color: #E4E8E7;
                outline: 0;
                border: 0;
                /*margin: 0 8px;*/
            }

            QTreeView::item {
                height: 24px;
                margin-top: 1px;
                margin-bottom: 1px;
                border: none;
            }

            QTreeView::branch:closed:has-children {
                image: url(:/icons/arrow_right_white.svg);
            }

            QTreeView::branch:open:has-children {
                image: url(:/icons/arrow_down_white.svg);
            }

            QTreeView::item:selected {
                background-color: #658076;
                outline: 0;
                border: none;
                color: white;
            }
                                
            QTreeView::item:hover {
                background-color: #4C5C56;
            }
                                
            /*QTreeView::item:selected:hover {
                background-color: #859A92;
            }*/
                                
            QScrollBar:vertical {
                background: #191919;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #4C5C56;
                min-height: 30px;
                border-radius: 10px;
            }

            QScrollBar::handle:vertical:hover {
                background: #658076;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            /* Optional horizontal scrollbar (if ever needed) */

            QScrollBar:horizontal {
                background: #191919;
                height: 8px;
            }

            QScrollBar::handle:horizontal {
                background: #4C5C56;
                border-radius: 4px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #658076;
            }
        """)

        self.add_btn = QPushButton()
        self.add_btn.setText("+ add game")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4C5C56;
                color: white;
                border: none;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5C6C66;
            }
        """)
        self.add_btn.clicked.connect(self._add_btn_on_clicked)

        self.tree_layout.addWidget(self.search_bar)
        self.tree_layout.addWidget(self.tree)
        self.tree_layout.addWidget(self.add_btn)

        # right side
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background-color: #2C2D2C;")
        self.content_container.setMinimumWidth(600)
        self.content_container.setMinimumHeight(500)

        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.banner_label = QLabel()
        self.banner_label.setAlignment(Qt.AlignCenter) # type: ignore
        self.banner_label.setStyleSheet("background-color: #3C3C3C;")
        self.banner_label.setMinimumHeight(240)
        self.banner_label.setMaximumHeight(380)
        self.banner_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # type: ignore
        self.banner_label.setText("BANNER HERE")

        self.title_settings_row = QHBoxLayout()

        self.title_label = QLabel()
        self.title_label.setText("game name here")
        self.title_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")

        self.settings_btn = QPushButton()
        self.settings_btn.setText("settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: none;
                color: white;
                border: none;
                font-size: 14pt;
            }
            QPushButton:hover {
                color: #658076;
            }
        """)
        self.settings_btn.clicked.connect(self._settings_btn_on_clicked)

        self.title_settings_row.addWidget(self.title_label)
        self.title_settings_row.addStretch()
        self.title_settings_row.addWidget(self.settings_btn)

        self.stat_layout = QVBoxLayout()
        self.stat_layout.setContentsMargins(10, 0, 10, 10)

        self.dev_label = QLabel("game dev")
        self.dev_label.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")

        self.notes_label = QLabel("game notes")
        self.notes_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.time_played_label = QLabel("Play time: ")
        self.time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.last_time_played_label = QLabel("Last played: ")
        self.last_time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.stat_layout.addLayout(self.title_settings_row)
        self.stat_layout.addWidget(self.dev_label)
        self.stat_layout.addWidget(self.notes_label)
        self.stat_layout.addWidget(self.time_played_label)
        self.stat_layout.addWidget(self.last_time_played_label)
        
        self.content_layout.addWidget(self.banner_label, stretch=2) # i like stretch 2
        self.content_layout.addLayout(self.stat_layout)
        self.content_layout.addStretch(1) # just so there's space at the bottom so everything gets moved to the top

        self.splitter.addWidget(self.tree_container)
        self.splitter.addWidget(self.content_container)

        self.splitter.setCollapsible(0, False)  # index 0 = left widget (tree), i don't want it to close
        self.splitter.setStretchFactor(1, 1)  # content expands

        self.setCentralWidget(self.splitter)

    def _settings_btn_on_clicked(self):
        return
    
    def _add_btn_on_clicked(self):
        add_game_dialog = AddGameDialog()
        if add_game_dialog.exec():
            return

class Application(QApplication):
    def __init__(self):
        super().__init__()
        self._setup()

    def _setup(self):
        self.setQuitOnLastWindowClosed(False)
        self.aboutToQuit.connect(self._cleanup)

        self.win = MainWindow()
        self.win.show()

        # icon shenanigans so it appears in the taskbar and tray properly
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("recap.rebooted.1")
        except Exception:
            pass  # (older Windows or other OS)

        icon = QIcon(str(ICON_PATH))
        self.setWindowIcon(icon)

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(icon)
        self.tray.setVisible(True)
        self.tray.activated.connect(self._tray_on_clicked)

        self.menu = QMenu()
        self.quit_action = QAction("quit")
        self.quit_action.triggered.connect(self._on_quit)
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)

    def _cleanup(self):
        # put thread stuff
        return

    # event on whatevers
    def _on_quit(self):
        self.quit()

    def _tray_on_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.win.show()
