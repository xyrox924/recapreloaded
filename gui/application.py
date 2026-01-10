import os

from PySide6.QtCore import Qt, QSortFilterProxyModel, QSize, Signal, QObject
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTreeView, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy, QSystemTrayIcon, QMenu

from utils import get_time_formatted
from gui.addgamedialog import AddGameDialog
from database.database import Database

from config import *

db = Database(str(DB_PATH))

# container, layout, then widgets, then add widgets and layouts to the layout of the container
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._refresh_tree_view()

        os.makedirs(str(DBS_PATH), exist_ok=True)
        os.makedirs(str(BANNERS_PATH), exist_ok=True)
        os.makedirs(str(ICONS_PATH), exist_ok=True)

        self.current_game = None
        self.current_game_banner_pixmap = None
        # sucks
        try:
            with open("game.txt") as f:
                last_game_id = int(f.readline())
                if last_game_id:
                    for row in range(self.model.rowCount()):
                        item = self.model.item(row)
                        if item and item.data(Qt.UserRole) == last_game_id: # type: ignore
                            source_index = self.model.indexFromItem(item)
                            proxy_index = self.proxy_model.mapFromSource(source_index)
                            self.tree.setCurrentIndex(proxy_index)
                            self.current_game = db.get_game(last_game_id)
                            break
        except ValueError:
            print("Last game_id in game.txt not a number. File tampering?")
        except FileNotFoundError:
            print("Last game game.txt file doesn't exist yet.")

        # i'm hitler and i love qt event queue
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._refresh_game_banner)

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

        self.model = QStandardItemModel()
        self.root = self.model.invisibleRootItem()

        self.tree.setModel(self.model)
        self.tree.expandAll()

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # type: ignore
        self.proxy_model.setFilterKeyColumn(0)  # game names in collumn 0

        self.tree.setModel(self.proxy_model)
        self.tree.selectionModel().selectionChanged.connect(self._tree_on_selection_changed)

        self.search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)

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
        #self.banner_label.setText("BANNER HERE")
        #self.banner_label.setScaledContents(False)

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

        self.time_played_label = QLabel("play time: ")
        self.time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.first_time_played_label = QLabel("first played: ")
        self.first_time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.last_time_played_label = QLabel("last played: ")
        self.last_time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.stat_layout.addLayout(self.title_settings_row)
        self.stat_layout.addWidget(self.dev_label)
        self.stat_layout.addWidget(self.notes_label)
        self.stat_layout.addWidget(self.time_played_label)
        self.stat_layout.addWidget(self.first_time_played_label)
        self.stat_layout.addWidget(self.last_time_played_label)
        
        self.content_layout.addWidget(self.banner_label, stretch=2) # i like stretch 2
        self.content_layout.addLayout(self.stat_layout)
        self.content_layout.addStretch(1) # just so there's space at the bottom so everything gets moved to the top

        self.splitter.addWidget(self.tree_container)
        self.splitter.addWidget(self.content_container)

        self.splitter.setCollapsible(0, False)  # index 0 = left widget (tree), i don't want it to close
        self.splitter.setStretchFactor(1, 1)  # content expands

        self.setCentralWidget(self.splitter)

    def _refresh_tree_view(self):
        self.model.removeRows(0, self.model.rowCount())

        games = db.get_all_games()
        if games:
            for game in games:
                child = QStandardItem(game[1])
                child.setEditable(False)
                # game id
                child.setData(game[0], Qt.UserRole) # type: ignore
                self.root.appendRow(child)

    def _refresh_game_banner(self):
        if self.current_game is not None and self.current_game.banner_path is not None:
                if self.current_game_banner_pixmap is None or self.current_game_banner_pixmap.isNull():
                    self.current_game_banner_pixmap = QPixmap(Path(BANNERS_PATH / self.current_game.banner_path))
                    
                if not self.current_game_banner_pixmap.isNull():
                    scaled_pixmap = self.current_game_banner_pixmap.scaled(
                        self.banner_label.size(),
                        Qt.KeepAspectRatioByExpanding,  # type: ignore
                        Qt.SmoothTransformation  # type: ignore
                    )
                    
                    x = (scaled_pixmap.width() - self.banner_label.width()) // 2
                    y = (scaled_pixmap.height() - self.banner_label.height()) // 2
                    
                    cropped_pixmap = scaled_pixmap.copy(
                        x, y, 
                        self.banner_label.width(), 
                        self.banner_label.height()
                    )
                    
                    self.banner_label.setPixmap(cropped_pixmap)
                else:
                    self.banner_label.clear()
        else:
            self.banner_label.clear()

    # on events
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_game_banner()

    def _tree_on_selection_changed(self, selected):
        # get the game
        indexes = selected.indexes()
        if not indexes:
            return

        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)

        item = self.model.itemFromIndex(source_index)
        if item is None:
            return
        
        game_id = item.data(Qt.UserRole) # type: ignore
        self.current_game = db.get_game(game_id)

        # change the info contents
        if self.current_game is not None:
            self.title_label.setText(self.current_game.name)
            self.dev_label.setText(self.current_game.developer)
            self.notes_label.setText(self.current_game.notes)
            self.time_played_label.setText(f"total time played: {get_time_formatted(db.get_game_playtime(game_id))}")
            self.first_time_played_label.setText(f"first time played: {db.get_game_first_time(game_id)}")
            self.last_time_played_label.setText(f"last time played: {db.get_game_last_time(game_id)}")
            self.current_game_banner_pixmap = None # clear the pixmap cause then it won't update if it isn't
            self._refresh_game_banner()
            
    def _settings_btn_on_clicked(self):
        return
    
    def _add_btn_on_clicked(self):
        add_game_dialog = AddGameDialog()
        if add_game_dialog.exec():
            game = add_game_dialog.get_game_data()
            db.insert_game(game)
            self._refresh_tree_view()

    def cleanup(self):
        if self.current_game:
            with open("game.txt", "w") as f:
                f.write(str(self.current_game.id))

class Application(QApplication):
    def __init__(self):
        super().__init__()
        self._setup()

    def _setup(self):
        self.setQuitOnLastWindowClosed(False)
        self.aboutToQuit.connect(self._on_about_to_quit)

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

    # event on whatevers
    def _on_about_to_quit(self):
        self.win.cleanup()

    def _on_quit(self):
        self.quit()

    def _tray_on_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.win.show()
