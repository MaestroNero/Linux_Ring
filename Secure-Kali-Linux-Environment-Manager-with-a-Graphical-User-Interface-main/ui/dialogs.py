from PySide6.QtWidgets import QMessageBox, QInputDialog, QWidget


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    dialog = QMessageBox(parent)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    dialog.setDefaultButton(QMessageBox.No)
    return dialog.exec() == QMessageBox.Yes


def prompt_text(parent: QWidget, title: str, label: str, default: str = "") -> str | None:
    text, ok = QInputDialog.getText(parent, title, label, text=default)
    if not ok or not text:
        return None
    return text
