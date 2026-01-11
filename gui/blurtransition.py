from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap, QImage, QLinearGradient, QColor, QTransform
from PySide6.QtWidgets import QGraphicsScene, QGraphicsBlurEffect

class BlurTransition(QWidget):
    def __init__(self, parent=None, min_height=60, max_height=120, bg_color="#FFFFFF"):
        super().__init__(parent)
        self.min_height = min_height
        self.max_height = max_height
        self.current_height = max_height
        self.bg_color = QColor(bg_color) # color it fades into
        self.blurred_pixmap = None
        self.cached_scaled_pixmap = None
        self.last_width = 0
        self.last_height = 0
        self.setMinimumHeight(min_height)
        self.setMaximumHeight(max_height)

    def set_background_color(self, color):
        self.bg_color = QColor(color)
        self.cached_scaled_pixmap = None  # clear cache to force redraw
        self.update()
        
    def set_banner_pixmap(self, pixmap):
        if pixmap is None or pixmap.isNull():
            self.blurred_pixmap = None
            self.cached_scaled_pixmap = None
        else:
            self.blurred_pixmap = self._create_blurred_pixmap(pixmap)
            self.cached_scaled_pixmap = None  # clear cache when new image is set
        self.last_width = 0
        self.last_height = 0
        self.update()  # trigger repaint
    
    def set_proportional_height(self, banner_height):
        # scale between min and max based on banner size
        proportion = 1.2
        new_height = int(banner_height * proportion)
        self.current_height = max(self.min_height, min(new_height, self.max_height))
        self.setFixedHeight(self.current_height)
        self.cached_scaled_pixmap = None  # clear cache when height changes
        self.last_height = 0
        
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
        painter.setRenderHint(QPainter.SmoothPixmapTransform)   # type: ignore
        
        if self.blurred_pixmap and not self.blurred_pixmap.isNull():
            # only rescale if width or height changed
            if self.cached_scaled_pixmap is None or self.last_width != self.width() or self.last_height != self.height():
                scaled_blur = self.blurred_pixmap.scaled(
                    self.width(), 
                    self.blurred_pixmap.height(),
                    Qt.KeepAspectRatio, # type: ignore
                    Qt.SmoothTransformation # type: ignore
                )
                
                # extract the bottom portion (last N pixels)
                extract_height = min(self.current_height, scaled_blur.height())
                source_y = scaled_blur.height() - extract_height
                
                bottom_portion = scaled_blur.copy(
                    0, source_y,
                    scaled_blur.width(), extract_height
                )
                
                # mirror on y axis and stretch a bit
                self.cached_scaled_pixmap = bottom_portion.transformed(
                    QTransform().scale(1, -1.3)
                )
                self.last_width = self.width()
                self.last_height = self.height()
            
            painter.drawPixmap(0, 0, self.cached_scaled_pixmap)
            
            # create vertical-only gradient overlay that fades to solid color
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor(self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), 50))
            gradient.setColorAt(0.3, QColor(self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), 120))
            gradient.setColorAt(0.6, QColor(self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), 200))
            gradient.setColorAt(1.0, QColor(self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), 255))
            
            painter.fillRect(0, 0, self.width(), self.height(), gradient)
        else:
            # fallback to solid color
            painter.fillRect(self.rect(), self.bg_color)
        
        painter.end()