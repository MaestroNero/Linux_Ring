from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

class Sidebar(QListWidget):
    def __init__(self, sections: list[str]):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setSpacing(5)
        self.setIconSize(QSize(24, 24))
        
        # Map section names to system icons (fallback to emojis/text if needed)
        # Using standard freedesktop icon names
        icon_map = {
            "Dashboard": "dashboard", # or speed-o-meter
            "Secure Profiles": "security-high", # or shield
            "System Monitor": "utilities-system-monitor",
            "Users": "system-users",
            "Tools": "applications-system",
            "Updates": "system-software-update",
            "Terminal": "utilities-terminal",
            "Logs": "document-open-recent",
            "About Developer": "help-about"
        }
        
        # Fallback Map if system theme is missing icons
        emoji_map = {
             "Dashboard": "📊",
            "Secure Profiles": "🛡️",
            "System Monitor": "📈",
            "Users": "👥",
            "Tools": "🧰",
            "Updates": "🔄",
            "Terminal": "💻",
            "Logs": "📝",
            "About Developer": "👨‍💻"       
        }

        for section in sections:
            item = QListWidgetItem(section)
            
            # Try load icon
            icon_name = icon_map.get(section, "")
            icon = QIcon.fromTheme(icon_name)
            
            if icon.isNull():
                 # Use emoji as text prefix if no icon
                 emoji = emoji_map.get(section, "•")
                 item.setText(f"{emoji}  {section}")
            else:
                 item.setIcon(icon)
                 
            self.addItem(item)
            
        self.setCurrentRow(0)

