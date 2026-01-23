from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGridLayout, QScrollArea
)
from core.utils import resource_path

class SocialCard(QFrame):
    def __init__(self, name, url, color, icon_path):
        super().__init__()
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("SocialCard")
        
        # Parse color for hover effect
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Style
        self.setStyleSheet(f"""
            #SocialCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.9),
                    stop:1 rgba(51, 65, 85, 0.7));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
            #SocialCard:hover {{
                border: 1px solid {color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r}, {g}, {b}, 0.2),
                    stop:1 rgba(51, 65, 85, 0.8));
            }}
            QLabel {{
                color: #e2e8f0;
                background: transparent;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icon
        icon_lbl = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_lbl.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
             icon_lbl.setText("🌐")
             icon_lbl.setStyleSheet("font-size: 32px;")
        
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)
        
        lbl = QLabel(name)
        lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color};")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

    def mousePressEvent(self, event):
        QDesktopServices.openUrl(QUrl(self.url))


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)
        
        # Header Frame
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(139, 92, 246, 0.15),
                    stop:0.5 rgba(30, 41, 59, 0.8),
                    stop:1 rgba(34, 197, 94, 0.1));
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 20px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 30, 30, 30)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Avatar
        avatar = QLabel("💎")
        avatar.setFixedSize(100, 100)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #22c55e);
            font-size: 48px; 
            border-radius: 50px;
            border: 3px solid #38bdf8;
        """)
        header_layout.addWidget(avatar)
        
        header_layout.addSpacing(20)
        
        info_box = QVBoxLayout()
        info_box.setSpacing(8)
        
        name = QLabel("Maestro Nero")
        name.setStyleSheet("""
            font-size: 36px; 
            font-weight: bold; 
            color: #f1f5f9;
            background: transparent;
        """)
        info_box.addWidget(name)
        
        role = QLabel("Linux Ring Creator • Cyber Security Specialist")
        role.setStyleSheet("font-size: 16px; color: #a855f7; background: transparent;")
        info_box.addWidget(role)
        
        site = QLabel('<a href="https://www.mn-cy.org" style="color: #38bdf8; text-decoration: none; font-weight: bold;">🌐 WWW.MN-CY.ORG</a>')
        site.setOpenExternalLinks(True)
        site.setStyleSheet("font-size: 14px; margin-top: 5px; background: transparent;")
        info_box.addWidget(site)
        
        header_layout.addLayout(info_box)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)
        
        # Social Section
        social_frame = QFrame()
        social_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
        """)
        social_layout = QVBoxLayout(social_frame)
        social_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_connect = QLabel("🔗 Connect With Me")
        lbl_connect.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8; background: transparent;")
        social_layout.addWidget(lbl_connect)
        social_grid = QGridLayout()
        social_grid.setSpacing(15)
        
        base_icon_path = resource_path("assets/icons/")
        links = [
            ("Instagram", "https://www.instagram.com/m.n.cy", "#E1306C", "instagram.svg"),
            ("Telegram", "https://t.me/CYBER_Nero", "#0088cc", "telegram.svg"),
            ("YouTube", "https://www.youtube.com/@MaestroNero", "#FF0000", "youtube.svg"),
            ("LinkedIn", "https://www.linkedin.com/in/maestronero/", "#0077b5", "linkedin.svg"),
            ("TikTok", "https://www.tiktok.com/@maestro_nero", "#ff0050", "tiktok.svg"),
            ("GitHub", "https://github.com/MaestroNero", "#8b5cf6", "github.svg"),
            ("Facebook", "https://www.facebook.com/mncybersec/", "#1877F2", "facebook.svg"),
            ("X (Twitter)", "https://x.com/m_n_cy", "#38bdf8", "twitter.svg"),
        ]
        
        for idx, (name, url, color, icon_file) in enumerate(links):
            card = SocialCard(name, url, color, base_icon_path + icon_file)
            card.setFixedSize(140, 110)
            row, col = divmod(idx, 4)
            social_grid.addWidget(card, row, col)
        
        social_layout.addLayout(social_grid)
        main_layout.addWidget(social_frame)
        main_layout.addStretch()
