from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsSceneMouseEvent, QGraphicsLineItem
from PyQt6.QtGui import QBrush, QPen, QColor, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
from task_dialog import TaskDialog

import math

class ConnectionLine(QGraphicsLineItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QPen(Qt.GlobalColor.white, 3)) # Thicker line
        self.setZValue(-1) # Behind shapes
        self.update_position()

    def update_position(self):
        line = QLineF(self.start_item.scenePos(), self.end_item.scenePos())
        start_pos = self.start_item.get_edge_point(line.p2())
        end_pos = self.end_item.get_edge_point(line.p1())
        self.setLine(QLineF(start_pos, end_pos))

    def boundingRect(self):
        extra = 20
        return super().boundingRect().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget):
        if self.line().length() == 0:
            return
            
        painter.setPen(self.pen())
        painter.setBrush(self.pen().color())
        
        line = self.line()
        painter.drawLine(line)
        
        # Draw Arrowhead
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = 15
        
        arrow_p1 = line.p2() - QPointF(math.cos(angle - math.pi / 6) * arrow_size,
                                       math.sin(angle - math.pi / 6) * arrow_size)
        arrow_p2 = line.p2() - QPointF(math.cos(angle + math.pi / 6) * arrow_size,
                                       math.sin(angle + math.pi / 6) * arrow_size)
                                       
        arrow_head = QPolygonF()
        arrow_head.append(line.p2())
        arrow_head.append(arrow_p1)
        arrow_head.append(arrow_p2)
        
        painter.drawPolygon(arrow_head)

class TaskShape:
    def __init__(self, color="#0e639c"):
        self.base_color = QColor(color)
        self.default_brush = QBrush(self.base_color)
        self.selected_brush = QBrush(self.base_color.lighter(120))
        self.pen = QPen(Qt.GlobalColor.black, 3)
        
        # Data
        self.title = "New Task"
        self.category = "General"
        self.description = ""
        self.status = "Todo"
        self.connections = []
        
        # Custom colors
        self.custom_bg_color = None  # None means use default
        self.custom_text_color = None  # None means use default (black)
        
        # Flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def add_connection(self, connection):
        self.connections.append(connection)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for connection in self.connections:
                connection.update_position()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        # Update color based on status or custom color
        if self.custom_bg_color:
            color = self.custom_bg_color
            border_color = QColor(self.custom_bg_color).darker(120)
        elif self.status == "Done":
            color = QColor("#38d156") # Green
            border_color = QColor("#00ff00") # Bright green border
        elif self.status == "In Progress":
            color = QColor("#388ed1") # Blue
            border_color = QColor("#ffaa00") # Yellow/Orange border
        else:  # Todo
            color = self.base_color
            border_color = QColor("#0099ff") # Blue border

        if self.isSelected():
            painter.setBrush(QBrush(color.lighter(120)))
            painter.setPen(QPen(Qt.GlobalColor.yellow, 3, Qt.PenStyle.DashLine))
        else:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(border_color, 3))  # Thicker border for visibility

    def draw_header(self, painter, rect):
        # Draw Header Background
        header_height = 25
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), header_height)
        
        # Clip to shape if needed (simple rect for now)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50))) # Darker transparent overlay
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(header_rect)
        
        # Draw Category Text
        text_color = self.custom_text_color if self.custom_text_color else Qt.GlobalColor.black
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, self.category)
        
        # Reset Font for Title
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        dialog = TaskDialog(None, self.title, self.description, self.status, self.category)
        if dialog.exec():
            data = dialog.get_data()
            self.title = data["title"]
            self.category = data["category"]
            self.description = data["description"]
            self.status = data["status"]
            self.update() # Trigger repaint

    def get_edge_point(self, other_pos):
        # Default center (fallback)
        return self.scenePos()

