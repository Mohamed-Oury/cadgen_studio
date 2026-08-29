# pyrefly: ignore [missing-import]
import ezdxf
# pyrefly: ignore [missing-import]
from ezdxf.enums import TextEntityAlignment
import math
import os

class DXFExporter:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir

    def export_lot(self, filename, lot_data, full_data):
        """
        Génère un nouveau fichier DXF avec le cartouche complet (Espace Objet).
        """
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Calques
        doc.layers.add('CADRE', color=7)
        doc.layers.add('TEXTES', color=7)
        doc.layers.add('PARCELLE', color=1)  # Rouge pour le lot principal
        doc.layers.add('BORNES', color=1)
        doc.layers.add('VOISINS', color=8)   # Gris pour les voisins
        
        points = lot_data.get('bornes', [])
        voisins = full_data.get('voisins', {})
        
        if not points:
            return None
            
        # 1. Calcul de la boîte englobante et du centroïde du lot
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        lot_w = max_x - min_x
        lot_h = max_y - min_y
        
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        
        # 2. Dimensions dynamiques du cadre pour que le lot entre parfaitement
        # La zone de dessin du lot occupe 65% de la largeur du cadre et entre le bas (12%) et le haut (82%) de la hauteur
        draw_w_ratio = 0.60
        draw_h_ratio = 0.65
        
        req_w = (max(lot_w, 25.0) * 1.35) / draw_w_ratio
        req_h = (max(lot_h, 25.0) * 1.35) / draw_h_ratio
        
        # Ratio A4 Landscape (297 / 210 = 1.41428)
        width = max(148.5, req_w, req_h * 1.41428)
        height = width / 1.41428
        
        scale_ratio = height / 105.0
        scale_val = int(round(500 * scale_ratio / 50.0) * 50)
        if scale_val < 100: scale_val = 100
        
        # Position du coin inférieur gauche du cadre (ox, oy)
        # de sorte que le centre de la ZONE DE DESSIN corresponde exactement à (cx, cy)
        ox = cx - (0.325 * width)
        oy = cy - (0.470 * height)
        
        # 3. Dessin du cadre extérieur
        cadre_pts = [(ox, oy), (ox+width, oy), (ox+width, oy+height), (ox, oy+height)]
        msp.add_lwpolyline(cadre_pts, close=True, dxfattribs={'layer': 'CADRE'})
        
        # Ligne de séparation Gauche (65%) / Droite (35%)
        sep_x = ox + (width * 0.65)
        msp.add_line((sep_x, oy), (sep_x, oy+height), dxfattribs={'layer': 'CADRE'})
        
        # Lignes horizontales de séparation pour l'en-tête et le pied de page
        header_line_y = oy + (0.82 * height)
        footer_line_y = oy + (0.12 * height)
        msp.add_line((ox, header_line_y), (sep_x, header_line_y), dxfattribs={'layer': 'CADRE'})
        msp.add_line((ox, footer_line_y), (sep_x, footer_line_y), dxfattribs={'layer': 'CADRE'})
        
        # ==========================================
        # COLONNE GAUCHE (CARTOUCHE ET PLAN)
        # ==========================================
        th = 1.2 * scale_ratio # Text height proportionnel
        
        def add_text(text, x, y, h, align='LEFT'):
            if not text: text = "......"
            align_map = {
                'LEFT': TextEntityAlignment.LEFT,
                'CENTER': TextEntityAlignment.CENTER,
                'RIGHT': TextEntityAlignment.RIGHT
            }
            msp.add_text(text, dxfattribs={'layer': 'TEXTES', 'height': h}).set_placement((x, y), align=align_map.get(align, TextEntityAlignment.LEFT))
            
        # En-tête gauche
        header_top_y = oy + height - (2.0 * scale_ratio)
        add_text("République de Côte d'Ivoire", ox + (2 * scale_ratio), header_top_y, th)
        add_text("Ministère des Finances et du Budget", ox + (2 * scale_ratio), header_top_y - (2 * scale_ratio), th)
        add_text("Direction du Cadastre", ox + (2 * scale_ratio), header_top_y - (4 * scale_ratio), th)
        centre_ville = full_data.get('centre', '......')
        add_text(f"Bureau de {centre_ville}", ox + (2 * scale_ratio), header_top_y - (6 * scale_ratio), th)
        
        # Info Centre (Milieu-Haut)
        mid_x = ox + (35 * scale_ratio)
        add_text(f"Centre: {full_data.get('lotissement', '......')}", mid_x, header_top_y, th)
        add_text(f"Ilot: {full_data.get('ilot', '......')}    Lot: {full_data.get('lot', '......')}", mid_x, header_top_y - (2 * scale_ratio), th)
        add_text(f"Morcellement du TF: {full_data.get('tf', '......')}", mid_x, header_top_y - (4 * scale_ratio), th)
        add_text(f"Livre Foncier: {full_data.get('livre_foncier', '......')}", mid_x, header_top_y - (6 * scale_ratio), th)
        add_text(f"Demandeur: {full_data.get('demandeur', '......')}", mid_x, header_top_y - (8 * scale_ratio), th)
        
        # Dessin du lot et des voisins
        for nom_v, pts_v in voisins.items():
            if pts_v and len(pts_v) >= 3:
                msp.add_lwpolyline(pts_v, close=True, dxfattribs={'layer': 'VOISINS', 'linetype': 'DASHED'})
                vc_x = sum(p[0] for p in pts_v) / len(pts_v)
                vc_y = sum(p[1] for p in pts_v) / len(pts_v)
                add_text(nom_v, vc_x, vc_y, 1.2 * scale_ratio, 'CENTER')
                
        msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'PARCELLE'})
        for i, p in enumerate(points):
            msp.add_text(f"B{i+1}", dxfattribs={'layer': 'BORNES', 'height': 1.0 * scale_ratio}).set_placement((p[0] + 0.8*scale_ratio, p[1] + 0.8*scale_ratio))
            msp.add_circle(p, radius=0.4 * scale_ratio, dxfattribs={'layer': 'BORNES'})
            
        # Echelle et Contenance (dans le bas de la zone plan)
        add_text(f"ECHELLE : 1/{scale_val}", ox + (15 * scale_ratio), footer_line_y + (3 * scale_ratio), 1.4 * scale_ratio)
        
        # Pied de page gauche
        footer_top_y = footer_line_y - (2.0 * scale_ratio)
        add_text(f"N°: {full_data.get('dossier', '......')}", ox + (2 * scale_ratio), footer_top_y, th)
        add_text("Copie certifiée conforme", ox + (2 * scale_ratio), footer_top_y - (2.5 * scale_ratio), th)
        add_text("Le Géomètre Assermenté", ox + (2 * scale_ratio), footer_top_y - (5.0 * scale_ratio), th)
        
        # Signature
        sig_x = sep_x - (35 * scale_ratio)
        add_text(f"Levé par {full_data.get('cabinet_nom', '......')}", sig_x, footer_top_y, th)
        add_text(str(full_data.get('cabinet_adresse', '......'))[:40], sig_x, footer_top_y - (2.5 * scale_ratio), th)
        add_text(str(full_data.get('signataire_nom', '......')), sig_x, footer_top_y - (5.0 * scale_ratio), th)
        
        # ==========================================
        # COLONNE DROITE (TABLEAU)
        # ==========================================
        rx = sep_x + (2 * scale_ratio)
        ry = oy + height - (5 * scale_ratio)
        
        add_text("TABLEAU DES COORDONNEES", rx + (15 * scale_ratio), ry, 1.8 * scale_ratio, 'CENTER')
        add_text("WGS 84 UTM FUSEAU 30N", rx + (15 * scale_ratio), ry - (3 * scale_ratio), 1.1 * scale_ratio, 'CENTER')
        
        # Entêtes du tableau
        ty = ry - (7 * scale_ratio)
        col_w = [w * scale_ratio for w in [8, 11, 11, 10]] # Bornes, X, Y, Distances
        row_h = 3.0 * scale_ratio
        
        def draw_table_row(y, vals, is_header=False):
            cx_cell = rx
            h = 1.2 * scale_ratio if is_header else 1.0 * scale_ratio
            for i, val in enumerate(vals):
                msp.add_lwpolyline([(cx_cell, y), (cx_cell+col_w[i], y), (cx_cell+col_w[i], y-row_h), (cx_cell, y-row_h)], close=True, dxfattribs={'layer': 'CADRE'})
                add_text(str(val), cx_cell + (col_w[i]/2), y - (2 * scale_ratio), h, 'CENTER')
                cx_cell += col_w[i]
                
        draw_table_row(ty, ["BORNES", "X", "Y", "DIST"], True)
        
        # Lignes du tableau
        cy_row = ty - row_h
        for i in range(len(points)):
            b1 = points[i]
            b2 = points[(i+1)%len(points)]
            dist = math.sqrt((b2[0]-b1[0])**2 + (b2[1]-b1[1])**2)
            
            draw_table_row(cy_row, [f"B{i+1}", f"{b1[0]:.3f}", f"{b1[1]:.3f}", f"{dist:.3f}"])
            cy_row -= row_h

        # Sauvegarde
        output_path = os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path

