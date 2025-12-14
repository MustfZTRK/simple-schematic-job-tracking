from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPainter, QTransform, QPen, QColor
from shapes import RectangleShape, CircleShape, DiamondShape, TriangleShape, TaskShape, ConnectionLine, FrameShape
import json

class TaskScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 5000, 5000) # Large canvas
        self.current_tool = "Select"
        self.connecting_line = None
        self.start_item = None

    def set_tool(self, tool_name):
        self.current_tool = tool_name

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == "Connect":
                item = self.itemAt(event.scenePos(), QTransform())
                if isinstance(item, TaskShape):
                    self.start_item = item
                    self.connecting_line = QGraphicsLineItem(QLineF(event.scenePos(), event.scenePos()))
                    self.connecting_line.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine))
                    self.addItem(self.connecting_line)
                    return # Don't propagate to item (avoids moving it while connecting)
            elif self.current_tool != "Select":
                pos = event.scenePos()
                self.add_shape_at(pos.x(), pos.y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.connecting_line:
            line = self.connecting_line.line()
            line.setP2(event.scenePos())
            self.connecting_line.setLine(line)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.connecting_line:
            # Find a TaskShape at the release position
            items = self.items(event.scenePos())
            target_item = None
            for item in items:
                if isinstance(item, TaskShape) and item != self.start_item:
                    target_item = item
                    break
            
            if target_item:
                connection = ConnectionLine(self.start_item, target_item)
                self.addItem(connection)
                self.start_item.add_connection(connection)
                target_item.add_connection(connection)
            
            self.removeItem(self.connecting_line)
            self.connecting_line = None
            self.start_item = None
        super().mouseReleaseEvent(event)

    def add_shape_at(self, x, y):
        shape = None
        if self.current_tool == "Rectangle":
            shape = RectangleShape(x, y)
        elif self.current_tool == "Circle":
            shape = CircleShape(x, y)
        elif self.current_tool == "Diamond":
            shape = DiamondShape(x, y)
        elif self.current_tool == "Triangle":
            shape = TriangleShape(x, y)
        elif self.current_tool == "Frame":
            shape = FrameShape(x, y)
        
        if shape:
            self.addItem(shape)

    def save_to_file(self, filename):
        data = {
            "shapes": [],
            "connections": []
        }
        
        shape_id_map = {}
        
        # Save shapes
        for item in self.items():
            if isinstance(item, TaskShape):
                shape_id = id(item)
                shape_id_map[shape_id] = len(data["shapes"])
                
                shape_data = {
                    "type": item.__class__.__name__,
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y(),
                    "title": item.title,
                    "category": item.category,
                    "description": item.description,
                    "status": item.status,
                    "custom_bg_color": item.custom_bg_color.name() if item.custom_bg_color else None,
                    "custom_text_color": item.custom_text_color.name() if item.custom_text_color else None
                }
                
                # Save Frame-specific properties
                if isinstance(item, FrameShape):
                    shape_data["width"] = item.rect().width()
                    shape_data["height"] = item.rect().height()
                    shape_data["border_width"] = item.border_width
                
                data["shapes"].append(shape_data)
        
        # Save connections
        processed_connections = set()
        for item in self.items():
            if isinstance(item, TaskShape):
                for conn in item.connections:
                    conn_id = id(conn)
                    if conn_id not in processed_connections:
                        processed_connections.add(conn_id)
                        start_id = id(conn.start_item)
                        end_id = id(conn.end_item)
                        
                        if start_id in shape_id_map and end_id in shape_id_map:
                            data["connections"].append({
                                "start": shape_id_map[start_id],
                                "end": shape_id_map[end_id]
                            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Clear scene
        self.clear()
        
        # Load shapes
        shapes = []
        for shape_data in data["shapes"]:
            shape = None
            if shape_data["type"] == "RectangleShape":
                shape = RectangleShape(shape_data["x"], shape_data["y"])
            elif shape_data["type"] == "CircleShape":
                shape = CircleShape(shape_data["x"], shape_data["y"])
            elif shape_data["type"] == "DiamondShape":
                shape = DiamondShape(shape_data["x"], shape_data["y"])
            elif shape_data["type"] == "TriangleShape":
                shape = TriangleShape(shape_data["x"], shape_data["y"])
            elif shape_data["type"] == "FrameShape":
                # Load with custom dimensions if available
                w = shape_data.get("width", 300)
                h = shape_data.get("height", 200)
                shape = FrameShape(shape_data["x"], shape_data["y"], w, h)
            
            if shape:
                shape.title = shape_data["title"]
                shape.category = shape_data.get("category", "General")
                shape.description = shape_data["description"]
                shape.status = shape_data["status"]
                if shape_data.get("custom_bg_color"):
                    shape.custom_bg_color = QColor(shape_data["custom_bg_color"])
                if shape_data.get("custom_text_color"):
                    shape.custom_text_color = QColor(shape_data["custom_text_color"])
                
                # Restore Frame-specific properties
                if isinstance(shape, FrameShape) and "border_width" in shape_data:
                    shape.border_width = shape_data["border_width"]
                
                self.addItem(shape)
                shapes.append(shape)
        
        # Load connections
        for conn_data in data["connections"]:
            start_shape = shapes[conn_data["start"]]
            end_shape = shapes[conn_data["end"]]
            connection = ConnectionLine(start_shape, end_shape)
            self.addItem(connection)
            start_shape.add_connection(connection)
            end_shape.add_connection(connection)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Get selected items
            selected_items = self.selectedItems()
            
            for item in selected_items:
                if isinstance(item, TaskShape):
                    # Remove all connections associated with this shape
                    connections_to_remove = item.connections.copy()
                    for conn in connections_to_remove:
                        # Remove from both shapes
                        if conn in conn.start_item.connections:
                            conn.start_item.connections.remove(conn)
                        if conn in conn.end_item.connections:
                            conn.end_item.connections.remove(conn)
                        # Remove from scene
                        self.removeItem(conn)
                    
                    # Remove the shape itself
                    self.removeItem(item)
        
        super().keyPressEvent(event)

class TaskCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = TaskScene(self)
        self.setScene(self.scene)
        
        # Graphics View Settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Zooming
        self._zoom = 0
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor

            # Save the scene pos
            old_pos = self.mapToScene(event.position().toPoint())

            # Zoom
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
                self._zoom += 1
            else:
                zoom_factor = zoom_out_factor
                self._zoom -= 1

            self.scale(zoom_factor, zoom_factor)

            # Get the new position
            new_pos = self.mapToScene(event.position().toPoint())

            # Move scene to old position
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
        else:
            super().wheelEvent(event)

    def set_tool(self, tool_name):
        self.scene.set_tool(tool_name)
        if tool_name == "Select":
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
