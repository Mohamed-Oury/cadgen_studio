import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsPolygonItem
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF, QBrush
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext, config
from ezdxf.addons.drawing.pyqt import PyQtBackend
from shapely.geometry import Point, Polygon

class InteractiveDXFView(QGraphicsView):
    # Signals to communicate with the widget
    distance_measured = Signal(float)
    lot_info_found = Signal(str, float) # nom, surface
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Enable antialiasing
        self.setRenderHint(QPainter.Antialiasing)
        
        # View settings for navigation
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Black background for debugging
        self.setBackgroundBrush(QBrush(QColor("black")))
        
        # Modes: "nav", "distance", "area"
        self.current_mode = "nav"
        
        # State for distance measurement
        self.measure_points = []
        self.measure_line = None
        
        # State for lot parsing
        self.dxf_parser = None
        self.highlighted_poly = None
        self._last_view_rect = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._last_view_rect:
            self.fitInView(self._last_view_rect, Qt.KeepAspectRatio)
            self._last_view_rect = None

    def load_dxf(self, filepath, dxf_parser=None):
        self.scene.clear()
        self.measure_points = []
        self.measure_line = None
        self.highlighted_poly = None
        self.dxf_parser = dxf_parser
        self._last_view_rect = None
        
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()
            
            # Setup ezdxf render context and backend
            ctx = RenderContext(doc)
            
            # Configuration: set background to black for debugging
            cfg = config.Configuration(
                background_policy=config.BackgroundPolicy.CUSTOM,
                custom_bg_color="#000000",
                color_policy=config.ColorPolicy.COLOR,
            )
            
            out = PyQtBackend(self.scene)
            Frontend(ctx, out, config=cfg).draw_layout(msp)
            
            # Use itemsBoundingRect for the full scene size
            full_rect = self.scene.itemsBoundingRect()
            self.scene.setSceneRect(full_rect)
            
            # Determine the best view rect to zoom to
            view_rect = None
            if self.dxf_parser and hasattr(self.dxf_parser, 'ilots') and self.dxf_parser.ilots:
                min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
                for ilot in self.dxf_parser.ilots.values():
                    for lot in ilot.get('lots', {}).values():
                        poly = lot.get('geom')
                        if poly:
                            bounds = poly.bounds # (minx, miny, maxx, maxy)
                            min_x = min(min_x, bounds[0])
                            min_y = min(min_y, bounds[1])
                            max_x = max(max_x, bounds[2])
                            max_y = max(max_y, bounds[3])
                
                if min_x != float('inf'):
                    # ezdxf PyQtBackend flips Y axis (Scene y = - DXF y)
                    view_rect = QRectF(QPointF(min_x, -max_y), QPointF(max_x, -min_y))
            
            # If no lots found, compute custom bounding box ignoring outliers
            if not view_rect:
                min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
                from ezdxf import bbox
                
                boxes = []
                for entity in msp:
                    ext = bbox.extents([entity])
                    if ext.has_data:
                        boxes.append(ext)
                
                if boxes:
                    # Find the median center of all elements
                    centers_x = [(ext.extmin.x + ext.extmax.x)/2 for ext in boxes]
                    centers_y = [(ext.extmin.y + ext.extmax.y)/2 for ext in boxes]
                    centers_x.sort()
                    centers_y.sort()
                    median_x = centers_x[len(centers_x)//2]
                    median_y = centers_y[len(centers_y)//2]

                    # Only keep elements whose center is within 50km of the median center
                    # This safely ignores any stray lines drawn to (0,0) or points at infinity
                    for ext in boxes:
                        cx = (ext.extmin.x + ext.extmax.x)/2
                        cy = (ext.extmin.y + ext.extmax.y)/2
                        if abs(cx - median_x) < 50000 and abs(cy - median_y) < 50000:
                            min_x = min(min_x, ext.extmin.x)
                            min_y = min(min_y, ext.extmin.y)
                            max_x = max(max_x, ext.extmax.x)
                            max_y = max(max_y, ext.extmax.y)

                if min_x != float('inf'):
                    view_rect = QRectF(QPointF(min_x, -max_y), QPointF(max_x, -min_y))
                else:
                    view_rect = full_rect

            # Add a 5% margin to the final view_rect
            margin_x = max(view_rect.width() * 0.05, 10)
            margin_y = max(view_rect.height() * 0.05, 10)
            view_rect.adjust(-margin_x, -margin_y, margin_x, margin_y)
                
            self._last_view_rect = view_rect
            
            # Use QTimer to ensure the layout has updated before fitting in view
            QTimer.singleShot(100, lambda: self.fitInView(view_rect, Qt.KeepAspectRatio))
            
            return True, "Fichier chargé avec succès."
        except Exception as e:
            return False, str(e)
    def zoom_extents(self):
        if self._last_view_rect:
            self.fitInView(self._last_view_rect, Qt.KeepAspectRatio)
        elif self.scene.items():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def set_mode(self, mode):
        self.current_mode = mode
        self.measure_points = []
        if self.measure_line:
            self.scene.removeItem(self.measure_line)
            self.measure_line = None
            
        if self.highlighted_poly:
            self.scene.removeItem(self.highlighted_poly)
            self.highlighted_poly = None

        if mode == "nav":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif mode == "distance":
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == "area":
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.PointingHandCursor)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            
            if self.current_mode == "distance":
                self.handle_distance_click(scene_pos)
            elif self.current_mode == "area":
                self.handle_area_click(scene_pos)
                
        super().mousePressEvent(event)
        
    def handle_distance_click(self, scene_pos):
        self.measure_points.append(scene_pos)
        
        if len(self.measure_points) == 1:
            # First click
            if self.measure_line:
                self.scene.removeItem(self.measure_line)
            # Create a point/small circle maybe, but for now just wait for 2nd point
            self.measure_line = QGraphicsLineItem(scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y())
            pen = QPen(QColor("red"))
            pen.setWidth(2)
            # We want cosmetic pen so width doesn't scale with zoom
            pen.setCosmetic(True) 
            self.measure_line.setPen(pen)
            self.scene.addItem(self.measure_line)
            
        elif len(self.measure_points) == 2:
            # Second click
            p1 = self.measure_points[0]
            p2 = self.measure_points[1]
            self.measure_line.setLine(p1.x(), p1.y(), p2.x(), p2.y())
            
            # Calculate distance
            # NOTE: ezdxf PyQtBackend flips Y axis (y = -y). So dx and dy are same magnitude.
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            distance = math.sqrt(dx*dx + dy*dy)
            
            self.distance_measured.emit(distance)
            self.measure_points = [] # Reset for next measurement

    def mouseMoveEvent(self, event):
        # Update measure line interactively
        if self.current_mode == "distance" and len(self.measure_points) == 1 and self.measure_line:
            scene_pos = self.mapToScene(event.pos())
            p1 = self.measure_points[0]
            self.measure_line.setLine(p1.x(), p1.y(), scene_pos.x(), scene_pos.y())
            
        super().mouseMoveEvent(event)

    def handle_area_click(self, scene_pos):
        if not self.dxf_parser:
            return
            
        # ezdxf PyQtBackend maps DXF (x,y) to Scene (x, -y).
        # So Scene (x, y) maps to DXF (x, -y).
        dxf_x = scene_pos.x()
        dxf_y = -scene_pos.y()
        click_point = Point(dxf_x, dxf_y)
        
        found_lot = None
        found_ilot = None
        found_geom = None
        
        # Search in the parsed ilots/lots
        for ilot_name, ilot_data in self.dxf_parser.ilots.items():
            for lot_name, lot_data in ilot_data["lots"].items():
                poly = lot_data["geom"]
                if poly.contains(click_point):
                    found_lot = lot_name
                    found_ilot = ilot_name
                    found_geom = poly
                    break
            if found_lot:
                break
                
        if found_lot and found_geom:
            area = found_geom.area
            self.lot_info_found.emit(f"Îlot: {found_ilot} | Lot: {found_lot}", area)
            
            # Highlight the polygon
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                
            qpoly = QPolygonF()
            # Convert Shapely exterior coords to QPointF (remembering to invert Y)
            for coord in found_geom.exterior.coords:
                qpoly.append(QPointF(coord[0], -coord[1]))
                
            self.highlighted_poly = QGraphicsPolygonItem(qpoly)
            
            pen = QPen(QColor("#2ECC71")) # Emerald Green
            pen.setWidth(3)
            pen.setCosmetic(True)
            self.highlighted_poly.setPen(pen)
            
            brush = QBrush(QColor(46, 204, 113, 100)) # Transparent green
            self.highlighted_poly.setBrush(brush)
            
            self.scene.addItem(self.highlighted_poly)
        else:
            self.lot_info_found.emit("Aucun lot trouvé à cet emplacement", 0.0)
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                self.highlighted_poly = None