class RectangleShape(TaskShape, QGraphicsRectItem):
    def __init__(self, x, y, w=150, h=80):
        QGraphicsRectItem.__init__(self, 0, 0, w, h)
        TaskShape.__init__(self)
        self.setPos(x, y)

    def paint(self, painter, option, widget):
        TaskShape.paint(self, painter, option, widget)
        painter.drawRect(self.rect())
        self.draw_header(painter, self.rect())
        
        # Draw Title (below header)
        content_rect = self.rect().adjusted(0, 25, 0, 0)
        text_color = self.custom_text_color if self.custom_text_color else Qt.GlobalColor.black
        painter.setPen(text_color)
        painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, self.title)
    
    def mouseDoubleClickEvent(self, event):
        TaskShape.mouseDoubleClickEvent(self, event)

    def get_edge_point(self, other_pos):
        center = self.scenePos() + self.rect().center()
        line = QLineF(center, other_pos)
        polygon = QPolygonF(self.rect())
        polygon.translate(self.scenePos())
        
        p1 = polygon.first()
        for i in range(1, polygon.count()):
            p2 = polygon.at(i)
            poly_line = QLineF(p1, p2)
            intersection_type, intersection_point = poly_line.intersects(line)
            if intersection_type == QLineF.IntersectionType.BoundedIntersection:
                return intersection_point
            p1 = p2
        # Close the loop
        poly_line = QLineF(polygon.last(), polygon.first())
        intersection_type, intersection_point = poly_line.intersects(line)
        if intersection_type == QLineF.IntersectionType.BoundedIntersection:
            return intersection_point
            
        return center

class CircleShape(TaskShape, QGraphicsEllipseItem):
    def __init__(self, x, y, w=100, h=100):
        QGraphicsEllipseItem.__init__(self, 0, 0, w, h)
        TaskShape.__init__(self, color="#d13838") # Red for urgent
        self.setPos(x, y)

    def paint(self, painter, option, widget):
        TaskShape.paint(self, painter, option, widget)
        painter.drawEllipse(self.rect())
        
        # Draw Header (approximate for circle)
        # For circle, maybe just draw text at top? Or a clipped rect?
        # Let's keep it simple: Text at top
        text_color = self.custom_text_color if self.custom_text_color else Qt.GlobalColor.black
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        
        header_rect = self.rect().adjusted(0, 15, 0, -50)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, self.category)
        
        # Title
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        content_rect = self.rect().adjusted(0, 30, 0, 0)
        painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, self.title)

    def mouseDoubleClickEvent(self, event):
        TaskShape.mouseDoubleClickEvent(self, event)

    def get_edge_point(self, other_pos):
        center = self.scenePos() + self.rect().center()
        line = QLineF(center, other_pos)
        angle = line.angle() * 3.14159 / 180
        # QLineF angle is in degrees, 0 is 3 o'clock, increases counter-clockwise (usually)
        # But Qt coordinate system Y is down.
        # Let's use simple trig.
        dx = other_pos.x() - center.x()
        dy = other_pos.y() - center.y()
        import math
        angle = math.atan2(-dy, dx) # Note: -dy because Y is down
        
        r = self.rect().width() / 2
        # x = cx + r * cos(a)
        # y = cy - r * sin(a) # - because Y is down
        
        edge_x = center.x() + r * math.cos(angle)
        edge_y = center.y() - r * math.sin(angle)
        
        return QPointF(edge_x, edge_y)

class DiamondShape(TaskShape, QGraphicsPolygonItem):
    def __init__(self, x, y, w=120, h=80):
        QGraphicsPolygonItem.__init__(self)
        TaskShape.__init__(self, color="#8e38d1") # Purple for milestone
        
        # Create Diamond Polygon
        polygon = QPolygonF([
            QPointF(w/2, 0),
            QPointF(w, h/2),
            QPointF(w/2, h),
            QPointF(0, h/2)
        ])
        self.setPolygon(polygon)
        self.setPos(x, y)
        self._width = w
        self._height = h

    def paint(self, painter, option, widget):
        TaskShape.paint(self, painter, option, widget)
        painter.drawPolygon(self.polygon())
        
        # Header Text (Top half)
        text_color = self.custom_text_color if self.custom_text_color else Qt.GlobalColor.black
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        
        rect = QRectF(0, 0, self._width, self._height)
        header_rect = rect.adjusted(0, 15, 0, -40)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, self.category)
        
        # Title
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        content_rect = rect.adjusted(0, 10, 0, 0)
        painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, self.title)

    def mouseDoubleClickEvent(self, event):
        TaskShape.mouseDoubleClickEvent(self, event)

    def get_edge_point(self, other_pos):
        center = self.scenePos() + self.boundingRect().center()
        line = QLineF(center, other_pos)
        polygon = self.polygon()
        polygon.translate(self.scenePos())
        
        p1 = polygon.first()
        for i in range(1, polygon.count()):
            p2 = polygon.at(i)
            poly_line = QLineF(p1, p2)
            intersection_type, intersection_point = poly_line.intersects(line)
            if intersection_type == QLineF.IntersectionType.BoundedIntersection:
                return intersection_point
            p1 = p2
        # Close loop
        poly_line = QLineF(polygon.last(), polygon.first())
        intersection_type, intersection_point = poly_line.intersects(line)
        if intersection_type == QLineF.IntersectionType.BoundedIntersection:
            return intersection_point
            
        return center

