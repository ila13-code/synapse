from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, Qt, pyqtProperty,
                          pyqtSignal)
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    """Widget toggle switch iOS-style con animazione"""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 0.0
        self._enabled = True
        self.setFixedSize(50, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Animazione per il movimento della pallina
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
    
    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def setChecked(self, checked, animate=True):
        if self._checked != checked:
            self._checked = checked
            if animate:
                self.animation.setStartValue(self._circle_position)
                self.animation.setEndValue(1.0 if checked else 0.0)
                self.animation.start()
            else:
                self.animation.stop()
                self._circle_position = 1.0 if checked else 0.0
                self.update()
    
    def isChecked(self):
        return self._checked
    
    def setEnabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.update()
        super().setEnabled(enabled)
    
    def mousePressEvent(self, event):
        if not self._enabled:
            return
        self._checked = not self._checked
        self.animation.setStartValue(self._circle_position)
        self.animation.setEndValue(1.0 if self._checked else 0.0)
        self.animation.start()
        self.toggled.emit(self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background track - grigio se disabilitato
        if not self._enabled:
            track_color = QColor('#9CA3AF')  # Grigio chiaro
        elif self._checked:
            track_color = QColor('#8B5CF6')  # Viola se attivo
        else:
            track_color = QColor('#D1D5DB')  # Grigio se inattivo
        
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 26, 13, 13)
        
        # Circle (pallina) - più scura se disabilitato
        circle_x = 3 + (50 - 26) * self._circle_position
        circle_color = QColor('#E5E7EB') if not self._enabled else QColor('#FFFFFF')
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(int(circle_x), 3, 20, 20)
