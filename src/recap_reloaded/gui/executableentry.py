from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QFileDialog

class ExecutableEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("no executable selected...")
        self.path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #4C5C56;
                padding: 4px 8px;
            }
        """)
        
        self.browse_btn = QPushButton("browse")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #658076;
                color: white;
                border: none;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #859A92;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_file)
        
        self.remove_btn = QPushButton("-")
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B4C4C;
                color: white;
                border: none;
                font-size: 16pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A85C5C;
            }
        """)
        # this is connected in addgamedialog.py with lambda
        
        layout.addWidget(self.path_edit, 1)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.remove_btn)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "select executable",
            "",
            "Executables (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
    
    def get_path(self):
        return self.path_edit.text()
    
    def set_path(self, path):
        self.path_edit.setText(path)