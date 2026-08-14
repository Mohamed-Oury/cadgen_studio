import math
from shapely.geometry import Polygon

def calculate_area(polygon: Polygon) -> float:
    """Calcule la surface d'un polygone en mètres carrés."""
    return polygon.area

def calculate_distance(p1, p2):
    """Calcule la distance entre deux points (x1, y1) et (x2, y2)."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def calculate_gisement(p1, p2):
    """
    Calcule le gisement (en grades) entre deux points p1(X1, Y1) et p2(X2, Y2).
    Le gisement est l'angle compté dans le sens des aiguilles d'une montre 
    à partir du Nord de la projection (axe Y).
    1 cercle complet = 400 grades.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    
    if dy == 0:
        if dx > 0:
            return 100.0
        elif dx < 0:
            return 300.0
        else:
            return 0.0
            
    angle_rad = math.atan2(dx, dy)
    angle_grad = angle_rad * (200.0 / math.pi)
    
    if angle_grad < 0:
        angle_grad += 400.0
        
    return angle_grad
