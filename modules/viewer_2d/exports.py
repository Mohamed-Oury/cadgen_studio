import os
import json
from PySide6.QtWidgets import QMessageBox

def _get_viewer_from_widget(widget):
    p = widget
    while p and not hasattr(p, 'viewer'):
        p = p.parentWidget()
    if p and hasattr(p, 'viewer'):
        return p.viewer
    return None

def export_dxf_enriched(parent_widget, dxf_filepath, attributes_db, save_path):
    """
    Exporte le DXF avec des hachures et du texte basé sur les attributs
    """
    try:
        import ezdxf
        doc = ezdxf.readfile(dxf_filepath)
        msp = doc.modelspace()
        
        # Création des calques d'enrichissement
        if "CADGEN_THEMATIQUE" not in doc.layers:
            doc.layers.add("CADGEN_THEMATIQUE")
        if "CADGEN_TEXTES" not in doc.layers:
            doc.layers.add("CADGEN_TEXTES")
            
        viewer = _get_viewer_from_widget(parent_widget)
        parser = viewer.dxf_parser if viewer else None
            
        lots_to_export = []
        if parser and hasattr(parser, 'ilots') and parser.ilots:
            for ilot_name, ilot in parser.ilots.items():
                for lot_name, lot in ilot.get("lots", {}).items():
                    if "geom" in lot:
                        lots_to_export.append({
                            "ilot_name": ilot_name,
                            "lot_name": lot_name,
                            "geom": lot["geom"],
                            "id": f"{ilot_name}|{lot_name}"
                        })
        else:
            # Fallback for standard polygons
            from shapely.geometry import Polygon
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
                                lots_to_export.append({
                                    "ilot_name": entity.dxf.layer,
                                    "lot_name": f"Poly_{cx}_{cy}",
                                    "geom": poly,
                                    "id": f"{entity.dxf.layer}|Poly_{cx}_{cy}"
                                })
                        except Exception:
                            pass
                            
        for item in lots_to_export:
            lot_id = item["id"]
            poly = item["geom"]
            data = attributes_db.get(lot_id, {})
            statut = data.get("statut", "Disponible")
            
            # Détermination de la couleur (Index ACI)
            if statut == "Disponible":
                color = 3 # Vert
            elif statut == "Réservé":
                color = 2 # Jaune
            elif statut == "Vendu":
                color = 1 # Rouge
            else:
                color = 7 # Blanc/Noir
                
            # Ajout du Solid (Hachure)
            coords = list(poly.exterior.coords)
            hatch = msp.add_hatch(color=color, dxfattribs={"layer": "CADGEN_THEMATIQUE"})
            hatch.paths.add_polyline_path(coords, is_closed=True)
            
            # Ajout du Texte
            cx, cy = poly.centroid.x, poly.centroid.y
            text_lines = [
                f"Lot: {item['lot_name']}",
                f"Statut: {statut}"
            ]
            if data.get("proprietaire"):
                text_lines.append(f"Prop: {data['proprietaire']}")
                
            text_content = "\\P".join(text_lines) # \\P est le saut de ligne MTEXT
            
            # Taille du texte (adaptée à la surface approximative)
            import math
            char_height = max(1.0, math.sqrt(poly.area) / 15.0)
            
            msp.add_mtext(text_content, dxfattribs={
                "layer": "CADGEN_TEXTES",
                "char_height": char_height,
                "insert": (cx, cy),
                "attachment_point": 5 # Milieu centre
            })
            
        doc.saveas(save_path)
        QMessageBox.information(parent_widget, "Succès", f"Export DXF Enrichi réussi. {len(lots_to_export)} lots exportés.")
        
    except Exception as e:
        QMessageBox.critical(parent_widget, "Erreur", f"Erreur lors de l'export DXF : {str(e)}")