class TriangleShape(TaskShape, QGraphicsPolygonItem):
    def __init__(self, x, y, w=100, h=100):
        QGraphicsPolygonItem.__init__(self)
        TaskShape.__init__(self, color="#d18e38") # Orange for bug
        
        # Create Triangle Polygon
        polygon = QPolygonF([
            QPointF(w/2, 0),
            QPointF(w, h),
            QPointF(0, h)
        ])
        self.setPolygon(polygon)
        self.setPos(x, y)
        self._width = w
        self._height = h

    def paint(self, painter, option, widget):
        TaskShape.paint(self, painter, option, widget)
        painter.drawPolygon(self.polygon())
        
        # Header Text (Top part)
        text_color = self.custom_text_color if self.custom_text_color else Qt.GlobalColor.black
        painter.setPen(text_color)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        
        rect = QRectF(0, 0, self._width, self._height)
        header_rect = rect.adjusted(0, 25, 0, -50)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, self.category)
        
        # Title
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        content_rect = rect.adjusted(0, 20, 0, 0)
        painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, self.title)

    def mouseDoubleClickEvent(self, event):
        TaskShape.mouseDoubleClickEvent(self, event)

    def get_edge_point(self, other_pos):
        center = self.scenePos() + self.boundingRect().center()
        line = QLineF(center, other_pos)
        polygon = self.polygon()
        polygon.translate(self.scenePos())
        
        p1 = polygon.first()
        for i in range(1, polygon.count()):
            p2 = polygon.at(i)
            poly_line = QLineF(p1, p2)
            intersection_type, intersection_point = poly_line.intersects(line)
            if intersection_type == QLineF.IntersectionType.BoundedIntersection:
                return intersection_point
            p1 = p2
        # Close loop
        poly_line = QLineF(polygon.last(), polygon.first())
        intersection_type, intersection_point = poly_line.intersects(line)
        if intersection_type == QLineF.IntersectionType.BoundedIntersection:
            return intersection_point
            
        return center


