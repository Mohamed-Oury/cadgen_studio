import os
import sys
import unittest
from shapely.geometry import Polygon

# Ajouter le dossier parent au path pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.geometry import calculate_area, calculate_distance, calculate_gisement
from core.dxf_parser import DXFParser
from core.dxf_exporter import DXFExporter

class TestCadGenStudio(unittest.TestCase):
    
    def test_geometry_calculations(self):
        # Un carré de 10x10
        points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        poly = Polygon(points)
        
        # Test Surface
        area = calculate_area(poly)
        self.assertEqual(area, 100.0)
        
        # Test Distance
        dist = calculate_distance((0,0), (3,4))
        self.assertEqual(dist, 5.0)
        
        # Test Gisement
        g = calculate_gisement((0,0), (10,10))
        # dx=10, dy=10 => angle = pi/4 => 50 grades
        self.assertAlmostEqual(g, 50.0)
        
    def test_dxf_parser(self):
        # Vérifier que le parser ne crashe pas à l'init
        parser = DXFParser("dummy.dxf")
        self.assertIsNotNone(parser)
        
if __name__ == '__main__':
    print("Démarrage de l'outil de Test QA automatisé...")
    unittest.main()
