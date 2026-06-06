from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from recap_reloaded.database.models import Executable
from recap_reloaded.gui.executableentry import ExecutableEntry


class ExecutableListWidget(QWidget):
    def __init__(self, add_empty_entry=True, parent=None):
        super().__init__(parent)

        self.entries_layout = QVBoxLayout(self)
        self.entries_layout.setAlignment(Qt.AlignTop) # type: ignore
        self.entries_layout.setContentsMargins(0, 0, 0, 0)
        self.entries_layout.setSpacing(10)

        if add_empty_entry:
            self.add_executable_entry()

    def add_executable_entry(self, path=""):
        entry = ExecutableEntry()
        entry.remove_btn.clicked.connect(lambda: self.remove_executable_entry(entry))
        if path:
            entry.set_path(path)
        self.entries_layout.addWidget(entry)

    def remove_executable_entry(self, entry):
        self.entries_layout.removeWidget(entry)
        entry.deleteLater()
        self.ensure_empty_entry()

    def ensure_empty_entry(self):
        if self.entries_layout.count() == 0:
            self.add_executable_entry()

    def get_executables(self):
        executables = []
        for i in range(self.entries_layout.count()):
            entry = self.entries_layout.itemAt(i).widget() # type: ignore
            if isinstance(entry, ExecutableEntry) and entry.path_edit.text().strip():
                executables.append(Executable(path=entry.path_edit.text().strip()))
        return executables
