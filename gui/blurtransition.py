from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap, QImage, QLinearGradient, QColor, QTransform
from PySide6.QtWidgets import QGraphicsScene, QGraphicsBlurEffect

class BlurTransition(QWidget):
    def __init__(self, parent=None, transition_height=80):
        super().__init__(parent)
        self.transition_height = transition_height
        self.blurred_pixmap = None
        self.setFixedHeight(transition_height)
        
    def set_banner_pixmap(self, pixmap):
        if pixmap is None or pixmap.isNull():
            self.blurred_pixmap = None
        else:
            self.blurred_pixmap = self._create_blurred_pixmap(pixmap)
        self.update()
        
    def _create_blurred_pixmap(self, pixmap):
        if pixmap.isNull():
            return pixmap
            
        scene = QGraphicsScene()
        pixmap_item = scene.addPixmap(pixmap)
        
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(40)  # Heavy blur - adjust as needed
        pixmap_item.setGraphicsEffect(blur_effect)
        
        blurred_image = QImage(pixmap.size(), QImage.Format_ARGB32) # type: ignore
        blurred_image.fill(Qt.transparent) # type: ignore
        
        painter = QPainter(blurred_image)
        painter.setRenderHint(QPainter.Antialiasing) # type: ignore
        scene.render(painter)
        painter.end()
        
        return QPixmap.fromImage(blurred_image)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # type: ignore
        
        if self.blurred_pixmap and not self.blurred_pixmap.isNull():
            scaled_blur = self.blurred_pixmap.scaled(
                self.width(), 
                self.blurred_pixmap.height(),
                Qt.KeepAspectRatioByExpanding, # type: ignore
                Qt.SmoothTransformation # type: ignore
            )
            
            source_y = max(0, scaled_blur.height() - self.transition_height - 50)
            source_rect_pixmap = scaled_blur.copy(
                0, source_y,
                self.width(), self.transition_height
            )

            flipped_pixmap = source_rect_pixmap.transformed(
                QTransform().scale(1, -1)  # Scale Y by -1 to flip vertically
            )
            
            painter.drawPixmap(0, 0, flipped_pixmap)
            
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(44, 45, 44, 100))
            gradient.setColorAt(0.5, QColor(44, 45, 44, 180))
            gradient.setColorAt(1, QColor(44, 45, 44, 255))
            
            painter.fillRect(0, 0, self.width(), self.height(), gradient)
        else:
            painter.fillRect(self.rect(), QColor(44, 45, 44))
        
        painter.end()