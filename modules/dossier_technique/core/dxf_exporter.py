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
        Génère un fichier DXF reproduisant fidèlement la page 4 du PDF
        sur un format A3 paysage (420 × 297 mm).

        Layout (2 panneaux de ~210mm chacun):
          ┌──────────────────────────┬──────────────────────────┐
          │  PANNEAU GAUCHE (50%)    │  PANNEAU DROIT (50%)     │
          │                          │                          │
          │  ┌─ En-tête 3 colonnes ─┐│  TABLEAU DES COORDONNÉES │
          │  │ Rép. │ TF │ Centre   ││  ITRF96-1998.2           │
          │  └──────────────────────┘│  ┌──────────────────────┐│
          │  ┌─Situation─┐  NOTA     │  │ BORNES│X│Y│ANG│DIST ││
          │  │  1/5000   │ Contenance│  │  B1   │ │ │   │     ││
          │  └───────────┘           │  │  B2   │ │ │   │     ││
          │                          │  │  ...  │ │ │   │     ││
          │  ┌─ Plan de Masse ──────┐│  └──────────────────────┘│
          │  │   Croquis bornage    ││                          │
          │  │   Échelle 1/500      ││                          │
          │  │   (taille réelle)    ││                          │
          │  └──────────────────────┘│                          │
          │  ┌─ Pied de page ───────┐│                          │
          │  │ N° │ Certif │ Cabinet││                          │
          │  └──────────────────────┘│                          │
          └──────────────────────────┴──────────────────────────┘
        """
        doc = ezdxf.new('R2010', setup=True)
        msp = doc.modelspace()

        # ── Calques ──
        doc.layers.add('CADRE', color=7)
        doc.layers.add('TEXTES', color=7)
        doc.layers.add('TEXTES_BOLD', color=7)
        doc.layers.add('PARCELLE', color=1)
        doc.layers.add('PARCELLE_FILL', color=1)
        doc.layers.add('BORNES', color=1)
        doc.layers.add('VOISINS', color=8)
        doc.layers.add('TABLEAU', color=7)

        points = lot_data.get('bornes', [])
        voisins = full_data.get('voisins', {})

        if not points:
            return None

        # ══════════════════════════════════════════════════════
        # DIMENSIONS A3 PAYSAGE (mm)
        # ══════════════════════════════════════════════════════
        W = 420.0   # Largeur A3 paysage
        H = 297.0   # Hauteur A3 paysage
        ox = 0.0
        oy = 0.0

        # Séparation gauche/droite (50/50 → chaque panneau ≈ A4)
        sep_x = ox + W * 0.50   # 210 mm

        # Tailles de texte (en mm)
        t_tiny = 1.8
        t_small = 2.2
        t_normal = 2.8
        t_bold = 3.2
        t_title = 4.5

        # ══════════════════════════════════════════════════════
        # CADRE EXTÉRIEUR + SÉPARATION VERTICALE
        # ══════════════════════════════════════════════════════
        msp.add_lwpolyline(
            [(ox, oy), (ox + W, oy), (ox + W, oy + H), (ox, oy + H)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )
        msp.add_line((sep_x, oy), (sep_x, oy + H), dxfattribs={'layer': 'CADRE'})

        # ── Helper: texte aligné (ezdxf 1.4.x → set_placement) ──
        def add_text(text, x, y, h=t_normal, layer='TEXTES', align='LEFT'):
            if not text:
                text = "......"
            text = str(text)
            align_map = {
                'LEFT': TextEntityAlignment.LEFT,
                'CENTER': TextEntityAlignment.CENTER,
                'RIGHT': TextEntityAlignment.RIGHT,
            }
            align_val = align_map.get(align, TextEntityAlignment.LEFT)
            t_entity = msp.add_text(text, dxfattribs={'layer': layer, 'height': h})
            t_entity.set_placement((x, y), align=align_val)

        # ── Données du formulaire ──
        centre = full_data.get('centre', '......')
        tf = full_data.get('tf', '......')
        section = full_data.get('section', '......')
        ilot = full_data.get('ilot', '......')
        lot = full_data.get('lot', '......')
        lotissement = full_data.get('lotissement', '......')
        livre_foncier = full_data.get('livre_foncier', '......')
        demandeur = full_data.get('demandeur', '......')
        dossier = full_data.get('dossier', '......')
        cabinet_nom = full_data.get('cabinet_nom', '......')
        cabinet_adresse = full_data.get('cabinet_adresse', '......')
        signataire_nom = full_data.get('signataire_nom', '......')
        signataire_titre = full_data.get('signataire_titre', '......')
        date_consultation = full_data.get('date_consultation', '......')

        # ══════════════════════════════════════════════════════
        # EN-TÊTE GAUCHE (3 colonnes) — tiers supérieur
        # ══════════════════════════════════════════════════════
        header_top = oy + H - 5.0
        header_bottom = oy + H - 50.0   # ~45mm de hauteur
        msp.add_line((ox, header_bottom), (sep_x, header_bottom), dxfattribs={'layer': 'CADRE'})

        # Séparateurs verticaux dans l'en-tête
        hcol2_x = ox + 62.0
        hcol3_x = ox + 115.0
        msp.add_line((hcol2_x, header_top + 5.0), (hcol2_x, header_bottom), dxfattribs={'layer': 'CADRE'})
        msp.add_line((hcol3_x, header_top + 5.0), (hcol3_x, header_bottom), dxfattribs={'layer': 'CADRE'})

        # Colonne 1 — République
        col1_x = ox + 5.0
        ly = header_top
        add_text("Republique de Côte d'Ivoire", col1_x, ly, t_small)
        add_text("Ministère des Finances et du Budget", col1_x, ly - 4.5, t_small)
        add_text("Direction du Cadastre", col1_x, ly - 9.0, t_small)
        add_text(f"Bureau de {centre}", col1_x, ly - 13.5, t_small)

        # Colonne 2 — TF / Section
        col2_x = hcol2_x + 4.0
        add_text(f"T.F.No:    {tf}", col2_x, ly, t_small)
        add_text(f"Section:   {section}", col2_x, ly - 5.0, t_small)
        add_text("No du Plan:  ......", col2_x, ly - 10.0, t_small)

        # Colonne 3 — Centre / Ilot / Lot / Demandeur
        col3_x = hcol3_x + 4.0
        add_text(f"Centre: {lotissement}", col3_x, ly, t_small)
        add_text(f"Ilot: {ilot}    Lot: {lot}    Parcelle: ......", col3_x, ly - 4.0, t_small)
        add_text(f"Morcellement du TF: {tf}", col3_x, ly - 8.0, t_small)
        add_text("Fusion des TF.....: ......", col3_x, ly - 12.0, t_small)
        add_text("Requisition ......: ......", col3_x, ly - 16.0, t_small)
        add_text(f"Livre Foncier de : {livre_foncier}", col3_x, ly - 20.0, t_small)
        add_text("Cédant: ETAT DE CI", col3_x, ly - 24.0, t_small)
        add_text(f"Demandeur: {demandeur}", col3_x, ly - 28.0, t_small, layer='TEXTES_BOLD')

        # ══════════════════════════════════════════════════════
        # PIED DE PAGE GAUCHE — ligne de séparation
        # ══════════════════════════════════════════════════════
        footer_top = oy + 40.0
        msp.add_line((ox, footer_top), (sep_x, footer_top), dxfattribs={'layer': 'CADRE'})

        # ══════════════════════════════════════════════════════
        # ZONE CONTENU GAUCHE
        # ══════════════════════════════════════════════════════
        content_top = header_bottom - 3.0
        content_bottom = footer_top + 3.0

        # ── Calculs géométriques du lot ──
        min_bx = min(p[0] for p in points)
        max_bx = max(p[0] for p in points)
        min_by = min(p[1] for p in points)
        max_by = max(p[1] for p in points)
        lot_w = max_bx - min_bx
        lot_h = max_by - min_by
        cx_lot = (min_bx + max_bx) / 2.0
        cy_lot = (min_by + max_by) / 2.0

        # ══════════════════════════════════════════════════════
        # PLAN DE SITUATION (1/5000) — coin supérieur gauche
        # ══════════════════════════════════════════════════════
        sit_x = ox + 5.0
        sit_y = content_top
        sit_w = 80.0
        sit_h = 55.0

        # Cadre du plan de situation
        msp.add_lwpolyline(
            [(sit_x, sit_y), (sit_x + sit_w, sit_y),
             (sit_x + sit_w, sit_y - sit_h), (sit_x, sit_y - sit_h)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )

        # Échelle 1/5000 : 1 mètre réel = 1000mm / 5000 = 0.2mm sur papier
        scale_5000 = full_data.get('scale_5000', 5000)
        sit_paper_scale = 1000.0 / scale_5000  # mm par mètre

        # Centrer le lot dans la boîte situation
        sit_cx = sit_x + sit_w / 2.0
        sit_cy = sit_y - sit_h / 2.0

        def world_to_sit(wx, wy):
            return (
                sit_cx + (wx - cx_lot) * sit_paper_scale,
                sit_cy + (wy - cy_lot) * sit_paper_scale
            )

        # Voisins en situation
        for nom_v, pts_v in voisins.items():
            if pts_v and len(pts_v) >= 3:
                s_pts = [world_to_sit(p[0], p[1]) for p in pts_v]
                msp.add_lwpolyline(s_pts, close=True,
                                   dxfattribs={'layer': 'VOISINS', 'linetype': 'DASHED'})

        # Lot principal rempli
        sit_lot_pts = [world_to_sit(p[0], p[1]) for p in points]
        hatch = msp.add_hatch(color=0, dxfattribs={'layer': 'PARCELLE_FILL'})
        hatch.paths.add_polyline_path(
            [(p[0], p[1]) for p in sit_lot_pts],
            is_closed=True
        )
        msp.add_lwpolyline(sit_lot_pts, close=True,
                           dxfattribs={'layer': 'PARCELLE'})

        # Flèche Nord
        north_x = sit_x + sit_w - 8.0
        north_y_top = sit_y - 5.0
        north_y_bot = north_y_top - 12.0
        msp.add_line((north_x, north_y_bot), (north_x, north_y_top),
                      dxfattribs={'layer': 'CADRE'})
        # Pointe de flèche
        msp.add_lwpolyline(
            [(north_x - 2.0, north_y_top - 2.5),
             (north_x, north_y_top),
             (north_x + 2.0, north_y_top - 2.5)],
            dxfattribs={'layer': 'CADRE'}
        )
        add_text("N", north_x, north_y_top + 1.5, t_normal, align='CENTER')

        # Label échelle situation
        echelle_1 = full_data.get('echelle_1', f"1/{scale_5000}")
        # Bandeau sous la boîte situation
        msp.add_lwpolyline(
            [(sit_x, sit_y - sit_h), (sit_x + sit_w, sit_y - sit_h),
             (sit_x + sit_w, sit_y - sit_h - 6.0), (sit_x, sit_y - sit_h - 6.0)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )
        add_text(f"ECHELLE : {echelle_1}", sit_x + sit_w / 2.0,
                 sit_y - sit_h - 4.0, t_normal, align='CENTER', layer='TEXTES_BOLD')

        # ── NOTA + Contenance (à droite du plan de situation) ──
        nota_x = sit_x + sit_w + 12.0
        nota_y = content_top - 5.0
        add_text("NOTA: Toute reproduction officielle doit obligatoirement",
                 nota_x, nota_y, t_small)
        add_text("comporter le timbre sec du Service du Cadastre",
                 nota_x, nota_y - 4.5, t_small)

        # Contenance
        surface_str = full_data.get('surface', '0.0')
        try:
            surface_val = float(str(surface_str).replace("m²", "").replace(" ", "").replace(",", ".").strip())
        except (ValueError, TypeError):
            surface_val = 0.0

        ha = int(surface_val // 10000)
        a = int((surface_val % 10000) // 100)
        ca = int(surface_val % 100)
        contenance_str = f"{ha:02d} ha {a:02d} a {ca:02d} ca"

        add_text("Contenance:", nota_x + 15.0, nota_y - 18.0, t_normal, align='CENTER')
        add_text(contenance_str, nota_x + 15.0, nota_y - 24.0, t_bold,
                 align='CENTER', layer='TEXTES_BOLD')

        # ══════════════════════════════════════════════════════
        # PLAN DE MASSE (1/500) — ÉCHELLE RÉELLE
        # Zone: du milieu du panneau gauche jusqu'au footer
        # ══════════════════════════════════════════════════════
        masse_top = content_top - sit_h - 12.0
        masse_bottom = content_bottom
        masse_left = ox + 5.0
        masse_right = sep_x - 5.0
        masse_w = masse_right - masse_left
        # Échelle 1/500 réelle : 1 mètre réel = 1000mm / 500 = 2mm sur papier
        scale_500 = full_data.get('scale_500', 500)
        masse_paper_scale = 1000.0 / scale_500  # mm par mètre

        # Repères réels A3 paysage (420 × 297 mm) :
        # Panneau gauche = 210 × 297 mm
        # Le tracé de bornage B1-B2-B3-B4 (~48×48 mm) est centré horizontalement à masse_cx = 105 mm.
        # Son coin haut (B1) est situé à 40-45% de la hauteur depuis le haut (soit Y ≈ 170.8 mm).
        lot_h_paper = lot_h * masse_paper_scale
        masse_cx = ox + sep_x * 0.50  # 105.0 mm (centré dans le panneau gauche)
        masse_cy = (oy + H * 0.575) - (lot_h_paper / 2.0)  # Centre Y calculé pour que le haut soit à 42.5%

        def world_to_masse(wx, wy):
            return (
                masse_cx + (wx - cx_lot) * masse_paper_scale,
                masse_cy + (wy - cy_lot) * masse_paper_scale
            )

        # Voisins dans le plan de masse (garder UNIQUEMENT les 2 plus proches)
        masse_voisins = {}
        if voisins:
            def neighbor_distance(pts):
                min_d = min(math.hypot(px - lx, py - ly) for px, py in pts for lx, ly in points)
                vcx = sum(p[0] for p in pts) / len(pts)
                vcy = sum(p[1] for p in pts) / len(pts)
                cd = math.hypot(vcx - cx_lot, vcy - cy_lot)
                return (min_d, cd)

            valid_v = [(n, pts) for n, pts in voisins.items() if pts and len(pts) >= 3]
            valid_v.sort(key=lambda x: neighbor_distance(x[1]))
            masse_voisins = dict(valid_v[:2])

        for nom_v, pts_v in masse_voisins.items():
            m_pts = [world_to_masse(p[0], p[1]) for p in pts_v]
            msp.add_lwpolyline(m_pts, close=True,
                               dxfattribs={'layer': 'VOISINS', 'linetype': 'DASHED'})
            # Label voisin
            vc_x = sum(p[0] for p in pts_v) / len(pts_v)
            vc_y = sum(p[1] for p in pts_v) / len(pts_v)
            mx, my = world_to_masse(vc_x, vc_y)
            add_text(nom_v, mx, my, t_small, align='CENTER')

        # Lot principal
        masse_lot_pts = [world_to_masse(p[0], p[1]) for p in points]
        msp.add_lwpolyline(masse_lot_pts, close=True,
                           dxfattribs={'layer': 'PARCELLE'})

        # Bornes + labels + distances sur segments
        for i, p in enumerate(points):
            mx, my = world_to_masse(p[0], p[1])
            # Cercle de borne
            msp.add_circle((mx, my), radius=0.8, dxfattribs={'layer': 'BORNES'})
            # Label borne
            add_text(f"B{i + 1}", mx + 1.5, my + 1.5, t_small, layer='BORNES')

            # Distance sur le segment vers la borne suivante
            p2 = points[(i + 1) % len(points)]
            dist = math.sqrt((p2[0] - p[0]) ** 2 + (p2[1] - p[1]) ** 2)
            mid_wx = (p[0] + p2[0]) / 2.0
            mid_wy = (p[1] + p2[1]) / 2.0
            mid_mx, mid_my = world_to_masse(mid_wx, mid_wy)

            # Angle du segment pour rotation
            angle = math.degrees(math.atan2(p2[1] - p[1], p2[0] - p[0]))
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

            # Décaler perpendiculairement au segment
            perp_angle = math.radians(angle + 90)
            offset = 2.0
            t_dist = msp.add_text(
                f"{dist:.3f}",
                dxfattribs={'layer': 'TEXTES', 'height': 1.8, 'rotation': angle}
            )
            t_dist.set_placement(
                (mid_mx + offset * math.cos(perp_angle),
                 mid_my + offset * math.sin(perp_angle)),
                align=TextEntityAlignment.CENTER
            )

        # Label échelle masse positionné sous le tracé
        echelle_2 = full_data.get('echelle_2', f"1/{scale_500}")
        lot_bottom_paper = masse_cy - (lot_h_paper / 2.0)
        echelle_y = max(lot_bottom_paper - 8.0, footer_top + 6.0)
        add_text(f"ECHELLE : {echelle_2}", masse_cx,
                 echelle_y, t_bold, align='CENTER', layer='TEXTES_BOLD')

        # ══════════════════════════════════════════════════════
        # PIED DE PAGE GAUCHE
        # ══════════════════════════════════════════════════════
        foot_y = footer_top - 4.0

        # Colonne gauche du footer
        add_text(f"N°: {dossier}", ox + 5.0, foot_y, t_normal, layer='TEXTES_BOLD')
        add_text("Copie certifiée conforme", ox + 5.0, foot_y - 5.0, t_small)
        centre_cap = centre.capitalize() if centre and centre != '......' else '......'
        add_text(f"{centre_cap}, le :", ox + 5.0, foot_y - 9.0, t_small)
        add_text("Le Géomètre Assermenté du Cadastre", ox + 5.0, foot_y - 13.0, t_small)

        # Colonne droite du footer
        footer_right_x = sep_x - 50.0
        add_text(f"Levé et Dressé par {cabinet_nom}", footer_right_x, foot_y,
                 t_normal, align='CENTER', layer='TEXTES_BOLD')
        add_text(str(cabinet_adresse)[:60], footer_right_x, foot_y - 4.5,
                 t_small, align='CENTER')
        centre_up = centre.upper() if centre and centre != '......' else '......'
        add_text(f"{centre_up}, le {date_consultation}", footer_right_x,
                 foot_y - 9.0, t_small, align='CENTER')
        add_text(str(signataire_nom), footer_right_x, foot_y - 15.0,
                 t_normal, align='CENTER', layer='TEXTES_BOLD')
        add_text(str(signataire_titre), footer_right_x, foot_y - 19.0,
                 t_small, align='CENTER')

        # ══════════════════════════════════════════════════════
        # PANNEAU DROIT — TABLEAU DES COORDONNÉES
        # ══════════════════════════════════════════════════════
        right_left = sep_x + 5.0
        right_right = ox + W - 5.0
        right_w = right_right - right_left

        # Titre
        tab_title_y = oy + H - 10.0
        add_text("TABLEAU DES COORDONNEES",
                 sep_x + (W - sep_x) / 2.0, tab_title_y,
                 t_title, align='CENTER', layer='TEXTES_BOLD')
        add_text("ITRF96-1998.2 /Ellipsoïde du WGS 84 UTM FUSEAU 30N",
                 sep_x + (W - sep_x) / 2.0, tab_title_y - 6.0,
                 t_small, align='CENTER')

        # Colonnes: BORNES | X | Y | ANGLES | DISTANCES
        tab_y = tab_title_y - 14.0
        col_widths = [18.0, 38.0, 38.0, 25.0, 25.0]
        row_h = 7.0
        total_table_w = sum(col_widths)

        # Centrer le tableau dans le panneau droit
        tab_x = sep_x + ((W - sep_x) - total_table_w) / 2.0

        def draw_cell(x, y, w, h, text="", text_h=t_small, bold=False):
            """Dessine une cellule avec texte centré."""
            msp.add_lwpolyline(
                [(x, y), (x + w, y), (x + w, y - h), (x, y - h)],
                close=True, dxfattribs={'layer': 'TABLEAU'}
            )
            if text:
                layer = 'TEXTES_BOLD' if bold else 'TEXTES'
                add_text(str(text), x + w / 2.0, y - h / 2.0 - text_h * 0.3,
                         text_h, layer=layer, align='CENTER')

        def draw_row(y, values, is_header=False):
            cx_cell = tab_x
            th = t_normal if is_header else t_small
            for i, val in enumerate(values):
                draw_cell(cx_cell, y, col_widths[i], row_h,
                          str(val), th, bold=is_header)
                cx_cell += col_widths[i]

        # En-tête du tableau
        draw_row(tab_y, ["BORNES", "X", "Y", "ANGLES", "DISTANCES"], is_header=True)

        # Calcul des données
        bornes_calc = []
        for i in range(len(points)):
            b_cur = points[i]
            b_next = points[(i + 1) % len(points)]
            dist = math.sqrt((b_next[0] - b_cur[0]) ** 2 + (b_next[1] - b_cur[1]) ** 2)
            bornes_calc.append({
                'nom': f"B{i + 1}",
                'x': b_cur[0],
                'y': b_cur[1],
                'angle': 100.000,
                'dist': dist,
            })

        # Lignes du tableau — distances avec effet rowspan entre 2 bornes
        cy_row = tab_y - row_h
        for i, b in enumerate(bornes_calc):
            # Cellules BORNES, X, Y, ANGLES
            cx_cell = tab_x
            vals = [b['nom'], f"{b['x']:.3f}", f"{b['y']:.3f}", f"{b['angle']:.3f}"]
            for j, val in enumerate(vals):
                draw_cell(cx_cell, cy_row, col_widths[j], row_h, val)
                cx_cell += col_widths[j]

            # Cellule DISTANCES (rowspan visuel: à cheval entre cette ligne et la suivante)
            dist_x = cx_cell
            dist_cell_h = row_h
            msp.add_lwpolyline(
                [(dist_x, cy_row),
                 (dist_x + col_widths[4], cy_row),
                 (dist_x + col_widths[4], cy_row - dist_cell_h),
                 (dist_x, cy_row - dist_cell_h)],
                close=True, dxfattribs={'layer': 'TABLEAU'}
            )
            add_text(f"{b['dist']:.3f}",
                     dist_x + col_widths[4] / 2.0,
                     cy_row - dist_cell_h / 2.0 - 0.5,
                     t_small, align='CENTER')

            cy_row -= row_h

        # Dernière ligne: B1 (retour/fermeture du polygone)
        cx_cell = tab_x
        draw_cell(cx_cell, cy_row, col_widths[0], row_h, "B1")
        cx_cell += col_widths[0]
        for j in range(1, 5):
            draw_cell(cx_cell, cy_row, col_widths[j], row_h, "")
            cx_cell += col_widths[j]

        # ══════════════════════════════════════════════════════
        # VIEWPORT / ZOOM — centrer sur la feuille A3
        # ══════════════════════════════════════════════════════
        doc.set_modelspace_vport(
            center=(W / 2.0, H / 2.0),
            height=H * 1.05
        )

        # ── Sauvegarde ──
        output_path = filename if os.path.isabs(filename) else os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
