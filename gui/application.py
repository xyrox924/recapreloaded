import os, sys, time, threading

from datetime import datetime

from PySide6.QtCore import Qt, QSortFilterProxyModel, QSize, Signal, QObject, QTimer, QSharedMemory
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QAction, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTreeView, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy, QSystemTrayIcon, QMenu

from utils import get_time_formatted, get_running_process_names
from database.database import Database
from gui.addgamedialog import AddGameDialog
from gui.settingsdialog import SettingsDialog
from gui.blurtransition import BlurTransition
from gui.notification import notify

from config import *

db = Database(str(DB_PATH)) # i don't like this being global anymore

class TrackingSignals(QObject):
    game_started = Signal(int, str)  # game_id, game_name
    game_stopped = Signal(int, str)  # game_id, game_name

# container, layout, then widgets, then add widgets and layouts to the layout of the container
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # single instance only
        self._memory = QSharedMemory("recap_rebooted_singleton_key")
        
        if self._memory.attach():
            print("another instance is already running")
            sys.exit(0)
        
        if not self._memory.create(1):
            print("critical error can't start application")
            sys.exit(1)

        os.makedirs(str(DBS_PATH), exist_ok=True)
        os.makedirs(str(BANNERS_PATH), exist_ok=True)
        os.makedirs(str(ICONS_PATH), exist_ok=True)

        self.current_game = None
        self.current_game_banner_pixmap = None

        self.tracking_signals = TrackingSignals()
        self.tracking_signals.game_started.connect(self._on_game_started)
        self.tracking_signals.game_stopped.connect(self._on_game_stopped)

        self.active_sessions = {}
        self.stop_event = threading.Event()
        self.tracker_thread = threading.Thread(target=self._tracking_loop, args=(self.tracking_signals,), daemon=True)
        self.tracker_thread.start()

        self._setup_ui()
        self._refresh_tree_view()

        # sucks
        try:
            with open(GAMETXT_PATH) as f:
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

    def _setup_ui(self):
        self.setWindowTitle("recap rebooted")
        self.resize(1000, 640)
        self.setMinimumHeight(600)

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
        self.content_layout.setSpacing(0)

        self.banner_label = QLabel()
        self.banner_label.setAlignment(Qt.AlignCenter) # type: ignore
        self.banner_label.setStyleSheet("background-color: #3C3C3C;")
        self.banner_label.setMinimumHeight(150)
        self.banner_label.setMaximumHeight(440)
        self.banner_label.setSizePolicy(
            QSizePolicy.Expanding, # type: ignore
            QSizePolicy.Ignored # type: ignore
        )
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
                border: none;
            }
        """)
        self.settings_btn.clicked.connect(self._settings_btn_on_clicked)

        self.title_settings_row.addWidget(self.title_label)
        self.title_settings_row.addStretch()
        self.title_settings_row.addWidget(self.settings_btn)

        self.stat_layout = QVBoxLayout()
        self.stat_layout.setContentsMargins(10, 0, 10, 10)
        self.stat_layout.setSpacing(6)

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

        self.avg_time_played_label = QLabel("average time played a day: ")
        self.avg_time_played_label.setStyleSheet("color: white; font-size: 14pt; font-weight: normal;")

        self.stat_layout.addLayout(self.title_settings_row)
        self.stat_layout.addWidget(self.dev_label)
        self.stat_layout.addWidget(self.notes_label)
        self.stat_layout.addWidget(self.time_played_label)
        self.stat_layout.addWidget(self.first_time_played_label)
        self.stat_layout.addWidget(self.last_time_played_label)
        self.stat_layout.addWidget(self.avg_time_played_label)

        self.blur_transition = BlurTransition(min_height=140, max_height=900, bg_color="#2C2C2C")

        self.content_bottom = QWidget()
        self.content_bottom.setStyleSheet("background-color: #2C2D2C;")  # Match background
        self.content_bottom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # type: ignore
        #self.content_bottom.setMinimumHeight(300)

        self.blur_transition.setParent(self.content_bottom)

        self.stats_wrapper = QWidget(self.content_bottom)
        self.stats_wrapper.setStyleSheet("background: transparent;")  # transparent so blur shows through
        self.stats_wrapper_layout = QVBoxLayout(self.stats_wrapper)
        self.stats_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_wrapper_layout.setSpacing(0)

        self.stat_layout.setContentsMargins(10, 10, 10, 10)
        self.stats_wrapper_layout.addLayout(self.stat_layout)
        self.stats_wrapper_layout.addStretch(1)

        self.content_layout.addWidget(self.banner_label)
        self.content_layout.addWidget(self.content_bottom)
        self.content_layout.setStretch(0, 2)  # banner
        self.content_layout.setStretch(1, 3)  # content_bottom

        self.splitter.addWidget(self.tree_container)
        self.splitter.addWidget(self.content_container)

        self.splitter.setCollapsible(0, False)  # index 0 = left widget (tree), i don't want it to close
        self.splitter.setStretchFactor(1, 1)  # content expands

        self.setCentralWidget(self.splitter)

        # i'm hitler and i love qt event queue
        QTimer.singleShot(0, self._refresh_game_banner)
        QTimer.singleShot(10, lambda: self.resizeEvent(None))

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
                        Qt.KeepAspectRatioByExpanding, # type: ignore
                        Qt.SmoothTransformation # type: ignore
                    )
                    
                    x = (scaled_pixmap.width() - self.banner_label.width()) // 2
                    y = (scaled_pixmap.height() - self.banner_label.height()) // 2
                    
                    cropped_pixmap = scaled_pixmap.copy(
                        x, y, 
                        self.banner_label.width(), 
                        self.banner_label.height()
                    )
                    
                    self.banner_label.setPixmap(cropped_pixmap)
                    
                    # update blur transition with cropped pixmap AND set proportional height
                    self.blur_transition.set_proportional_height(self.banner_label.height())
                    self.blur_transition.set_banner_pixmap(cropped_pixmap)
                else:
                    self.banner_label.clear()
                    self.blur_transition.set_banner_pixmap(None)
        else:
            self.banner_label.clear()
            self.blur_transition.set_banner_pixmap(None)

    def _refresh_game_content(self):
        if self.current_game is not None:
            self.title_label.setText(self.current_game.name)
            self.dev_label.setText(self.current_game.developer)
            self.notes_label.setText(self.current_game.notes)
            self.time_played_label.setText(f"total time played: {get_time_formatted(db.get_game_playtime(self.current_game.id))}")
            self.first_time_played_label.setText(f"first time played: {db.get_game_first_time(self.current_game.id)}")
            self.last_time_played_label.setText(f"last time played: {db.get_game_last_time(self.current_game.id)}")
            self.avg_time_played_label.setText(f"average time played a day: {get_time_formatted(db.get_average_playtime_day(self.current_game.id))}")
            self.current_game_banner_pixmap = None # clear the pixmap cause then it won't update if it isn't # why i did this
            self._refresh_game_banner()

    def _tracking_loop(self, signals):
        while not self.stop_event.is_set():
            running_processes = get_running_process_names()
            known_exes = db.get_known_executables()

            for exe_name, game_id in known_exes.items():
                if exe_name in running_processes and game_id not in self.active_sessions:
                    self.active_sessions[game_id] = datetime.now()

                    game = db.get_game(game_id)
                    # None checking should be safe to ignore don't care
                    print(f"Started tracking game {game.name}") # type: ignore
                    signals.game_started.emit(game_id, game.name) # type: ignore

            for game_id in list(self.active_sessions.keys()):
                # check if ANY exe for this game is still running
                game_exes = [exe for exe, gid in known_exes.items() if gid == game_id]
                if not any(exe in running_processes for exe in game_exes):
                    start_time = self.active_sessions[game_id]
                    end_time = datetime.now()
                    
                    db.insert_session(game_id, start_time, end_time)
                    del self.active_sessions[game_id]
                    
                    game = db.get_game(game_id)
                    # None checking here too should be safe to ignore don't care
                    print(f"Ended tracking game {game.name}") # type: ignore # should be safe to ignore too don't care also
                    signals.game_stopped.emit(game_id, game.name) # type: ignore

            time.sleep(10)

    # signal handlers
    def _on_game_started(self, game_id, game_name):
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item and item.data(Qt.UserRole) == game_id: # type: ignore
                item.setForeground(QColor("#658076"))
                item.setText(game_name + " - Running")
                break

        notify("Now playing", game_name)

    def _on_game_stopped(self, game_id, game_name):
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item and item.data(Qt.UserRole) == game_id: # type: ignore
                item.setForeground(QColor("#E4E8E7"))
                item.setText(game_name)
                break

        notify("Stopped playing", game_name)

    # on events
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_game_banner()

        # the hitler strikes again
        #if hasattr(self, 'blur_transition') and hasattr(self, 'stats_wrapper') and hasattr(self, 'content_bottom'):
        # get the actual width and the blur's current height (set by set_proportional_height)
        width = self.content_bottom.width()
        blur_height = self.blur_transition.current_height  # Use the proportional height!
        
        # position blur at top with its proportional height
        self.blur_transition.setGeometry(0, -1, width, blur_height + 1) # -1 and +1 so the banner and blur overlap just a tiny bit because qt rounding when moving widgets makes a 1px gap between them sometimes on resize
        
        # stats wrapper overlays from top, extending to bottom
        bottom_height = max(self.content_bottom.height(), 400)
        self.stats_wrapper.setGeometry(0, 0, width, bottom_height)
        self.stats_wrapper.raise_()  # ensure stats are on top i hate this

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

        self._refresh_game_content()
            
    def _settings_btn_on_clicked(self):
        if self.current_game is not None:
            self.current_game = db.get_game_full(self.current_game.id) # type: ignore
            # it gets the literal same exact game from the database no way this should ever fail
            settings_dialog = SettingsDialog(self.current_game) # type: ignore
            if settings_dialog.exec():
                self.current_game = settings_dialog.get_game_data()
                db.update_game(self.current_game)
                self._refresh_game_content()
            
    def _add_btn_on_clicked(self):
        add_game_dialog = AddGameDialog()
        if add_game_dialog.exec():
            game = add_game_dialog.get_game_data()
            db.insert_game(game)
            self._refresh_tree_view()

    def cleanup(self):
        for game_id, start_time in self.active_sessions.items():
            db.insert_session(game_id, start_time, datetime.now())
        
        self.stop_event.set()
        self.tracker_thread.join(timeout=2)

        if self.current_game:
            with open(GAMETXT_PATH, "w") as f:
                f.write(str(self.current_game.id))

class Application(QApplication):
    def __init__(self):
        super().__init__()
        self._setup()

    def _setup(self):
        self.setQuitOnLastWindowClosed(False)
        self.aboutToQuit.connect(self._on_about_to_quit)

        self.win = MainWindow()

        # icon shenanigans so it appears in the taskbar and tray properly. i have no idea why this is needed
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("recap.rebooted.1")
        except Exception:
            pass  # (older Windows or other OS)

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
        
        self.win.show()

    # event on whatevers
    def _on_about_to_quit(self):
        self.win.cleanup()

    def _on_quit(self):
        self.quit()

    def _tray_on_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.win.show()
            self.win.raise_()  # bring to front
            self.win.activateWindow()  # focus it
