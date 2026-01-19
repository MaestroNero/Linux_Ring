from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout, QScrollArea
)

class SocialCard(QFrame):
    def __init__(self, name, url, color, icon_path):
        super().__init__()
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("SocialCard")
        
        # Style
        self.setStyleSheet(f"""
            #SocialCard {{
                background-color: rgba(5, 5, 5, 0.9);
                border: 2px solid #333;
                border-radius: 10px;
            }}
            #SocialCard:hover {{
                border: 2px solid {color};
                background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
            }}
            QLabel {{
                color: #e0e0e0;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_lbl = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            # Scale it
            icon_lbl.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
             icon_lbl.setText("🌐") # Fallback
        
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
        
        lbl = QLabel(name)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl(self.url))


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Header / Profile
        header = QHBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        
        # Avatar (Placeholder logic)
        avatar = QLabel("NR")
        avatar.setFixedSize(120, 120)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #050505; 
            color: #00ff41; 
            font-size: 48px; 
            font-weight: bold; 
            border-radius: 60px;
            border: 3px solid #00ff41;
        """)
        header.addWidget(avatar)
        
        info_box = QVBoxLayout()
        name = QLabel("Maestro Nero")
        name.setStyleSheet("font-size: 42px; font-weight: bold; color: #00ff41; text-transform: uppercase; letter-spacing: 2px;")
        info_box.addWidget(name)
        
        role = QLabel("Linux Ring Creator // Cyber Security Specialist")
        role.setStyleSheet("font-size: 20px; color: #9d00ff;")
        info_box.addWidget(role)
        
        site = QLabel('<a href="https://www.mn-cy.org" style="color: #00ff41; text-decoration: none; font-weight: bold;">[ ACCESS MAINFRAME : WWW.MN-CY.ORG ]</a>')
        site.setOpenExternalLinks(True)
        site.setStyleSheet("font-size: 16px; margin-top: 10px;")
        info_box.addWidget(site)
        
        header.addLayout(info_box)
        main_layout.addLayout(header)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #00ff41; margin-top: 10px; margin-bottom: 10px;")
        main_layout.addWidget(line)
        
        # Social Grid
        lbl_connect = QLabel("<h2>// ESTABLISH UPLINK</h2>")
        lbl_connect.setStyleSheet("color: #00ff41;")
        main_layout.addWidget(lbl_connect)
        
        social_grid = QGridLayout()
        social_grid.setSpacing(25)
        
        base_icon_path = "assets/icons/"
        links = [
            ("Instagram", "https://www.instagram.com/m.n.cy", "#E1306C", "instagram.svg"),
            ("Telegram", "https://t.me/CYBER_Nero", "#0088cc", "telegram.svg"),
            ("YouTube", "https://www.youtube.com/@MaestroNero", "#FF0000", "youtube.svg"),
            ("LinkedIn", "https://www.linkedin.com/in/maestronero/", "#0077b5", "linkedin.svg"),
            ("TikTok", "https://www.tiktok.com/@maestro_nero", "#000000", "tiktok.svg"),
            ("GitHub", "https://github.com/MaestroNero", "#ffffff", "github.svg"),
            ("Facebook", "https://www.facebook.com/mncybersec/", "#1877F2", "facebook.svg"),
            ("X (Twitter)", "https://x.com/m_n_cy", "#1DA1F2", "twitter.svg"),
        ]
        
        for idx, (name, url, color, icon_file) in enumerate(links):
            card = SocialCard(name, url, color, base_icon_path + icon_file)
            card.setFixedSize(160, 130)
            row, col = divmod(idx, 4)
            social_grid.addWidget(card, row, col)
            
        main_layout.addLayout(social_grid)
        main_layout.addStretch()
