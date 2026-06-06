import os

from pathlib import Path

from PySide6.QtCore import Qt, QSortFilterProxyModel, QSize, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QColor
from PySide6.QtWidgets import QMainWindow, QWidget, QTreeView, QSplitter, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy, QMessageBox, QStyledItemDelegate, QStyleOptionViewItem, QStyle

from recap_reloaded.utils import get_time_formatted
from recap_reloaded.win_utils import add_to_startup, remove_from_startup, is_in_startup
from recap_reloaded.database.database import Database, DatabaseError
from recap_reloaded.gui.addgamedialog import AddGameDialog
from recap_reloaded.gui.settingsdialog import SettingsDialog
from recap_reloaded.gui.blurtransition import BlurTransition
from recap_reloaded.gui.notification import notify
from recap_reloaded.tracking.game_tracker import GameTracker

from recap_reloaded.config import (
    BANNERS_PATH,
    DB_PATH,
    DBS_PATH,
    GAMETXT_PATH,
    ICONS_PATH,
    WIN1_ICON_PATH,
    WIN2_ICON_PATH,
    regkey_name,
)

SWATCH_PIXMAP_ROLE = Qt.UserRole + 1 # type: ignore


class GameTreeDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        swatch = index.data(SWATCH_PIXMAP_ROLE)
        if not isinstance(swatch, QPixmap) or swatch.isNull():
            return

        item_option = QStyleOptionViewItem(option)
        self.initStyleOption(item_option, index)
        decoration_rect = item_option.widget.style().subElementRect(
            QStyle.SE_ItemViewItemDecoration, # type: ignore
            item_option,
            item_option.widget
        )
        painter.drawPixmap(decoration_rect, swatch)


