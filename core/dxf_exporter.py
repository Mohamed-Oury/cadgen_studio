import ezdxf

class DXFExporter:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir

    def export_lot(self, filename, lot_data):
        """
        Génère un nouveau fichier DXF avec la géométrie du lot.
        lot_data doit contenir: 'geom' (Polygon), 'bornes' (liste de points)
        """
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Création des calques standards
        doc.layers.add('PARCELLE', color=7)
        doc.layers.add('BORNES', color=1)
        doc.layers.add('CARTOUCHE', color=3)
        
        points = lot_data.get('bornes', [])
        
        # Dessiner le polygone du lot (Ligne fermée)
        if points:
            msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'PARCELLE'})
            
            # Dessiner les bornes (cercles ou points)
            for i, p in enumerate(points):
                # Ajouter un texte pour le nom de la borne
                msp.add_text(f"B{i+1}", dxfattribs={'layer': 'BORNES', 'height': 0.5}).set_placement((p[0]+0.5, p[1]+0.5))
                # Ajouter un point
                msp.add_point(p, dxfattribs={'layer': 'BORNES'})
                
        # Sauvegarde
        import os
        output_path = os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