def export_web_html(parent_widget, attributes_db, save_path):
    """
    Exporte le lotissement sous forme de carte web interactive HTML (Leaflet)
    """
    try:
        # On va réutiliser la logique d'export GeoJSON existante pour extraire les données
        geojson = {"type": "FeatureCollection", "features": []}
        
        viewer = _get_viewer_from_widget(parent_widget)
        parser = viewer.dxf_parser if viewer else None
            
        features = []
        if parser and hasattr(parser, 'ilots') and parser.ilots:
            for ilot_name, ilot in parser.ilots.items():
                for lot_name, lot in ilot.get("lots", {}).items():
                    poly = lot.get("geom")
                    if poly:
                        lot_id = f"{ilot_name}|{lot_name}"
                        props = {
                            "Ilot": ilot_name,
                            "Lot": lot_name,
                            "Surface": poly.area
                        }
                        db_props = attributes_db.get(lot_id, {})
                        props.update(db_props)
                        
                        # Leaflet with CRS.Simple uses [lat, lng] which corresponds to [y, x]!
                        # BUT L.geoJSON handles geojson properly (which is [lng, lat] = [x, y]).
                        coords = [[list(coord) for coord in list(poly.exterior.coords)]]
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": coords},
                            "properties": props
                        })
                        
        if not features and viewer and viewer.doc:
            from shapely.geometry import Polygon
            msp = viewer.doc.modelspace()
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
                                lot_name = f"Poly_{cx}_{cy}"
                                ilot_name = entity.dxf.layer
                                lot_id = f"{ilot_name}|{lot_name}"
                                
                                props = {
                                    "Layer": ilot_name,
                                    "Surface": poly.area
                                }
                                db_props = attributes_db.get(lot_id, {})
                                props.update(db_props)
                                
                                coords = [[list(coord) for coord in list(poly.exterior.coords)]]
                                features.append({
                                    "type": "Feature",
                                    "geometry": {"type": "Polygon", "coordinates": coords},
                                    "properties": props
                                })
                        except:
                            pass
                            
        geojson["features"] = features
        geojson_str = json.dumps(geojson)
        
        # Génération du HTML
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Carte Interactive - CadGen Studio</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        #map {{ width: 100vw; height: 100vh; background-color: #f8f9fa; }}
        .info-panel {{ padding: 10px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Utilisation de CRS.Simple car les coordonnées DXF ne sont pas forcément en WGS84
        var map = L.map('map', {{
            crs: L.CRS.Simple,
            minZoom: -5
        }});
        
        var geojsonData = {geojson_str};
        
        function getColor(statut) {{
            return statut === 'Vendu' ? '#e74c3c' :
                   statut === 'Réservé' ? '#f39c12' :
                   statut === 'Disponible' ? '#2ecc71' : '#bdc3c7';
        }}
        
        function style(feature) {{
            return {{
                fillColor: getColor(feature.properties.statut || 'Disponible'),
                weight: 2,
                opacity: 1,
                color: 'white',
                dashArray: '3',
                fillOpacity: 0.7
            }};
        }}
        
        function onEachFeature(feature, layer) {{
            var popupContent = '<div class="info-panel">' +
                '<h3>' + (feature.properties.Lot || 'Lot') + '</h3>' +
                '<p><b>Îlot:</b> ' + (feature.properties.Ilot || feature.properties.Layer || 'N/A') + '</p>' +
                '<p><b>Surface:</b> ' + (feature.properties.Surface ? feature.properties.Surface.toFixed(2) + ' m²' : 'N/A') + '</p>' +
                '<p><b>Statut:</b> ' + (feature.properties.statut || 'Disponible') + '</p>' +
                '<p><b>Propriétaire:</b> ' + (feature.properties.proprietaire || 'Non défini') + '</p>' +
                '</div>';
            layer.bindPopup(popupContent);
        }}
        
        // Custom coordinates to CRS.Simple (LatLng(y, x))
        var geojsonLayer = L.geoJSON(geojsonData, {{
            coordsToLatLng: function(coords) {{
                // GeoJSON is [x, y], Leaflet LatLng expects [lat, lng] which maps to [y, x] in CRS.Simple
                return new L.LatLng(coords[1], coords[0]);
            }},
            style: style,
            onEachFeature: onEachFeature
        }}).addTo(map);
        
        map.fitBounds(geojsonLayer.getBounds());
    </script>
</body>
</html>"""

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        QMessageBox.information(parent_widget, "Succès", f"Export Web HTML réussi. {len(features)} éléments intégrés.")
        
    except Exception as e:
        QMessageBox.critical(parent_widget, "Erreur", f"Erreur lors de l'export HTML : {str(e)}")
