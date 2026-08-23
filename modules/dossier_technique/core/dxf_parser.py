# pyrefly: ignore [missing-import]
import ezdxf
from shapely.geometry import Polygon, Point

class DXFParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.doc = None
        self.msp = None
        self.ilots = {}  # {ilot_name: {'geom': Polygon, 'lots': {lot_name: {'geom': Polygon, 'bornes': [points]}}}}
        
    def load(self):
        try:
            self.doc = ezdxf.readfile(self.filepath)
            self.msp = self.doc.modelspace()
            return True, "Fichier chargé avec succès."
        except IOError:
            return False, f"Impossible de lire le fichier {self.filepath}."
        except ezdxf.DXFStructureError:
            return False, f"Fichier DXF invalide ou corrompu: {self.filepath}."
            
    def get_layer_entities(self, layer_name):
        if not self.msp:
            return []
        return [e for e in self.msp.query(f'*[layer=="{layer_name}"]')]

    def extract_lots_and_ilots(self):
        """
        Extrait les géométries des lots et les associe aux 
        textes (NOMLOT, NOMILOT) via des tests d'inclusion spatiale.
        """
        self.ilots = {}
        
        lots_entities = []
        ilot_texts = []
        lot_texts = []
        
        # 0. Collecte flexible des entités basée sur des mots clés
        for e in self.msp:
            try:
                layer = e.dxf.layer.upper()
            except Exception:
                continue
                
            if e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                if layer == 'L' or 'LOT' in layer or 'PARCEL' in layer:
                    lots_entities.append(e)
            elif e.dxftype() in ('TEXT', 'MTEXT'):
                if 'ILOT' in layer:
                    ilot_texts.append(e)
                elif 'LOT' in layer or 'PARCEL' in layer or layer in ['TEXT', 'TEXTE', 'NUM', '0']:
                    if 'ILOT' not in layer:
                        lot_texts.append(e)
        
        # 1. Extraire les points des textes
        ilot_labels = []
        for t in ilot_texts:
            if t.dxftype() in ('TEXT', 'MTEXT'):
                if hasattr(t.dxf, 'insert'):
                    pos = Point(t.dxf.insert.x, t.dxf.insert.y)
                    ilot_labels.append((t.dxf.text, pos))
                    
        lot_labels = []
        for t in lot_texts:
            if t.dxftype() in ('TEXT', 'MTEXT'):
                if hasattr(t.dxf, 'insert'):
                    pos = Point(t.dxf.insert.x, t.dxf.insert.y)
                    lot_labels.append((t.dxf.text, pos))

        # 2. Associer les polygones aux labels
        lot_idx = 1
        for entity in lots_entities:
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
                        if poly.is_valid and poly.area > 0:
                            # Trouver le nom du lot
                            lot_name = f"Lot_{lot_idx}"
                            for text, pos in lot_labels:
                                if poly.contains(pos):
                                    lot_name = text
                                    break
                                    
                            # Trouver le nom de l'ilot en utilisant le centroide du lot
                            # (simplification car on n'extrait pas les polygones ILOT)
                            ilot_name = "Inconnu"
                            centroid = poly.centroid
                            # Chercher le label ILOT le plus proche (heuristique)
                            min_dist = float('inf')
                            for text, pos in ilot_labels:
                                dist = centroid.distance(pos)
                                if dist < min_dist:
                                    min_dist = dist
                                    ilot_name = text
                            
                            # Si on a des polygones ILOT on pourrait faire poly_ilot.contains(poly)
                            
                            if ilot_name not in self.ilots:
                                self.ilots[ilot_name] = {"geom": None, "pos": None, "lots": {}}
                                for txt, p in ilot_labels:
                                    if txt == ilot_name:
                                        self.ilots[ilot_name]["pos"] = (p.x, p.y)
                                        break
                                
                            self.ilots[ilot_name]["lots"][lot_name] = {
                                "geom": poly,
                                "bornes": points
                            }
                            lot_idx += 1
                    except Exception as e:
                        pass
        
        # 3. Extraire les autres calques pour affichage en arrière-plan
        self.background_layers = {}
        
        # Identifier dynamiquement les calques utilisés pour les lots/textes pour ne pas les dessiner en double
        lot_layer_names = set()
        for e in lots_entities + ilot_texts + lot_texts:
            try:
                lot_layer_names.add(e.dxf.layer)
            except Exception:
                pass
                
        for entity in self.msp:
            try:
                layer = entity.dxf.layer
            except Exception:
                # Ignorer les entités personnalisées (comme COVAPLPOINT) qui n'ont pas d'attribut layer
                continue
                
            # Ignorer les calques traités spécifiquement pour les lots
            if layer in lot_layer_names or layer.upper() in ['LOTS', 'LOTS_1', 'LOT', 'NOMLOT', 'NOMILOT']:
                continue
                
            if layer not in self.background_layers:
                self.background_layers[layer] = []
                
            if entity.dxftype() == 'LINE':
                p1 = entity.dxf.start
                p2 = entity.dxf.end
                self.background_layers[layer].append({'type': 'line', 'points': [(p1.x, p1.y), (p2.x, p2.y)]})
            elif entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                points = []
                for p in entity.vertices():
                    if hasattr(p, 'dxf'):
                        points.append((p.dxf.location.x, p.dxf.location.y))
                    else:
                        points.append((p[0], p[1]))
                if len(points) > 1:
                    self.background_layers[layer].append({'type': 'polyline', 'points': points})
        
        # Compter le nombre de lots
        total_lots = sum(len(i["lots"]) for i in self.ilots.values())
        return len(self.ilots), total_lots

    def extract_lot_by_name(self, ilot_name, lot_name):
        # Pour une extraction spécifique d'un lot et de ses bornes
        pass
