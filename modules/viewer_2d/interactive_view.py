import math
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsPolygonItem
# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF, QBrush
# pyrefly: ignore [missing-import]
import ezdxf
# pyrefly: ignore [missing-import]
from ezdxf.addons.drawing import Frontend, RenderContext, config
# pyrefly: ignore [missing-import]
from ezdxf.addons.drawing.pyqt import PyQtBackend
# pyrefly: ignore [missing-import]
from shapely.geometry import Point, Polygon

class InteractiveDXFView(QGraphicsView):
    # Signals to communicate with the widget
    distance_measured = Signal(float)
    lot_info_found = Signal(str, float, str, str) # title, area, lot_name, ilot_name
    lot_coords_found = Signal(str, list) # nom, liste de (X, Y)
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Enable antialiasing
        self.setRenderHint(QPainter.Antialiasing)
        
        # Invert Y axis because Qt's Y axis points down, while DXF's points up
        self.scale(1, -1)
        
        # View settings for navigation
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid background for better visibility
        self.setBackgroundBrush(QBrush(QColor("#F5F6FA"))) # Light gray/white background
        
        # Modes: "nav", "distance", "area", "coords", "info"
        self.current_mode = "nav"
        
        # State for distance measurement
        self.measure_points = []
        self.measure_line = None
        
        # State for lot parsing
        self.dxf_parser = None
        self.highlighted_poly = None
        self.thematic_polys = []
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
        self.thematic_polys = []
        self.dxf_parser = dxf_parser
        self._last_view_rect = None
        self._is_loaded = False
        
        try:
            self.doc = ezdxf.readfile(filepath)
            self._render_scene()
            return True, "Fichier chargé avec succès."
        except Exception as e:
            return False, str(e)
            
    def get_layers(self):
        """Returns a list of layer names in the loaded DXF"""
        if hasattr(self, 'doc') and self.doc:
            return [layer.dxf.name for layer in self.doc.layers]
        return []
        
    def _render_scene(self, visible_layers=None):
        if not hasattr(self, 'doc') or not self.doc:
            return
            
        # Save current transform if we are just updating layers
        current_transform = self.transform()
        is_first_load = not getattr(self, '_is_loaded', False)
        
        self.scene.clear()
        self.thematic_polys = []
        
        msp = self.doc.modelspace()
        
        # Setup ezdxf render context and backend
        ctx = RenderContext(self.doc)
        
        # Configuration: set background to light gray
        cfg = config.Configuration(
            background_policy=config.BackgroundPolicy.CUSTOM,
            custom_bg_color="#F5F6FA",
            color_policy=config.ColorPolicy.COLOR,
        )
        
        out = PyQtBackend(self.scene)
        
        if visible_layers is not None:
            entities = [e for e in msp if e.dxf.layer in visible_layers]
            Frontend(ctx, out, config=cfg).draw_entities(entities)
        else:
            Frontend(ctx, out, config=cfg).draw_layout(msp)
        
        if not is_first_load:
            # Restore view transform
            self.setTransform(current_transform)
            return

        # Use itemsBoundingRect for the full scene size
        full_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(full_rect)
        
        # Determine the best view rect to zoom to
        view_rect = None
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
        
        # Check if we parsed any lots
        if self.dxf_parser and hasattr(self.dxf_parser, 'ilots') and self.dxf_parser.ilots:
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
                view_rect = QRectF(QPointF(min_x, min_y), QPointF(max_x, max_y))
                
        if not view_rect:
            # Fallback: robustly calculate bounding box from scene items
            # Filter out outliers (e.g. origin points at 0,0)
            items = self.scene.items()
            valid_rects = []
            
            for item in items:
                rect = item.sceneBoundingRect()
                # Ignore empty rects or excessively large background items
                if rect.width() > 0 and rect.height() > 0 and rect.width() < 1000000:
                    valid_rects.append(rect)
                    
            if valid_rects:
                # Find the center of mass of all rects
                centers_x = [r.center().x() for r in valid_rects]
                centers_y = [r.center().y() for r in valid_rects]
                centers_x.sort()
                centers_y.sort()
                
                # Use median as a robust center
                median_x = centers_x[len(centers_x)//2]
                median_y = centers_y[len(centers_y)//2]
                
                # Keep rects that are within a reasonable distance from the median
                # e.g. within 200,000 units (to allow large cities but exclude (0,0) if we are at 500,000)
                for rect in valid_rects:
                    cx = rect.center().x()
                    cy = rect.center().y()
                    
                    if abs(cx - median_x) < 200000 and abs(cy - median_y) < 200000:
                        min_x = min(min_x, rect.left())
                        min_y = min(min_y, rect.top())
                        max_x = max(max_x, rect.right())
                        max_y = max(max_y, rect.bottom())
                        
            if min_x != float('inf'):
                view_rect = QRectF(QPointF(min_x, min_y), QPointF(max_x, max_y))
            else:
                view_rect = full_rect

        # Add a 5% margin to the final view_rect
        margin_x = max(view_rect.width() * 0.05, 10)
        margin_y = max(view_rect.height() * 0.05, 10)
        view_rect.adjust(-margin_x, -margin_y, margin_x, margin_y)
            
        self._last_view_rect = view_rect
        self._is_loaded = True
        
        # Use QTimer to ensure the layout has updated before fitting in view
        QTimer.singleShot(100, lambda: self.fitInView(view_rect, Qt.KeepAspectRatio))

    def apply_theme(self, theme_mode, attributes_db):
        # Clear existing thematic polys
        for item in self.thematic_polys:
            self.scene.removeItem(item)
        self.thematic_polys.clear()

        if theme_mode == "Aucun" or not hasattr(self, 'doc') or not self.doc:
            return

        polygons_to_theme = []

        if self.dxf_parser and hasattr(self.dxf_parser, 'ilots') and self.dxf_parser.ilots:
            for ilot_name, ilot_data in self.dxf_parser.ilots.items():
                for lot_name, lot_data in ilot_data["lots"].items():
                    polygons_to_theme.append((ilot_name, lot_name, lot_data["geom"]))
        else:
            # Fallback
            msp = self.doc.modelspace()
            for entity in msp:
                if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                    points = []
                    for p in entity.vertices():
                        if hasattr(p, 'dxf'):
                            points.append((p.dxf.location.x, p.dxf.location.y))
                        else:
                            points.append((p[0], p[1]))
                    if len(points) >= 3:
                        try:
                            poly = Polygon(points)
                            if poly.is_valid and poly.area > 0:
                                cx, cy = int(poly.centroid.x), int(poly.centroid.y)
                                polygons_to_theme.append((entity.dxf.layer, f"Poly_{cx}_{cy}", poly))
                        except Exception:
                            pass

        for ilot_name, lot_name, poly in polygons_to_theme:
            lot_id = f"{ilot_name}|{lot_name}"
            data = attributes_db.get(lot_id, {})
            
            color = None
            if theme_mode == "Par Surface":
                area = data.get("surface", poly.area)
                if area < 300:
                    color = QColor(231, 76, 60, 150) # Red
                elif area <= 500:
                    color = QColor(241, 196, 15, 150) # Yellow
                else:
                    color = QColor(46, 204, 113, 150) # Green
            elif theme_mode == "Par Statut":
                statut = data.get("statut", "Disponible")
                if statut == "Disponible":
                    color = QColor(46, 204, 113, 150) # Green
                elif statut == "Réservé":
                    color = QColor(243, 156, 18, 150) # Orange
                elif statut == "Vendu":
                    color = QColor(231, 76, 60, 150) # Red
            
            if color:
                coords = list(poly.exterior.coords)
                qpoly = QPolygonF()
                for coord in coords:
                    qpoly.append(QPointF(coord[0], coord[1]))
                
                item = self.scene.addPolygon(qpoly, QPen(Qt.NoPen), QBrush(color))
                self.thematic_polys.append(item)

    def zoom_extents(self):
        if self._last_view_rect:
            self.fitInView(self._last_view_rect, Qt.KeepAspectRatio)
        elif self.scene.items():
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def zoom_in(self):
        self.scale(1.2, 1.2)

    def zoom_out(self):
        self.scale(1 / 1.2, 1 / 1.2)

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
        elif mode in ("area", "coords", "info"):
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
            elif self.current_mode in ["area", "info"]:
                self.handle_area_click(scene_pos)
            elif self.current_mode == "coords":
                self.handle_coords_click(scene_pos)
                
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
        dxf_x = scene_pos.x()
        dxf_y = scene_pos.y()
        click_point = Point(dxf_x, dxf_y)
        
        found_lot = None
        found_ilot = None
        found_geom = None
        
        if self.dxf_parser and hasattr(self.dxf_parser, 'ilots'):
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
                    
        # Fallback : chercher n'importe quel polygone fermé dans le DXF
        closest_poly = None
        min_dist_to_poly = float('inf')
        
        if not found_geom and hasattr(self, 'doc') and self.doc:
            msp = self.doc.modelspace()
            # Chercher le plus petit polygone contenant le point
            min_area = float('inf')
            
            for entity in msp:
                if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                    points = []
                    if entity.dxftype() == 'LWPOLYLINE':
                        for p in entity: # LWPOLYLINE yields (x, y, start_width, end_width, bulge)
                            points.append((p[0], p[1]))
                    else:
                        for p in entity.vertices():
                            if hasattr(p, 'dxf'):
                                points.append((p.dxf.location.x, p.dxf.location.y))
                            else:
                                points.append((p[0], p[1]))
                            
                    if len(points) >= 3:
                        try:
                            poly = Polygon(points)
                            if not poly.is_valid:
                                poly = poly.buffer(0)
                            if poly.is_valid and poly.area > 0:
                                if poly.contains(click_point):
                                    if poly.area < min_area:
                                        min_area = poly.area
                                        found_geom = poly
                                        found_lot = "Polygone Inconnu"
                                        found_ilot = entity.dxf.layer
                                else:
                                    # Calculate distance to boundary for debugging
                                    dist = poly.distance(click_point)
                                    if dist < min_dist_to_poly:
                                        min_dist_to_poly = dist
                                        closest_poly = poly
                        except Exception:
                            pass
                            
        if found_lot and found_geom:
            area = found_geom.area
            title = f"Calque: {found_ilot} | Lot: {found_lot}"
            self.lot_info_found.emit(title, area, found_lot, found_ilot)
            
            # Highlight the polygon
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                
            coords = list(found_geom.exterior.coords)
            qpoly = QPolygonF()
            for coord in coords:
                qpoly.append(QPointF(coord[0], coord[1]))
                
            self.highlighted_poly = QGraphicsPolygonItem(qpoly)
            
            pen = QPen(QColor("#2ECC71")) # Green
            pen.setWidth(3)
            pen.setCosmetic(True)
            self.highlighted_poly.setPen(pen)
            
            brush = QBrush(QColor(46, 204, 113, 100)) # Transparent green
            self.highlighted_poly.setBrush(brush)
            
            self.scene.addItem(self.highlighted_poly)
        else:
            if min_dist_to_poly != float('inf'):
                msg = f"Aucun lot à cet emplacement. (Polygone le plus proche à {min_dist_to_poly:.2f} unités, point cliqué: {dxf_x:.2f}, {dxf_y:.2f})"
            else:
                msg = f"Aucun lot trouvé. (Aucun polygone détecté dans le fichier, point cliqué: {dxf_x:.2f}, {dxf_y:.2f})"
            self.lot_info_found.emit(msg, 0.0, "", "")
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                self.highlighted_poly = None

    def handle_coords_click(self, scene_pos):
        dxf_x = scene_pos.x()
        dxf_y = scene_pos.y()
        click_point = Point(dxf_x, dxf_y)
        
        found_lot = None
        found_ilot = None
        found_geom = None
        
        if self.dxf_parser and hasattr(self.dxf_parser, 'ilots'):
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
                    
        # Fallback : chercher n'importe quel polygone fermé dans le DXF
        if not found_geom and hasattr(self, 'doc') and self.doc:
            msp = self.doc.modelspace()
            # Chercher le plus petit polygone contenant le point
            min_area = float('inf')
            
            for entity in msp:
                if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                    points = []
                    for p in entity.vertices():
                        if hasattr(p, 'dxf'):
                            points.append((p.dxf.location.x, p.dxf.location.y))
                        else:
                            points.append((p[0], p[1]))
                            
                    if len(points) >= 3:
                        try:
                            poly = Polygon(points)
                            if poly.is_valid and poly.area > 0 and poly.contains(click_point):
                                if poly.area < min_area:
                                    min_area = poly.area
                                    found_geom = poly
                                    found_lot = "Polygone Inconnu"
                                    found_ilot = entity.dxf.layer
                        except Exception:
                            pass
                
        if found_geom:
            coords = list(found_geom.exterior.coords)
            title = f"Calque: {found_ilot} | Lot: {found_lot}"
            self.lot_coords_found.emit(title, coords)
            
            # Highlight the polygon
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                
            qpoly = QPolygonF()
            for coord in coords:
                qpoly.append(QPointF(coord[0], coord[1]))
                
            self.highlighted_poly = QGraphicsPolygonItem(qpoly)
            
            pen = QPen(QColor("#3498DB")) # Blue
            pen.setWidth(3)
            pen.setCosmetic(True)
            self.highlighted_poly.setPen(pen)
            
            brush = QBrush(QColor(52, 152, 219, 100)) # Transparent blue
            self.highlighted_poly.setBrush(brush)
            self.scene.addItem(self.highlighted_poly)
        else:
            self.lot_coords_found.emit("", [])
            if self.highlighted_poly:
                self.scene.removeItem(self.highlighted_poly)
                self.highlighted_poly = None

    def search_and_zoom(self, query):
        if not hasattr(self, 'doc') or not self.doc:
            return False
            
        query = query.lower()
        msp = self.doc.modelspace()
        
        found_entity = None
        for entity in msp:
            if entity.dxftype() in ('TEXT', 'MTEXT'):
                text = entity.dxf.text.lower()
                if query in text:
                    found_entity = entity
                    break
                    
        if not found_entity:
            return False
            
        # Get coordinates to zoom to
        # pyrefly: ignore [missing-import]
        from ezdxf import bbox
        ext = bbox.extents([found_entity])
        if not ext.has_data:
            return False
            
        center_x = (ext.extmin.x + ext.extmax.x) / 2
        center_y = (ext.extmin.y + ext.extmax.y) / 2
        scene_y = -center_y
        
        if self.highlighted_poly:
            self.scene.removeItem(self.highlighted_poly)
            self.highlighted_poly = None
            
        margin = max(5, (ext.extmax.x - ext.extmin.x) * 1.5)
        # Y is inverted in our scene, so the top-left of the rect is (min.x, -max.y)
        rect_x = ext.extmin.x - margin
        rect_y = -ext.extmax.y - margin
        rect_w = (ext.extmax.x - ext.extmin.x) + 2*margin
        rect_h = (ext.extmax.y - ext.extmin.y) + 2*margin
        
        # pyrefly: ignore [missing-import]
        from PySide6.QtWidgets import QGraphicsRectItem
        self.highlighted_poly = QGraphicsRectItem(rect_x, rect_y, rect_w, rect_h)
        pen = QPen(QColor("#E74C3C")) # Red
        pen.setWidth(3)
        pen.setCosmetic(True)
        self.highlighted_poly.setPen(pen)
        
        brush = QBrush(QColor(231, 76, 60, 50))
        self.highlighted_poly.setBrush(brush)
        self.scene.addItem(self.highlighted_poly)
        
        # Center view
        self.centerOn(center_x, scene_y)
        
        # Adjust zoom if we are zoomed out too much
        current_scale = self.transform().m11()
        if current_scale < 0.5:
            self.resetTransform()
            self.scale(1, -1)
            self.scale(2, 2)
            self.centerOn(center_x, scene_y)
            
        return True
