import os
import sys
from PySide6.QtCore import Qt, QProcess, QByteArray
from PySide6.QtGui import QFont, QKeyEvent, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget, QLineEdit

class TerminalWidget(QWidget):
    """
    A simple embedded terminal using QProcess.
    It emulates a shell by running /bin/bash and piping input/output.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Output area
        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QPlainTextEdit {
                background-color: #002b36;
                color: #839496;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: none;
            }
        """)
        layout.addWidget(self.output_area)
        
        # Input line
        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("""
            QLineEdit {
                background-color: #073642;
                color: #839496;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: none;
                padding: 5px;
            }
        """)
        self.input_line.returnPressed.connect(self.send_command)
        self.input_line.setPlaceholderText("$ Enter command...")
        layout.addWidget(self.input_line)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        
        # Start the shell
        self.start_shell()

    def start_shell(self):
        # We start a persistent bash shell
        shell = os.environ.get("SHELL", "/bin/bash")
        self.process.start(shell, ["-i"])
        self.append_output(f"Started {shell} session...\n")

    def read_output(self):
        data = self.process.readAllStandardOutput()
        text = data.data().decode('utf-8', errors='replace')
        self.append_output(text)

    def append_output(self, text):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()

    def send_command(self):
        cmd = self.input_line.text()
        if not cmd:
            return
            
        # Append command to view for feedback
        self.append_output(f"$ {cmd}\n")
        
        # Send to process
        self.process.write(QByteArray(f"{cmd}\n".encode()))
        self.input_line.clear()
        
        if cmd.strip() == "exit":
            self.input_line.setDisabled(True)

    def process_finished(self, exit_code, exit_status):
        self.append_output(f"\nShell exited with code {exit_code}")
        self.input_line.setDisabled(True)
