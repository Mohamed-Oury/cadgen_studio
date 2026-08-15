from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter, QFont
from PySide6.QtCore import Qt, QPointF, Signal, QRectF

class MapViewer(QGraphicsView):
    selection_changed = Signal(list)  # Emit list of (ilot_name, lot_name)
    mouse_moved = Signal(float, float) # Emit (x, y)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.setMouseTracking(True)
        
        # Panning state
        self._is_panning = False
        self._last_pan_point = None

        self.lot_items = {}
        self.text_items = []
        
        self.preview_box_5000 = None
        self.preview_box_500 = None

        self.scene.selectionChanged.connect(self.on_selection_changed)
        
    def draw_lots(self, lots_data):
        self.scene.clear()
        self.lot_items.clear()
        self.text_items.clear()
        self.preview_box_5000 = None
        self.preview_box_500 = None
        
        default_pen = QPen(QColor("#333333"))
        default_pen.setWidth(0) # Cosmetic pen (1 pixel regardless of zoom)
        
        default_brush = QBrush(Qt.transparent)
        selected_brush = QBrush(QColor(204, 228, 247, 150)) # QGIS light blue selection

        font = QFont("Arial", 8)
        ilot_font = QFont("Arial", 12, QFont.Bold)
        
        for ilot_name, ilot_data in lots_data.items():
            
            pos = ilot_data.get("pos")
            if pos:
                ilot_item = QGraphicsTextItem(ilot_name)
                ilot_item.setFont(ilot_font)
                ilot_item.setDefaultTextColor(QColor("#003366"))
                text_rect = ilot_item.boundingRect()
                ilot_item.setPos(pos[0] - text_rect.width() / 2, -pos[1] - text_rect.height() / 2)
                ilot_item.setZValue(2) # Above everything
                self.scene.addItem(ilot_item)
                self.text_items.append(ilot_item)
                
            for lot_name, lot_info in ilot_data.get('lots', {}).items():
                polygon = lot_info['geom']
                
                # Convert shapely polygon to QPolygonF
                qpoly = QPolygonF()
                for x, y in polygon.exterior.coords:
                    # Y axis is inverted in QGraphicsView compared to standard cartesian
                    qpoly.append(QPointF(x, -y))
                    
                item = QGraphicsPolygonItem(qpoly)
                item.setPen(default_pen)
                item.setBrush(default_brush)
                item.setFlag(QGraphicsItem.ItemIsSelectable)
                
                # Store data in item for click events
                item.setData(0, ilot_name)
                item.setData(1, lot_name)
                
                self.scene.addItem(item)
                self.lot_items[(ilot_name, lot_name)] = item
                
                # Add text label
                text_item = QGraphicsTextItem(lot_name)
                text_item.setFont(font)
                text_item.setDefaultTextColor(QColor("#666666"))
                # Center text on polygon centroid
                centroid = polygon.centroid
                text_rect = text_item.boundingRect()
                text_item.setPos(centroid.x - text_rect.width() / 2, -centroid.y - text_rect.height() / 2)
                text_item.setZValue(1) # Above polygons
                self.scene.addItem(text_item)
                self.text_items.append(text_item)
                
        # Fit view to scene
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    def on_selection_changed(self):
        selected_lots = []
        for item in self.scene.items():
            if isinstance(item, QGraphicsPolygonItem):
                if item.isSelected():
                    item.setBrush(QBrush(QColor(204, 228, 247, 150)))
                    selected_lots.append((item.data(0), item.data(1)))
                else:
                    item.setBrush(QBrush(Qt.transparent))
        self.selection_changed.emit(selected_lots)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        # Note: Y is inverted in our scene
        self.mouse_moved.emit(scene_pos.x(), -scene_pos.y())
        
        if self._is_panning and self._last_pan_point:
            delta = self.mapToScene(self._last_pan_point) - self.mapToScene(event.pos())
            self._last_pan_point = event.pos()
            self.setSceneRect(self.sceneRect().translated(delta.x(), delta.y()))
            self.translate(delta.x(), delta.y()) # Visual translate
            # Workaround for scrolling:
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(int(h_bar.value() + delta.x()))
            v_bar.setValue(int(v_bar.value() + delta.y()))

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self._last_pan_point = None
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
            
    def update_preview_boxes(self, center_x, center_y, width_5000, height_5000, width_500, height_500):
        if not self.preview_box_5000:
            self.preview_box_5000 = QGraphicsRectItem()
            pen = QPen(QColor("#FF0000"))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            self.preview_box_5000.setPen(pen)
            self.preview_box_5000.setZValue(10)
            self.scene.addItem(self.preview_box_5000)
            
            # Label for 5000
            self.label_5000 = QGraphicsTextItem("1/5000", self.preview_box_5000)
            self.label_5000.setDefaultTextColor(QColor("#FF0000"))
            self.label_5000.setPos(0, -20)
            
        if not self.preview_box_500:
            self.preview_box_500 = QGraphicsRectItem()
            pen = QPen(QColor("#0000FF"))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            self.preview_box_500.setPen(pen)
            self.preview_box_500.setZValue(10)
            self.scene.addItem(self.preview_box_500)
            
            self.label_500 = QGraphicsTextItem("1/500", self.preview_box_500)
            self.label_500.setDefaultTextColor(QColor("#0000FF"))
            self.label_500.setPos(0, -20)

        # Y is inverted
        rect_5000 = QRectF(center_x - width_5000/2, -center_y - height_5000/2, width_5000, height_5000)
        self.preview_box_5000.setRect(rect_5000)
        self.label_5000.setPos(rect_5000.left(), rect_5000.top() - 20)
        
        rect_500 = QRectF(center_x - width_500/2, -center_y - height_500/2, width_500, height_500)
        self.preview_box_500.setRect(rect_500)
        self.label_500.setPos(rect_500.left(), rect_500.top() - 20)

