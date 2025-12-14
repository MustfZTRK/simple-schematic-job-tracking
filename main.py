import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QWidget, QVBoxLayout, QFileDialog, QColorDialog, QSpinBox, QLabel
from PyQt6.QtGui import QAction, QIcon, QActionGroup, QPixmap, QPainter, QColor, QPolygonF, QPen
from PyQt6.QtCore import Qt, QSize, QPointF
from styles import DARK_THEME
from canvas import TaskCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schematic Task Tracker")
        self.resize(1200, 800)
        
        # Apply Theme
        self.setStyleSheet(DARK_THEME)
        
        # Setup Menu
        self.setup_menu()
        
        # Setup Toolbar
        self.setup_toolbar()
        
        # Setup Color Toolbar
        self.setup_color_toolbar()
        
        # Setup Central Widget
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central_widget)
        
        # Canvas
        self.canvas = TaskCanvas()
        self.layout.addWidget(self.canvas)
        
        # Connect selection change to update border width display
        self.canvas.scene.selectionChanged.connect(self.update_border_width_display)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_file)
        file_menu.addAction(load_action)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Task Board", "", "JSON Files (*.json)")
        if filename:
            self.canvas.scene.save_to_file(filename)

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Task Board", "", "JSON Files (*.json)")
        if filename:
            self.canvas.scene.load_from_file(filename)

    def setup_color_toolbar(self):
        color_toolbar = QToolBar("Colors")
        color_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, color_toolbar)
        
        # Background Color
        bg_color_action = QAction("Background Color", self)
        bg_color_action.triggered.connect(self.change_background_color)
        color_toolbar.addAction(bg_color_action)
        
        # Text Color
        text_color_action = QAction("Text Color", self)
        text_color_action.triggered.connect(self.change_text_color)
        color_toolbar.addAction(text_color_action)
        
        # Reset Colors
        reset_action = QAction("Reset Colors", self)
        reset_action.triggered.connect(self.reset_colors)
        color_toolbar.addAction(reset_action)
        
        # Separator
        color_toolbar.addSeparator()
        
        # Border Width Controls
        color_toolbar.addWidget(QLabel("  Border Width: "))
        
        # Decrease border width
        decrease_border = QAction("-", self)
        decrease_border.triggered.connect(self.decrease_border_width)
        color_toolbar.addAction(decrease_border)
        
        # Border width display
        self.border_width_spinbox = QSpinBox()
        self.border_width_spinbox.setMinimum(1)
        self.border_width_spinbox.setMaximum(10)
        self.border_width_spinbox.setValue(2)
        self.border_width_spinbox.setMaximumWidth(50)
        self.border_width_spinbox.valueChanged.connect(self.set_border_width)
        color_toolbar.addWidget(self.border_width_spinbox)
        
        # Increase border width
        increase_border = QAction("+", self)
        increase_border.triggered.connect(self.increase_border_width)
        color_toolbar.addAction(increase_border)

    def change_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            for item in self.canvas.scene.selectedItems():
                if hasattr(item, 'custom_bg_color'):
                    item.custom_bg_color = color
                    item.update()

    def change_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            for item in self.canvas.scene.selectedItems():
                if hasattr(item, 'custom_text_color'):
                    item.custom_text_color = color
                    item.update()

    def reset_colors(self):
        for item in self.canvas.scene.selectedItems():
            if hasattr(item, 'custom_bg_color'):
                item.custom_bg_color = None
                item.custom_text_color = None
                item.update()
    
    def increase_border_width(self):
        current = self.border_width_spinbox.value()
        if current < 10:
            self.border_width_spinbox.setValue(current + 1)
    
    def decrease_border_width(self):
        current = self.border_width_spinbox.value()
        if current > 1:
            self.border_width_spinbox.setValue(current - 1)
    
    def set_border_width(self, value):
        """Apply border width to selected frames"""
        for item in self.canvas.scene.selectedItems():
            if hasattr(item, 'border_width'):
                item.border_width = value
                item.update()
    
    def update_border_width_display(self):
        """Update spinbox to show border width of selected frame"""
        selected_items = self.canvas.scene.selectedItems()
        for item in selected_items:
            if hasattr(item, 'border_width'):
                # Block signals to prevent triggering set_border_width
                self.border_width_spinbox.blockSignals(True)
                self.border_width_spinbox.setValue(item.border_width)
                self.border_width_spinbox.blockSignals(False)
                break  # Only update from first frame found

    def create_icon(self, shape_type, color):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if shape_type == "Rectangle":
            painter.drawRect(4, 8, 24, 16)
        elif shape_type == "Circle":
            painter.drawEllipse(4, 4, 24, 24)
        elif shape_type == "Diamond":
            path = QPolygonF([
                QPointF(16, 4),
                QPointF(28, 16),
                QPointF(16, 28),
                QPointF(4, 16)
            ])
            painter.drawPolygon(path)
        elif shape_type == "Triangle":
            path = QPolygonF([
                QPointF(16, 4),
                QPointF(28, 28),
                QPointF(4, 28)
            ])
            painter.drawPolygon(path)
        elif shape_type == "Frame":
            painter.setPen(QPen(QColor("#888888"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(4, 4, 24, 24)
        elif shape_type == "Select":
            painter.setPen(QColor("#cccccc"))
            painter.drawLine(10, 10, 22, 22)
            painter.drawLine(10, 10, 10, 22)
            painter.drawLine(10, 10, 22, 10)
        elif shape_type == "Connect":
            painter.setPen(QPen(QColor("#cccccc"), 2))
            painter.drawLine(4, 28, 28, 4)
            # Arrowhead
            painter.drawLine(28, 4, 20, 4)
            painter.drawLine(28, 4, 28, 12)
            
        painter.end()
        return QIcon(pixmap)

    def setup_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        
        # Define tools
        tools = [
            ("Select", "#cccccc"),
            ("Rectangle", "#0e639c"),
            ("Circle", "#d13838"),
            ("Diamond", "#8e38d1"),
            ("Triangle", "#d18e38"),
            ("Frame", "#888888"),
            ("Connect", "#cccccc"),
        ]
        
        for name, color in tools:
            icon = self.create_icon(name, color)
            action = QAction(icon, name, self)
            action.setCheckable(True)
            if name == "Select":
                action.setChecked(True)
            
            # Connect action to handler
            action.triggered.connect(lambda checked, n=name: self.canvas.set_tool(n))
            
            toolbar.addAction(action)
            self.tool_group.addAction(action)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
