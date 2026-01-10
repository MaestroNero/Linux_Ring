from PySide6.QtWidgets import QListWidget, QListWidgetItem


class Sidebar(QListWidget):
    def __init__(self, sections: list[str]):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setSpacing(2)
        for section in sections:
            item = QListWidgetItem(section)
            self.addItem(item)
        self.setCurrentRow(0)
