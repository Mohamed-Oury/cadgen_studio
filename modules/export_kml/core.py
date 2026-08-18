 # pyrefly: ignore [missing-import]
import ezdxf
# pyrefly: ignore [missing-import]
import simplekml
# pyrefly: ignore [missing-import]
from pyproj import Transformer
import os

class KMLExporter:
    def __init__(self, dxf_filepath, epsg_source):
        """
        epsg_source: str or int, e.g. "EPSG:32630"
        """
        self.dxf_filepath = dxf_filepath
        self.epsg_source = str(epsg_source)
        if not self.epsg_source.upper().startswith("EPSG:"):
            self.epsg_source = f"EPSG:{self.epsg_source}"
        
        # Google Earth uses EPSG:4326 (WGS84, Longitude/Latitude)
        self.transformer = Transformer.from_crs(self.epsg_source, "EPSG:4326", always_xy=True)
        
    def export(self, output_filepath):
        try:
            doc = ezdxf.readfile(self.dxf_filepath)
            msp = doc.modelspace()
        except Exception as e:
            return False, f"Erreur lors de la lecture du fichier DXF: {str(e)}"
            
        kml = simplekml.Kml(name=os.path.basename(self.dxf_filepath))
        
        # Group features by layer using KML folders
        folders = {}
        
        polygon_count = 0
        text_count = 0
        
        for entity in msp:
            layer = entity.dxf.layer
            
            if layer not in folders:
                folders[layer] = kml.newfolder(name=layer)
            
            folder = folders[layer]
            
            # Export Polygons/Lines
            if entity.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                points = []
                for p in entity.vertices():
                    # get X, Y
                    x = p.dxf.location.x if hasattr(p, 'dxf') else p[0]
                    y = p.dxf.location.y if hasattr(p, 'dxf') else p[1]
                    
                    # Reproject
                    lon, lat = self.transformer.transform(x, y)
                    points.append((lon, lat))
                
                if len(points) >= 2:
                    # Check if closed
                    is_closed = False
                    if entity.dxftype() == 'LWPOLYLINE':
                        is_closed = entity.closed
                    elif entity.dxftype() == 'POLYLINE':
                        is_closed = entity.is_closed
                        
                    if is_closed and len(points) >= 3 and points[0] != points[-1]:
                        points.append(points[0]) # Close the loop for KML
                        
                    if is_closed:
                        pol = folder.newpolygon(name=layer)
                        pol.outerboundaryis = points
                        pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.white)
                        pol.style.linestyle.color = simplekml.Color.red
                        pol.style.linestyle.width = 2
                        polygon_count += 1
                    else:
                        lin = folder.newlinestring(name=layer)
                        lin.coords = points
                        lin.style.linestyle.color = simplekml.Color.blue
                        lin.style.linestyle.width = 2
            
            # Export Text
            elif entity.dxftype() in ('TEXT', 'MTEXT'):
                if hasattr(entity.dxf, 'insert'):
                    x = entity.dxf.insert.x
                    y = entity.dxf.insert.y
                    lon, lat = self.transformer.transform(x, y)
                    text = entity.dxf.text
                    # MTEXT specific text extraction can be more complex, but simple attribute often works
                    if entity.dxftype() == 'MTEXT':
                        text = entity.text
                    
                    pnt = folder.newpoint(name=text, coords=[(lon, lat)])
                    pnt.style.iconstyle.icon.href = "" # Hide the default yellow pushpin
                    pnt.style.labelstyle.scale = 1.2
                    pnt.style.labelstyle.color = simplekml.Color.black
                    text_count += 1

        try:
            kml.save(output_filepath)
            return True, f"Fichier KML généré avec succès !\\n{polygon_count} polygones/lignes et {text_count} textes exportés."
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde du fichier KML: {str(e)}"
