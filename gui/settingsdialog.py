import shutil

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QWidget, QLineEdit, QTextEdit, QFileDialog, QMessageBox

from database.models import Executable, Game
from database.database import Database
from gui.executableentry import ExecutableEntry

from config import BANNERS_PATH

class SettingsDialog(QDialog):
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self._setup_ui()

        self.game = game

        self.banner_path = ""
        if game.banner_path is not None:
            self.banner_path = game.banner_path
            path = Path(BANNERS_PATH / game.banner_path)
            banner_btn_pixmap = QPixmap(path)
            if not banner_btn_pixmap.isNull():
                scaled_pixmap = banner_btn_pixmap.scaled(
                    self.banner_btn.size(),
                    Qt.KeepAspectRatio, # type: ignore
                    Qt.SmoothTransformation # type: ignore
                )
                self.banner_btn.setIcon(QIcon(scaled_pixmap))
                self.banner_btn.setIconSize(self.banner_btn.size())
                self.banner_btn.setText("")  # remove the +

        self.name_edit.setText(game.name)
        self.developer_edit.setText(game.developer)
        self.notes_edit.setText(game.notes)

        for exe in game.executables:
            self.add_executable_entry(exe.path if isinstance(exe, Executable) else exe)
        if self.executables_layout.count() == 0:
            self.add_executable_entry()

    def _setup_ui(self):
        self.setWindowTitle("game settings")
        self.setMinimumSize(640, 600)
        self.setStyleSheet("background-color: #2C2D2C; color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # scroll area for executable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # type: ignore
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # type: ignore
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #191919;
            }
                             
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

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(5, 5, 5, 5)

        self.banner_btn = QPushButton()
        self.banner_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 20pt;
            }
            QPushButton:hover {
                background-color: #859A92;
            }
        """)
        self.banner_btn.setText("+")
        self.banner_btn.setFixedSize(200, 105)
        self.banner_btn.clicked.connect(self._banner_btn_on_clicked)
        
        banner_btn_container = QHBoxLayout()
        banner_btn_container.addStretch()
        banner_btn_container.addWidget(self.banner_btn)
        banner_btn_container.addStretch()
        
        name_label = QLabel("game name *")
        name_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("enter game name...")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #4C5C56;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #658076;
            }
        """)
        
        dev_label = QLabel("developer")
        dev_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        
        self.developer_edit = QLineEdit()
        self.developer_edit.setPlaceholderText("enter developer name...")
        self.developer_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #4C5C56;
                padding: 8px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #658076;
            }
        """)
        
        notes_label = QLabel("notes")
        notes_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("enter notes...")
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #4C5C56;
                padding: 8px;
                font-size: 10pt;
            }
            QTextEdit:focus {
                border: 1px solid #658076;
            }
        """)

        # executables
        exe_label = QLabel("executables")
        exe_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        
        self.executables_container = QWidget()
        self.executables_layout = QVBoxLayout(self.executables_container)
        self.executables_layout.setAlignment(Qt.AlignTop) # type: ignore
        self.executables_layout.setContentsMargins(0, 0, 0, 0)
        self.executables_layout.setSpacing(10)

        add_exe_btn = QPushButton("+ add executable")
        add_exe_btn.setStyleSheet("""
            QPushButton {
                background-color: #658076;
                color: white;
                border: none;
                padding: 8px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #859A92;
            }
        """)
        add_exe_btn.clicked.connect(self.add_executable_entry)

        # bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("save")
        save_btn.setFixedWidth(100)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #658076;
                color: white;
                border: none;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #859A92;
            }
        """)
        save_btn.clicked.connect(self._save_btn_on_clicked)
        
        cancel_btn = QPushButton("cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        container_layout.addLayout(banner_btn_container)
        container_layout.addWidget(name_label)
        container_layout.addWidget(self.name_edit)
        container_layout.addWidget(dev_label)
        container_layout.addWidget(self.developer_edit)
        container_layout.addWidget(notes_label)
        container_layout.addWidget(self.notes_edit)
        container_layout.addWidget(exe_label)  
        container_layout.addWidget(self.executables_container)
        container_layout.addWidget(add_exe_btn)
        container_layout.addStretch(1)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        layout.addLayout(button_layout)
        
    def add_executable_entry(self, path=""):
        entry = ExecutableEntry()
        entry.remove_btn.clicked.connect(lambda: self.remove_executable_entry(entry))
        if path:
            entry.set_path(path)
        self.executables_layout.addWidget(entry)

    def remove_executable_entry(self, entry):
        self.executables_layout.removeWidget(entry)
        entry.deleteLater()

        if self.executables_layout.count() == 0:
            self.add_executable_entry()

    def get_game_data(self):
        executables = []
        for i in range(self.executables_layout.count()):
            entry = self.executables_layout.itemAt(i).widget()
            if isinstance(entry, ExecutableEntry) and entry.path_edit.text().strip():
                executables.append(Executable(path=entry.path_edit.text().strip()))
        
        return Game(
            id=self.game.id,
            name=self.name_edit.text().strip(),
            developer=self.developer_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip(),
            executables=executables,
            banner_path=self.banner_path
        )
    
    # on events
    def _save_btn_on_clicked(self):
        if not self.name_edit.text().strip():
            # could add a QMessageBox here to show error
            self.name_edit.setFocus()
            self.name_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #3C3C3C;
                    color: white;
                    border: 2px solid #8B4C4C;
                    padding: 8px;
                    font-size: 10pt;
                }
            """)
            return
        self.accept()

    def _banner_btn_on_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "select banner image",
            "",
            "images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            temp = Path(file_path)
            try:
                shutil.copy(str(temp), BANNERS_PATH)
                self.banner_path = temp.name # get the filename with its extension not the full path

                # set button icon to the selected image
                banner_btn_pixmap = QPixmap(temp)
                if not banner_btn_pixmap.isNull():
                    scaled_pixmap = banner_btn_pixmap.scaled(
                        self.banner_btn.size(),
                        Qt.KeepAspectRatio, # type: ignore
                        Qt.SmoothTransformation # type: ignore
                    )
                    self.banner_btn.setIcon(QIcon(scaled_pixmap))
                    self.banner_btn.setIconSize(self.banner_btn.size())
                    self.banner_btn.setText("")  # remove the +
            except shutil.SameFileError:
                print("source and destination are the same file.")
            except PermissionError:
                print("permission denied.")