# container, layout, then widgets, then add widgets and layouts to the layout of the container
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        os.makedirs(str(DBS_PATH), exist_ok=True)
        os.makedirs(str(BANNERS_PATH), exist_ok=True)
        os.makedirs(str(ICONS_PATH), exist_ok=True)
        self.db = Database(str(DB_PATH))

        self.current_game = None
        self.current_game_banner_pixmap = None
        self.game_swatch_cache = {}
        self.cleanup_done = False

        self.tracker = GameTracker(self.db)
        self.tracker.game_started.connect(self._on_game_started)
        self.tracker.game_stopped.connect(self._on_game_stopped)

        self._setup_ui()
        self._refresh_tree_view()
        self.tracker.start()

        if is_in_startup(regkey_name):
            self.startup_btn.setIcon(self.win1_icon)
        else:
            self.startup_btn.setIcon(self.win2_icon)

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
                            try:
                                self.current_game = self.db.get_game(last_game_id)
                            except DatabaseError as e:
                                self._show_database_error(str(e))
                            break
        except ValueError:
            print("Last game_id in game.txt not a number. File tampering?")
        except FileNotFoundError:
            print("Last game game.txt file doesn't exist yet.")

    def _setup_ui(self):
        self.setWindowTitle("recap reloaded")
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
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

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
        self.tree.setIndentation(16)
        self.tree.setItemDelegate(GameTreeDelegate(self.tree))
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
        self.tree.setIconSize(QSize(16, 16))
        self.tree.expandAll()

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # type: ignore
        self.proxy_model.setFilterKeyColumn(0)  # game names in collumn 0

        self.tree.setModel(self.proxy_model)
        self.tree.selectionModel().selectionChanged.connect(self._tree_on_selection_changed)

        self.search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)

        self.startup_btn = QPushButton()
        self.startup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C2D2C;
                color: white;
                border: none;
                margin: 2px;

            }
            QPushButton:hover {
                background-color: #5C6C66;
            }
        """)
        self.startup_btn.setFixedSize(32, 32)
        self.win1_icon = QIcon(str(WIN1_ICON_PATH))
        self.win2_icon = QIcon(str(WIN2_ICON_PATH))
        self.startup_btn.setIcon(self.win1_icon)
        self.startup_btn.clicked.connect(self._startup_btn_on_clicked)

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

        self.add_btn_other_layout = QHBoxLayout()
        self.add_btn_other_layout.addWidget(self.startup_btn)
        self.add_btn_other_layout.addWidget(self.add_btn)

        self.tree_layout.addWidget(self.search_bar)
        self.tree_layout.addWidget(self.tree)
        self.tree_layout.addLayout(self.add_btn_other_layout)

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

        self.splitter.setChildrenCollapsible(False)
        self.splitter.setCollapsible(0, False)  # index 0 = left widget (tree), i don't want it to close
        self.splitter.setStretchFactor(1, 1)  # content expands

        self.setCentralWidget(self.splitter)

        # i'm hitler and i love qt event queue
        QTimer.singleShot(0, self._refresh_game_banner)
        QTimer.singleShot(10, lambda: self.resizeEvent(None))

    def _refresh_tree_view(self):
        try:
            games = self.db.get_all_games()
        except DatabaseError as e:
            self._show_database_error(str(e))
            return

        self.model.removeRows(0, self.model.rowCount())

        if games:
            for game in games:
                child = QStandardItem(game[1])
                swatch = self._get_game_swatch(game[2])
                child.setIcon(QIcon(swatch))
                child.setData(swatch, SWATCH_PIXMAP_ROLE) # type: ignore
                child.setEditable(False)
                # game id
                child.setData(game[0], Qt.UserRole) # type: ignore
                self.root.appendRow(child)

    def _get_game_swatch(self, banner_path):
        cache_key = banner_path or None
        if cache_key not in self.game_swatch_cache:
            self.game_swatch_cache[cache_key] = self._create_game_swatch_pixmap(banner_path)
        return self.game_swatch_cache[cache_key]

    def _create_game_swatch_pixmap(self, banner_path):
        size = self.tree.iconSize().width()
        placeholder = QPixmap(size, size)
        placeholder.fill(QColor("#3C3C3C"))

        if not banner_path:
            return placeholder

        pixmap = QPixmap(str(BANNERS_PATH / banner_path))
        if pixmap.isNull():
            return placeholder

        scaled_pixmap = pixmap.scaled(
            size,
            size,
            Qt.KeepAspectRatioByExpanding, # type: ignore
            Qt.SmoothTransformation # type: ignore
        )

        x = max(0, (scaled_pixmap.width() - size) // 2)
        y = max(0, (scaled_pixmap.height() - size) // 2)
        return scaled_pixmap.copy(x, y, size, size)

    def _refresh_game_banner(self):
        if self.current_game is not None and self.current_game.banner_path:
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
            try:
                self.time_played_label.setText(f"total time played: {get_time_formatted(self.db.get_game_playtime(self.current_game.id))}")
                self.first_time_played_label.setText(f"first time played: {self.db.get_game_first_time(self.current_game.id)}")
                self.last_time_played_label.setText(f"last time played: {self.db.get_game_last_time(self.current_game.id)}")
                self.avg_time_played_label.setText(f"average time played a day: {get_time_formatted(self.db.get_average_playtime_day(self.current_game.id))}")
            except DatabaseError as e:
                self._show_database_error(str(e))
                return
            self.current_game_banner_pixmap = None # clear the pixmap cause then it won't update if it isn't # why i did this
            self._refresh_game_banner()

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

    def _on_splitter_moved(self, pos, index):
        self._refresh_game_banner()
        self.resizeEvent(None)

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
        try:
            self.current_game = self.db.get_game(game_id)
        except DatabaseError as e:
            self._show_database_error(str(e))
            return

        self._refresh_game_content()
            
    def _settings_btn_on_clicked(self):
        if self.current_game is not None:
            try:
                self.current_game = self.db.get_game_full(self.current_game.id) # type: ignore
            except DatabaseError as e:
                self._show_database_error(str(e))
                return
            if self.current_game is None:
                self._show_database_error("Could not find the selected game.")
                return
            # it gets the literal same exact game from the database no way this should ever fail
            settings_dialog = SettingsDialog(self.current_game) # type: ignore
            while settings_dialog.exec():
                updated_game = settings_dialog.get_game_data()
                try:
                    self.db.update_game(updated_game)
                    self.current_game = updated_game
                    self._refresh_game_content()
                    self._refresh_tree_view()
                    break
                except DatabaseError as e:
                    self._show_database_error(str(e), settings_dialog)

    def _startup_btn_on_clicked(self):
        if not is_in_startup(regkey_name):
            self.startup_btn.setIcon(self.win1_icon)
            add_to_startup(regkey_name)
        else:
            self.startup_btn.setIcon(self.win2_icon)
            remove_from_startup(regkey_name)

    def _add_btn_on_clicked(self):
        add_game_dialog = AddGameDialog()
        while add_game_dialog.exec():
            game = add_game_dialog.get_game_data()
            try:
                self.db.insert_game(game)
                self._refresh_tree_view()
                break
            except DatabaseError as e:
                self._show_database_error(str(e), add_game_dialog)

    def cleanup(self):
        if self.cleanup_done:
            return
        self.cleanup_done = True

        self.tracker.stop()

        if self.current_game:
            with open(GAMETXT_PATH, "w") as f:
                f.write(str(self.current_game.id))

    def _show_database_error(self, message, parent=None):
        dialog = QMessageBox(parent or self)
        dialog.setWindowTitle("Database error")
        dialog.setIcon(QMessageBox.Warning) # type: ignore
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Ok) # type: ignore
        dialog.setStyleSheet("""
            QMessageBox {
                background-color: #2C2D2C;
                color: #E4E8E7;
                font-family: 'Raleway';
                font-size: 10pt;
            }
            QMessageBox QLabel {
                color: #E4E8E7;
                background-color: transparent;
            }
            QPushButton {
                background-color: #658076;
                color: white;
                border: none;
                padding: 8px 18px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #859A92;
            }
            QPushButton:pressed {
                background-color: #4C5C56;
            }
        """)
        dialog.exec()

