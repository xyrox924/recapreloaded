from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect

class NotificationWidget(QWidget):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # type: ignore
            Qt.WindowStaysOnTopHint |  # type: ignore
            Qt.Tool  # type: ignore
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # type: ignore
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # type: ignore
        
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #2C2D2C;
                border: 1px solid #658076;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #658076;
                font-family: 'Raleway';
                font-size: 11pt;
                font-weight: bold;
                /*background: transparent;*/
                border: none;
            }
        """)
        
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #E4E8E7;
                font-family: 'Raleway';
                font-size: 10pt;
                /*background: transparent;*/
                border: none;
            }
        """)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

        self.container.setLayout(layout)
        
        self.container.setFixedSize(300, 80)
        self.setFixedSize(300, 80)
        
        # opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        self.position_notification()
        
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)  # type: ignore
        
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)  # type: ignore
        self.fade_out_animation.finished.connect(self.close)
        
        # timer to auto-hide
        self.display_timer = QTimer(self)
        self.display_timer.setSingleShot(True)
        self.display_timer.timeout.connect(self.start_fade_out)
    
    def position_notification(self):
        screen = QScreen.availableGeometry(self.screen())
        
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60
        
        self.move(x, y)
    
    def show_notification(self, duration=3000):
        self.show()
        self.fade_in_animation.start()
        self.display_timer.start(duration)
    
    def start_fade_out(self):
        self.fade_out_animation.start()
    
    def mousePressEvent(self, event):
        # close if clicked
        self.start_fade_out()


class NotificationManager:    
    def __init__(self):
        self.active_notifications = []
        self.notification_spacing = 8
    
    def show_notification(self, title, message, duration=3000):
        notification = NotificationWidget(title, message)
        
        # position based on existing notifications
        if self.active_notifications:
            # Stack above the topmost notification
            topmost = self.active_notifications[-1]
            new_y = topmost.y() - notification.height() - self.notification_spacing
            notification.move(topmost.x(), new_y)
        
        self.active_notifications.append(notification)
        notification.show_notification(duration)
        
        # remove from list when closed
        notification.fade_out_animation.finished.connect(
            lambda: self._remove_notification(notification)
        )
        
        return notification
    
    def _remove_notification(self, notification):
        """Remove notification from active list"""
        if notification in self.active_notifications:
            self.active_notifications.remove(notification)


# global notification manager instance
_notification_manager = None

def get_notification_manager():
    """Get the global notification manager instance"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def notify(title, message, duration=5000):
    """Convenience function to show a notification"""
    return get_notification_manager().show_notification(title, message, duration)


# testing
"""if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    window = QWidget()
    layout = QVBoxLayout(window)
    
    btn1 = QPushButton("Show 'Now Playing' Notification")
    btn1.clicked.connect(lambda: notify("Now Playing", "Dark Souls III"))
    layout.addWidget(btn1)
    
    btn2 = QPushButton("Show 'Stopped Playing' Notification")
    btn2.clicked.connect(lambda: notify("Stopped Playing", "Dark Souls III"))
    layout.addWidget(btn2)
    
    btn3 = QPushButton("Show Multiple Notifications")
    def show_multiple():
        notify("Now Playing", "Game 1")
        QTimer.singleShot(500, lambda: notify("Now Playing", "Game 2"))
        QTimer.singleShot(1000, lambda: notify("Now Playing", "Game 3"))
    btn3.clicked.connect(show_multiple)
    layout.addWidget(btn3)
    
    window.show()
    
    sys.exit(app.exec())"""