class FrameShape(TaskShape, QGraphicsRectItem):
    """A large frame for grouping and organizing other shapes"""
    def __init__(self, x, y, w=300, h=200):
        QGraphicsRectItem.__init__(self, 0, 0, w, h)
        TaskShape.__init__(self, color="#555555")
        self.setPos(x, y)
        self.setZValue(-10)  # Behind everything else
        
        # Frame-specific properties
        self.frame_label = "Group"
        self.show_label = True
        self.border_width = 2  # Adjustable border width
        
        # Resizing properties
        self.resize_handle_size = 10
        self.resizing = False
        self.resize_handle = None  # Which handle is being dragged
        self.resize_start_pos = None
        self.resize_start_rect = None
    
    def paint(self, painter, option, widget):
        # Draw semi-transparent background
        if self.custom_bg_color:
            bg_color = QColor(self.custom_bg_color)
        else:
            bg_color = QColor("#2a2a2a")
        
        bg_color.setAlpha(30)  # Very transparent
        painter.setBrush(QBrush(bg_color))
        
        # Dashed border with adjustable width
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.yellow, self.border_width, Qt.PenStyle.DashLine))
        else:
            border_color = self.custom_text_color if self.custom_text_color else QColor("#888888")
            painter.setPen(QPen(border_color, self.border_width, Qt.PenStyle.DashLine))
        
        painter.drawRect(self.rect())
        
        # Draw label if enabled
        if self.show_label:
            text_color = self.custom_text_color if self.custom_text_color else QColor("#aaaaaa")
            painter.setPen(text_color)
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            
            # Draw label at top-left corner
            label_rect = QRectF(5, 5, self.rect().width() - 10, 25)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, 
                           self.category if self.category != "General" else "Group")
        
        # Draw resize handles when selected
        if self.isSelected():
            handle_color = QColor("#ffff00")
            painter.setBrush(QBrush(handle_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            
            rect = self.rect()
            handles = self.get_resize_handles()
            
            for handle_rect in handles.values():
                painter.drawRect(handle_rect)
    
    def get_resize_handles(self):
        """Get the positions of resize handles"""
        rect = self.rect()
        h = self.resize_handle_size
        
        return {
            'top_left': QRectF(rect.left() - h/2, rect.top() - h/2, h, h),
            'top_right': QRectF(rect.right() - h/2, rect.top() - h/2, h, h),
            'bottom_left': QRectF(rect.left() - h/2, rect.bottom() - h/2, h, h),
            'bottom_right': QRectF(rect.right() - h/2, rect.bottom() - h/2, h, h),
            'top': QRectF(rect.center().x() - h/2, rect.top() - h/2, h, h),
            'bottom': QRectF(rect.center().x() - h/2, rect.bottom() - h/2, h, h),
            'left': QRectF(rect.left() - h/2, rect.center().y() - h/2, h, h),
            'right': QRectF(rect.right() - h/2, rect.center().y() - h/2, h, h),
        }
    
    def get_handle_at_pos(self, pos):
        """Check if position is over a resize handle"""
        if not self.isSelected():
            return None
        
        handles = self.get_resize_handles()
        for name, handle_rect in handles.items():
            if handle_rect.contains(pos):
                return name
        return None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSelected():
            handle = self.get_handle_at_pos(event.pos())
            if handle:
                self.resizing = True
                self.resize_handle = handle
                self.resize_start_pos = event.scenePos()
                self.resize_start_rect = QRectF(self.rect())
                self.resize_start_scene_pos = self.scenePos()
                # Disable movement while resizing
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.resizing and self.resize_handle:
            # Calculate delta in scene coordinates
            delta = event.scenePos() - self.resize_start_pos
            new_rect = QRectF(self.resize_start_rect)
            new_pos = QPointF(self.resize_start_scene_pos)
            
            # Adjust rectangle based on which handle is being dragged
            if 'left' in self.resize_handle:
                new_rect.setLeft(self.resize_start_rect.left() + delta.x())
                new_pos.setX(self.resize_start_scene_pos.x() + delta.x())
            if 'right' in self.resize_handle:
                new_rect.setRight(self.resize_start_rect.right() + delta.x())
            if 'top' in self.resize_handle:
                new_rect.setTop(self.resize_start_rect.top() + delta.y())
                new_pos.setY(self.resize_start_scene_pos.y() + delta.y())
            if 'bottom' in self.resize_handle:
                new_rect.setBottom(self.resize_start_rect.bottom() + delta.y())
            
            # Normalize the rectangle to ensure positive width/height
            new_rect = new_rect.normalized()
            
            # Ensure minimum size
            if new_rect.width() >= 50 and new_rect.height() >= 50:
                # Update position and size
                self.setPos(new_pos)
                self.setRect(new_rect)
                
                # Update connections
                for connection in self.connections:
                    connection.update_position()
                
                self.update()
            
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            self.resize_handle = None
            self.resize_start_pos = None
            self.resize_start_rect = None
            self.resize_start_scene_pos = None
            # Re-enable movement
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        # Override to customize frame properties
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton
        
        dialog = QDialog()
        dialog.setWindowTitle("Frame Properties")
        dialog.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #ffffff; }
            QLabel { color: #ffffff; }
            QLineEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; padding: 5px; }
            QSpinBox { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555; padding: 5px; }
            QPushButton { background-color: #0e639c; color: #ffffff; border: none; padding: 8px; }
            QPushButton:hover { background-color: #1177bb; }
        """)
        
        layout = QVBoxLayout()
        
        # Category/Label
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Label:"))
        label_input = QLineEdit(self.category if self.category != "General" else "Group")
        label_layout.addWidget(label_input)
        layout.addLayout(label_layout)
        
        # Border Width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Border Width:"))
        width_input = QSpinBox()
        width_input.setMinimum(1)
        width_input.setMaximum(10)
        width_input.setValue(self.border_width)
        width_layout.addWidget(width_input)
        layout.addLayout(width_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec():
            self.category = label_input.text()
            self.border_width = width_input.value()
            self.update()
    
    def get_edge_point(self, other_pos):
        center = self.scenePos() + self.rect().center()
        line = QLineF(center, other_pos)
        polygon = QPolygonF(self.rect())
        polygon.translate(self.scenePos())
        
        p1 = polygon.first()
        for i in range(1, polygon.count()):
            p2 = polygon.at(i)
            poly_line = QLineF(p1, p2)
            intersection_type, intersection_point = poly_line.intersects(line)
            if intersection_type == QLineF.IntersectionType.BoundedIntersection:
                return intersection_point
            p1 = p2
        # Close the loop
        poly_line = QLineF(polygon.last(), polygon.first())
        intersection_type, intersection_point = poly_line.intersects(line)
        if intersection_type == QLineF.IntersectionType.BoundedIntersection:
            return intersection_point
            
        return center
