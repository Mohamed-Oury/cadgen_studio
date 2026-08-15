import ezdxf
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
            
        # 1. Calcul du centre du lot
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        
        # 2. Dimensions du cadre à l'échelle 1/500 (A4 = 297x210 mm -> 148.5x105 m)
        width = 148.5
        height = 105.0
        
        # Position du coin inférieur gauche du cadre
        ox = cx - (width * 0.35)  # On décentre légèrement le lot pour laisser la place au tableau à droite
        oy = cy - (height / 2)
        
        # 3. Dessin du cadre extérieur
        cadre_pts = [(ox, oy), (ox+width, oy), (ox+width, oy+height), (ox, oy+height)]
        msp.add_lwpolyline(cadre_pts, close=True, dxfattribs={'layer': 'CADRE'})
        
        # Ligne de séparation Gauche (65%) / Droite (35%)
        sep_x = ox + (width * 0.65)
        msp.add_line((sep_x, oy), (sep_x, oy+height), dxfattribs={'layer': 'CADRE'})
        
        # ==========================================
        # COLONNE GAUCHE (CARTOUCHE ET PLAN)
        # ==========================================
        
        # En-tête gauche
        header_y = oy + height - 2
        th = 1.2 # Text height
        
        def add_text(text, x, y, h, align='LEFT'):
            if not text: text = "......"
            align_map = {
                'LEFT': TextEntityAlignment.LEFT,
                'CENTER': TextEntityAlignment.CENTER,
                'RIGHT': TextEntityAlignment.RIGHT
            }
            # MTEXT is better but standard TEXT is easier to place precisely without wrapping issues in simple cases
            msp.add_text(text, dxfattribs={'layer': 'TEXTES', 'height': h}).set_placement((x, y), align=align_map.get(align, TextEntityAlignment.LEFT))
            
        add_text("République de Côte d'Ivoire", ox + 2, header_y, th)
        add_text("Ministère des Finances et du Budget", ox + 2, header_y - 2, th)
        add_text("Direction du Cadastre", ox + 2, header_y - 4, th)
        centre_ville = full_data.get('centre', '......')
        add_text(f"Bureau de {centre_ville}", ox + 2, header_y - 6, th)
        
        # Info Centre (Milieu-Haut)
        mid_x = ox + 45
        add_text(f"Centre: {full_data.get('lotissement', '......')}", mid_x, header_y, th)
        add_text(f"Ilot: {full_data.get('ilot', '......')}    Lot: {full_data.get('lot', '......')}", mid_x, header_y - 2, th)
        add_text(f"Morcellement du TF: {full_data.get('tf', '......')}", mid_x, header_y - 4, th)
        add_text(f"Livre Foncier: {full_data.get('livre_foncier', '......')}", mid_x, header_y - 6, th)
        add_text(f"Demandeur: {full_data.get('demandeur', '......')}", mid_x, header_y - 8, th)
        
        # Ligne sous l'en-tête
        msp.add_line((ox, header_y - 10), (sep_x, header_y - 10), dxfattribs={'layer': 'CADRE'})
        
        # Dessin du lot et des voisins (déjà à leurs vraies coordonnées)
        for nom_v, pts_v in voisins.items():
            if pts_v:
                msp.add_lwpolyline(pts_v, close=True, dxfattribs={'layer': 'VOISINS', 'linetype': 'DASHED'})
                # Label voisin
                vc_x = sum(p[0] for p in pts_v) / len(pts_v)
                vc_y = sum(p[1] for p in pts_v) / len(pts_v)
                add_text(nom_v, vc_x, vc_y, 1.5, 'CENTER')
                
        msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'PARCELLE'})
        for i, p in enumerate(points):
            msp.add_text(f"B{i+1}", dxfattribs={'layer': 'BORNES', 'height': 1.0}).set_placement((p[0]+1, p[1]+1))
            msp.add_circle(p, radius=0.5, dxfattribs={'layer': 'BORNES'})
            
        # Echelle et Contenance
        add_text("ECHELLE : 1/500", ox + 20, oy + 2, 1.5)
        
        # Pied de page gauche
        add_text(f"N°: {full_data.get('dossier', '......')}", ox + 2, oy + 8, th)
        add_text("Copie certifiée conforme", ox + 2, oy + 6, th)
        add_text(f"Le Géomètre Assermenté", ox + 2, oy + 2, th)
        
        # Signature
        sig_x = sep_x - 30
        add_text(f"Levé par {full_data.get('cabinet_nom', '......')}", sig_x, oy + 8, th)
        add_text(full_data.get('cabinet_adresse', '......')[:40], sig_x, oy + 6, th)
        add_text(full_data.get('signataire_nom', '......'), sig_x, oy + 4, th)
        
        # ==========================================
        # COLONNE DROITE (TABLEAU)
        # ==========================================
        rx = sep_x + 2
        ry = oy + height - 5
        
        add_text("TABLEAU DES COORDONNEES", rx + 15, ry, 2.0, 'CENTER')
        add_text("WGS 84 UTM FUSEAU 30N", rx + 15, ry - 3, 1.2, 'CENTER')
        
        # Entêtes du tableau
        ty = ry - 8
        col_w = [8, 12, 12, 10] # Bornes, X, Y, Distances
        
        def draw_table_row(y, vals, is_header=False):
            cx = rx
            h = 1.2 if is_header else 1.0
            for i, val in enumerate(vals):
                # Box
                msp.add_lwpolyline([(cx, y), (cx+col_w[i], y), (cx+col_w[i], y-3), (cx, y-3)], close=True, dxfattribs={'layer': 'CADRE'})
                # Text
                add_text(str(val), cx + (col_w[i]/2), y - 2, h, 'CENTER')
                cx += col_w[i]
                
        draw_table_row(ty, ["BORNES", "X", "Y", "DIST"], True)
        
        # Lignes du tableau
        cy = ty - 3
        for i in range(len(points)):
            b1 = points[i]
            b2 = points[(i+1)%len(points)]
            dist = math.sqrt((b2[0]-b1[0])**2 + (b2[1]-b1[1])**2)
            
            draw_table_row(cy, [f"B{i+1}", f"{b1[0]:.3f}", f"{b1[1]:.3f}", f"{dist:.3f}"])
            cy -= 3

        # Sauvegarde
        output_path = os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
