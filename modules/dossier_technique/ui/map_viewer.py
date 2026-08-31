 # pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem, QGraphicsPathItem
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter, QFont, QPainterPath
# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt, QPointF, Signal, QRectF
from shapely.geometry import Point

class MapViewer(QGraphicsView):
    selection_changed = Signal(list)  # Emit list of (ilot_name, lot_name)
    mouse_moved = Signal(float, float) # Emit (x, y)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.setMouseTracking(True)
        
        # Panning state
        self._is_panning = False
        self._last_pan_point = None
        self._click_start_pos = None

        self.lot_items = {}
        self.text_items = []
        self.layer_groups = {}
        
        self.preview_box_5000 = None
        self.preview_box_500 = None

        self.scene.selectionChanged.connect(self.on_selection_changed)
        
    def draw_background_layers(self, layers_data):
        self.layer_groups = {}
        default_pen = QPen(QColor("#B0B0B0")) # Gris clair pour l'arrière-plan
        default_pen.setWidth(0)
        
        for layer_name, entities in layers_data.items():
            group = self.scene.createItemGroup([])
            group.setZValue(-1) # En dessous des lots
            
            for ent in entities:
                if ent['type'] == 'line':
                    pts = ent['points']
                    line = self.scene.addLine(pts[0][0], -pts[0][1], pts[1][0], -pts[1][1], default_pen)
                    group.addToGroup(line)
                elif ent['type'] == 'polyline':
                    pts = ent['points']
                    path = QPainterPath()
                    if pts:
                        path.moveTo(pts[0][0], -pts[0][1])
                        for x, y in pts[1:]:
                            path.lineTo(x, -y)
                    path_item = self.scene.addPath(path, default_pen)
                    group.addToGroup(path_item)
            
            self.layer_groups[layer_name] = group
            
    def toggle_layer(self, layer_name, visible):
        if layer_name in self.layer_groups:
            self.layer_groups[layer_name].setVisible(visible)

    def draw_lots(self, lots_data):
        self.scene.clear()
        self.lot_items.clear()
        self.text_items.clear()
        self.layer_groups.clear()
        self.preview_box_5000 = None
        self.preview_box_500 = None
        
        default_pen = QPen(QColor("#333333"))
        default_pen.setWidth(0) # Cosmetic pen
        
        default_brush = QBrush(QColor(0, 0, 0, 1)) # Almost transparent brush for interior hit testing
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
                ilot_item.setZValue(2)
                self.scene.addItem(ilot_item)
                self.text_items.append(ilot_item)
                
            for lot_name, lot_info in ilot_data.get('lots', {}).items():
                polygon = lot_info['geom']
                
                qpoly = QPolygonF()
                for x, y in polygon.exterior.coords:
                    qpoly.append(QPointF(x, -y))
                    
                item = QGraphicsPolygonItem(qpoly)
                item.setPen(default_pen)
                item.setBrush(default_brush)
                item.setFlag(QGraphicsItem.ItemIsSelectable)
                
                item.setData(0, ilot_name)
                item.setData(1, lot_name)
                item.setData(2, polygon)
                
                self.scene.addItem(item)
                self.lot_items[(ilot_name, lot_name)] = item
                
                text_item = QGraphicsTextItem(lot_name)
                text_item.setFont(font)
                text_item.setDefaultTextColor(QColor("#666666"))
                centroid = polygon.centroid
                text_rect = text_item.boundingRect()
                text_item.setPos(centroid.x - text_rect.width() / 2, -centroid.y - text_rect.height() / 2)
                text_item.setZValue(1)
                self.scene.addItem(text_item)
                self.text_items.append(text_item)
                
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def zoom_to_selection(self):
        selected_items = self.scene.selectedItems()
        if not selected_items:
            if self.scene.sceneRect().isValid() and self.scene.sceneRect().width() > 0:
                self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            return
            
        bounding_rect = QRectF()
        for item in selected_items:
            if bounding_rect.isNull():
                bounding_rect = item.sceneBoundingRect()
            else:
                bounding_rect = bounding_rect.united(item.sceneBoundingRect())
                
        margin_x = bounding_rect.width() * 0.1
        margin_y = bounding_rect.height() * 0.1
        if margin_x == 0: margin_x = 10
        if margin_y == 0: margin_y = 10
        
        bounding_rect.adjust(-margin_x, -margin_y, margin_x, margin_y)
        self.fitInView(bounding_rect, Qt.KeepAspectRatio)

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
                    item.setBrush(QBrush(QColor(0, 0, 0, 1)))
        self.selection_changed.emit(selected_lots)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(scene_pos.x(), -scene_pos.y())
        
        if not self._is_panning and (event.buttons() & Qt.LeftButton) and hasattr(self, '_click_start_pos') and self._click_start_pos:
            if (event.pos() - self._click_start_pos).manhattanLength() > 5:
                self._is_panning = True
                self.setCursor(Qt.ClosedHandCursor)

        if self._is_panning and self._last_pan_point:
            delta = self.mapToScene(self._last_pan_point) - self.mapToScene(event.pos())
            self._last_pan_point = event.pos()
            self.setSceneRect(self.sceneRect().translated(delta.x(), delta.y()))
            self.translate(delta.x(), delta.y())
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(int(h_bar.value() + delta.x()))
            v_bar.setValue(int(v_bar.value() + delta.y()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_start_pos = event.pos()
            self._last_pan_point = event.pos()
            self._is_panning = False
            return
        elif event.button() == Qt.MiddleButton:
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
            return

        if event.button() == Qt.LeftButton and hasattr(self, '_click_start_pos') and self._click_start_pos is not None:
            click_dist = (event.pos() - self._click_start_pos).manhattanLength()
            self._click_start_pos = None
            
            if self._is_panning:
                self._is_panning = False
                self._last_pan_point = None
                self.setCursor(Qt.ArrowCursor)
                return
                
            if click_dist <= 5:
                scene_pos = self.mapToScene(event.pos())
                click_point = Point(scene_pos.x(), -scene_pos.y())
                
                # Trouve tous les lots contenant le point cliqué
                candidates = []
                for (ilot_name, lot_name), item in self.lot_items.items():
                    poly = item.data(2)
                    if poly:
                        if poly.contains(click_point):
                            candidates.append((poly.area, item))
                        elif poly.distance(click_point) < 0.2:
                            candidates.append((poly.area + 1000000.0, item))
                
                # Trie par surface croissante : le plus petit polygone correspond au lot individuel précis !
                clicked_item = None
                if candidates:
                    candidates.sort(key=lambda x: x[0])
                    clicked_item = candidates[0][1]
                
                modifiers = event.modifiers()
                is_multi = bool(modifiers & (Qt.ControlModifier | Qt.ShiftModifier))
                
                self.scene.blockSignals(True)
                if clicked_item:
                    if not is_multi:
                        for it in self.lot_items.values():
                            it.setSelected(False)
                        clicked_item.setSelected(True)
                    else:
                        clicked_item.setSelected(not clicked_item.isSelected())
                else:
                    if not is_multi:
                        for it in self.lot_items.values():
                            it.setSelected(False)
                self.scene.blockSignals(False)
                
                self.on_selection_changed()
                return

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

