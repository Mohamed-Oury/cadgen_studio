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
        Génère un fichier DXF reproduisant fidèlement la page 4 du document cadastral
        sur un format A3 paysage (420 × 297 mm).

        Layout :
          ┌──────────────────────────────────┬────────────────────────┐
          │  PANNEAU GAUCHE (58%)            │  PANNEAU DROIT (42%)   │
          │                                  │                        │
          │  ┌─ En-tête 3 colonnes ─────────┐│ TABLEAU COORDONNÉES    │
          │  │ Rép. │ TF/Sect │ Centre/Lot  ││ (centré, w≈140mm)      │
          │  └──────────────────────────────┘│ ┌────────────────────┐ │
          │  ┌─Situation─┐ ⮝   NOTA          │ │BORNES│ X │ Y │A │D │ │
          │  │  1/5000   │ N  Contenance     │ │  B1  │...│...│..│  │ │
          │  └───────────┘                   │ │  B2  │...│...│..│..│ │
          │                                  │ │  ... │...│...│..│..│ │
          │     Plan de Masse (1/500)        │ │  B1  │   │   │  │..│ │
          │     (croquis sans cadre,         │ └────────────────────┘ │
          │      2 voisins, carroyage +)     │                        │
          │                                  │                        │
          │  ┌─ Pied de page ───────────────┐│                        │
          │  │ N°/Certif │ ECHELLE │ Cabinet││                        │
          │  └──────────────────────────────┘│                        │
          └──────────────────────────────────┴────────────────────────┘
        """
        doc = ezdxf.new('R2010', setup=True)
        msp = doc.modelspace()

        # ── Configuration de la police Times New Roman ──
        try:
            if 'Standard' in doc.styles:
                doc.styles.get('Standard').dxf.font = 'times.ttf'
            if 'Times' not in doc.styles:
                doc.styles.new('Times', dxfattribs={'font': 'times.ttf'})
        except Exception:
            pass

        # ── Calques normalisés ──
        def ensure_layer(name, color, linetype='Continuous'):
            if name not in doc.layers:
                doc.layers.add(name, color=color, linetype=linetype)

        ensure_layer('CADRE', color=7)
        ensure_layer('CARROYAGE', color=8)
        ensure_layer('TEXTES', color=7)
        ensure_layer('TEXTES_BOLD', color=7)
        ensure_layer('PARCELLE', color=1)
        ensure_layer('PARCELLE_FILL', color=7)
        ensure_layer('BORNES', color=1)
        ensure_layer('VOISINS', color=8, linetype='DASHED')
        ensure_layer('TABLEAU', color=7)

        # Extraction des données du lot
        points = []
        if isinstance(lot_data, dict):
            points = lot_data.get('bornes', [])
        if not points and isinstance(full_data, dict):
            points = full_data.get('bornes', [])

        voisins = full_data.get('voisins', {}) if isinstance(full_data, dict) else {}

        if not points or len(points) < 3:
            return None

        # ══════════════════════════════════════════════════════
        # 1. GÉOMÉTRIE DE LA FEUILLE A3 PAYSAGE (420 × 297 mm)
        # ══════════════════════════════════════════════════════
        W = 420.0
        H = 297.0
        ox = 0.0
        oy = 0.0

        # Séparation verticale 58% / 42%
        sep_x = ox + W * 0.58   # 243.6 mm

        # Tailles typographiques (mm)
        t_tiny = 1.8
        t_small = 2.2
        t_normal = 2.7
        t_bold = 3.2
        t_title = 4.2

        # Cadre extérieur de la feuille A3
        msp.add_lwpolyline(
            [(ox, oy), (ox + W, oy), (ox + W, oy + H), (ox, oy + H)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )
        # Séparation verticale principale
        msp.add_line((sep_x, oy), (sep_x, oy + H), dxfattribs={'layer': 'CADRE'})

        # ── Helper texte avec alignement ──
        align_map = {
            'LEFT': TextEntityAlignment.LEFT,
            'CENTER': TextEntityAlignment.CENTER,
            'RIGHT': TextEntityAlignment.RIGHT,
            'MIDDLE_CENTER': TextEntityAlignment.MIDDLE_CENTER,
        }

        def add_text(text, x, y, h=t_normal, layer='TEXTES', align='LEFT', rotation=0.0):
            if text is None:
                text = ""
            text = str(text)
            if not text.strip():
                return None
            align_val = align_map.get(align, TextEntityAlignment.LEFT)
            t_entity = msp.add_text(
                text,
                dxfattribs={'layer': layer, 'height': h, 'style': 'Times', 'rotation': rotation}
            )
            t_entity.set_placement((x, y), align=align_val)
            return t_entity

        # ── Données textuelles sécurisées ──
        def val(k, default="......"):
            v = full_data.get(k) if isinstance(full_data, dict) else None
            return str(v).strip() if v and str(v).strip() else default

        centre = val('centre')
        tf = val('tf')
        section = val('section')
        ilot = val('ilot')
        lot = val('lot')
        lotissement = val('lotissement', centre)
        livre_foncier = val('livre_foncier')
        demandeur = val('demandeur')
        dossier = val('dossier')
        cabinet_nom = val('cabinet_nom', 'CABINET KOUAMELAN')
        cabinet_adresse = val('cabinet_adresse', '26 BP 1029 ABIDJAN 26 - Tel : 0707074850')
        signataire_nom = val('signataire_nom', 'Ahoulou Joseph KOUAMELAN')
        signataire_titre = val('signataire_titre', 'Géomètre-Expert Agréé\nMédiateur Professionnel\nChevalier du Mérite Agricole')
        date_consultation = val('date_consultation', '31-07-2026')

        # ══════════════════════════════════════════════════════
        # 2. EN-TÊTE DU PANNEAU GAUCHE (3 colonnes)
        # ══════════════════════════════════════════════════════
        header_top = oy + H
        header_bottom = oy + H - 48.0   # Ligne horizontale à Y=249.0 mm
        msp.add_line((ox, header_bottom), (sep_x, header_bottom), dxfattribs={'layer': 'CADRE'})

        # Lignes verticales internes de l'en-tête
        hcol2_x = ox + 60.0
        hcol3_x = ox + 115.0
        msp.add_line((hcol2_x, header_top), (hcol2_x, header_bottom), dxfattribs={'layer': 'CADRE'})
        msp.add_line((hcol3_x, header_top), (hcol3_x, header_bottom), dxfattribs={'layer': 'CADRE'})

        # Colonne 1 : République & Ministère (centrée ou à gauche bien aérée)
        col1_x = ox + 5.0
        ly1 = header_top - 6.0
        add_text("Republique de Côte d'Ivoire", col1_x, ly1, t_small)
        add_text("Ministère des Finances et du Budget", col1_x, ly1 - 5.0, t_small)
        add_text("Direction du Cadastre", col1_x, ly1 - 10.0, t_small)
        add_text(f"Bureau de {centre}", col1_x, ly1 - 15.0, t_small)

        # Colonne 2 : TF, Section, Plan
        col2_x = hcol2_x + 4.0
        ly2 = header_top - 6.0
        add_text(f"T.F.No:    {tf}", col2_x, ly2, t_small)
        add_text(f"Section:   {section}", col2_x, ly2 - 5.0, t_small)
        add_text("No du Plan:  ......", col2_x, ly2 - 10.0, t_small)

        # Colonne 3 : Détails morcellement
        col3_x = hcol3_x + 4.0
        ly3 = header_top - 5.0
        add_text(f"Centre: {lotissement}", col3_x, ly3, t_small)
        add_text(f"Ilot: {ilot}    Lot: {lot}    Parcelle: ......", col3_x, ly3 - 4.5, t_small)
        add_text(f"Morcellement du TF: {tf}", col3_x, ly3 - 9.0, t_small)
        add_text("Fusion des TF.....: ......", col3_x, ly3 - 13.5, t_small)
        add_text("Requisition ......: ......", col3_x, ly3 - 18.0, t_small)
        add_text(f"Livre Foncier de : {livre_foncier}", col3_x, ly3 - 22.5, t_small)
        add_text("Cédant: ETAT DE CI", col3_x, ly3 - 27.0, t_small)
        add_text(f"Demandeur: {demandeur}", col3_x, ly3 - 31.5, t_small, layer='TEXTES_BOLD')

        # ══════════════════════════════════════════════════════
        # 3. PIED DE PAGE DU PANNEAU GAUCHE
        # ══════════════════════════════════════════════════════
        footer_top = oy + 38.0  # Ligne horizontale à Y=38.0 mm
        msp.add_line((ox, footer_top), (sep_x, footer_top), dxfattribs={'layer': 'CADRE'})

        # Contenu du footer (3 colonnes virtuelles)
        foot_y = footer_top - 5.0

        # Colonne gauche du footer
        add_text("Copie certifiée conforme", ox + 5.0, foot_y, t_small)
        centre_cap = centre.capitalize() if centre and centre != '......' else '......'
        add_text(f"{centre_cap}, le :", ox + 5.0, foot_y - 4.5, t_small)
        add_text("Le Géomètre Assermenté du Cadastre", ox + 5.0, foot_y - 9.0, t_small)
        add_text(f"N°: {dossier}", ox + 5.0, foot_y - 18.0, t_small, layer='TEXTES_BOLD')

        # Colonne centrale du footer : ECHELLE 1/500
        scale_500 = full_data.get('scale_500', 500) if isinstance(full_data, dict) else 500
        echelle_2 = full_data.get('echelle_2', f"1/{scale_500}") if isinstance(full_data, dict) else f"1/{scale_500}"
        foot_cx = ox + sep_x * 0.48
        add_text(f"ECHELLE : {echelle_2}", foot_cx, foot_y - 12.0, t_bold, align='CENTER', layer='TEXTES_BOLD')

        # Colonne droite du footer
        foot_rx = sep_x - 52.0
        add_text(f"Levé et Dressé par {cabinet_nom}", foot_rx, foot_y, t_normal, align='CENTER', layer='TEXTES_BOLD')
        # Découpage adresse cabinet
        adr_lines = str(cabinet_adresse).replace('<br>', '\n').split('\n')
        cur_y = foot_y - 4.0
        for adr_l in adr_lines:
            if adr_l.strip():
                add_text(adr_l.strip(), foot_rx, cur_y, t_tiny, align='CENTER')
                cur_y -= 3.5
        centre_up = centre.upper() if centre and centre != '......' else '......'
        add_text(f"{centre_up}, le {date_consultation}", foot_rx, cur_y - 1.0, t_tiny, align='CENTER')

        # Signataire et titres
        cur_y -= 6.0
        add_text(str(signataire_nom), foot_rx, cur_y, t_normal, align='CENTER', layer='TEXTES_BOLD')
        titre_lines = str(signataire_titre).replace('<br>', '\n').split('\n')
        for t_line in titre_lines:
            if t_line.strip():
                cur_y -= 3.5
                add_text(t_line.strip(), foot_rx, cur_y, t_tiny, align='CENTER')

        # ══════════════════════════════════════════════════════
        # 4. RANGÉE SITUATION / BOUSSOLE / NOTA / CONTENANCE
        # ══════════════════════════════════════════════════════
        content_top = header_bottom - 4.0

        # Calculs géométriques du lot principal
        xs_pts = [p[0] for p in points]
        ys_pts = [p[1] for p in points]
        min_bx, max_bx = min(xs_pts), max(xs_pts)
        min_by, max_by = min(ys_pts), max(ys_pts)
        lot_w = max_bx - min_bx
        lot_h = max_by - min_by
        cx_lot = (min_bx + max_bx) / 2.0
        cy_lot = (min_by + max_by) / 2.0

        # ── 4.A Plan de situation (1/5000) ──
        sit_x = ox + 6.0
        sit_y = content_top
        sit_w = 75.0
        sit_h = 60.0

        # Cadre rectangulaire situation
        msp.add_lwpolyline(
            [(sit_x, sit_y), (sit_x + sit_w, sit_y),
             (sit_x + sit_w, sit_y - sit_h), (sit_x, sit_y - sit_h)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )

        # Bandeau échelle sous situation
        scale_box_h = 6.0
        msp.add_lwpolyline(
            [(sit_x, sit_y - sit_h), (sit_x + sit_w, sit_y - sit_h),
             (sit_x + sit_w, sit_y - sit_h - scale_box_h), (sit_x, sit_y - sit_h - scale_box_h)],
            close=True, dxfattribs={'layer': 'CADRE'}
        )
        scale_5000 = full_data.get('scale_5000', 5000) if isinstance(full_data, dict) else 5000
        echelle_1 = full_data.get('echelle_1', f"1/{scale_5000}") if isinstance(full_data, dict) else f"1/{scale_5000}"
        add_text(f"ECHELLE : {echelle_1}", sit_x + sit_w / 2.0,
                 sit_y - sit_h - 4.2, t_small, align='CENTER', layer='TEXTES_BOLD')

        # Transformation monde -> situation (échelle 1/5000 ou cadrage)
        sit_paper_scale = 1000.0 / scale_5000  # mm par mètre
        sit_cx = sit_x + sit_w / 2.0
        sit_cy = sit_y - sit_h / 2.0

        def world_to_sit(wx, wy):
            return (
                sit_cx + (wx - cx_lot) * sit_paper_scale,
                sit_cy + (wy - cy_lot) * sit_paper_scale
            )

        def in_sit_box(px, py, margin=1.0):
            return (sit_x - margin <= px <= sit_x + sit_w + margin) and (sit_y - sit_h - margin <= py <= sit_y + margin)

        # NOTE: Les calques d'arrière-plan (background_layers) sont retirés de la projection 1/5000.

        # Dessiner tous les lots environnants en situation
        all_ilots = full_data.get('all_ilots', {}) if isinstance(full_data, dict) else {}
        if all_ilots:
            for i_name, ilot_data in all_ilots.items():
                for l_name, lot_info in ilot_data.get('lots', {}).items():
                    l_bornes = lot_info.get('bornes', [])
                    if len(l_bornes) >= 3:
                        s_pts = [world_to_sit(p[0], p[1]) for p in l_bornes]
                        if any(in_sit_box(p[0], p[1]) for p in s_pts):
                            msp.add_lwpolyline(s_pts, close=True, dxfattribs={'layer': 'VOISINS'})
                            lcx = sum(p[0] for p in s_pts) / len(s_pts)
                            lcy = sum(p[1] for p in s_pts) / len(s_pts)
                            if in_sit_box(lcx, lcy, margin=0.0):
                                if math.hypot(lcx - sit_cx, lcy - sit_cy) > 3.0:
                                    add_text(str(l_name), lcx, lcy, h=1.5, align='CENTER', layer='TEXTES')
        elif voisins:
            for nom_v, pts_v in voisins.items():
                if pts_v and len(pts_v) >= 3:
                    s_pts = [world_to_sit(p[0], p[1]) for p in pts_v]
                    if any(in_sit_box(p[0], p[1]) for p in s_pts):
                        msp.add_lwpolyline(s_pts, close=True, dxfattribs={'layer': 'VOISINS', 'linetype': 'DASHED'})
                        vcx = sum(p[0] for p in s_pts) / len(s_pts)
                        vcy = sum(p[1] for p in s_pts) / len(s_pts)
                        if in_sit_box(vcx, vcy, margin=0.0):
                            add_text(str(nom_v), vcx, vcy, h=1.5, align='CENTER', layer='TEXTES')

        # Lot principal rempli (Hatch solide)
        sit_lot_pts = [world_to_sit(p[0], p[1]) for p in points]
        try:
            hatch = msp.add_hatch(color=7, dxfattribs={'layer': 'PARCELLE_FILL'})
            hatch.paths.add_polyline_path(
                [(p[0], p[1]) for p in sit_lot_pts],
                is_closed=True
            )
        except Exception:
            pass
        msp.add_lwpolyline(sit_lot_pts, close=True, dxfattribs={'layer': 'PARCELLE'})

        # ── 4.B Flèche NORD cadastrale (entre situation et NOTA) ──
        north_cx = sit_x + sit_w + 14.0
        north_top = content_top - 6.0
        needle_len = 22.0
        needle_w = 3.5

        # Pointe gauche remplie noire
        try:
            hatch_n = msp.add_hatch(color=7, dxfattribs={'layer': 'CADRE'})
            hatch_n.paths.add_polyline_path([
                (north_cx, north_top),
                (north_cx - needle_w, north_top - needle_len),
                (north_cx, north_top - needle_len + 4.0),
            ], is_closed=True)
        except Exception:
            pass

        # Demi-aiguille droite contour
        msp.add_lwpolyline([
            (north_cx, north_top),
            (north_cx + needle_w, north_top - needle_len),
            (north_cx, north_top - needle_len + 4.0),
            (north_cx, north_top)
        ], close=True, dxfattribs={'layer': 'CADRE'})

        # Tige verticale
        msp.add_line((north_cx, north_top - needle_len + 4.0),
                     (north_cx, north_top - needle_len - 6.0),
                     dxfattribs={'layer': 'CADRE'})

        # Lettre N au-dessus
        add_text("N", north_cx, north_top + 2.0, h=t_bold, align='CENTER', layer='TEXTES_BOLD')

        # ── 4.C Bloc NOTA & Contenance ──
        nota_cx = north_cx + (sep_x - north_cx) / 2.0
        nota_y = content_top - 12.0
        add_text("NOTA: Toute reproduction officielle doit obligatoirement",
                 nota_cx, nota_y, t_small, align='CENTER')
        add_text("comporter le timbre sec du Service du Cadastre",
                 nota_cx, nota_y - 4.5, t_small, align='CENTER')

        # Contenance formatée
        surface_str = full_data.get('surface', '0.0') if isinstance(full_data, dict) else '0.0'
        try:
            surface_val = float(str(surface_str).replace("m²", "").replace(" ", "").replace(",", ".").strip())
        except (ValueError, TypeError):
            surface_val = 0.0

        ha = int(surface_val // 10000)
        a = int((surface_val % 10000) // 100)
        ca = int(surface_val % 100)
        contenance_str = f"{ha:02d} ha {a:02d} a {ca:02d} ca"

        add_text(f"Contenance:   {contenance_str}",
                 nota_cx, nota_y - 18.0, t_normal, align='CENTER', layer='TEXTES_BOLD')

        # ══════════════════════════════════════════════════════
        # 5. PLAN DE MASSE (1/500) — CROQUIS SANS CADRE
        # ══════════════════════════════════════════════════════
        masse_paper_scale = 1000.0 / scale_500  # 2.0 mm / m à 1/500
        lot_w_paper = lot_w * masse_paper_scale
        lot_h_paper = lot_h * masse_paper_scale

        # Positionnement dans le panneau gauche (milieu entre footer et bande situation)
        masse_cx = ox + sep_x * 0.46
        masse_cy = footer_top + (content_top - sit_h - scale_box_h - footer_top) / 2.0

        def world_to_masse(wx, wy):
            return (
                masse_cx + (wx - cx_lot) * masse_paper_scale,
                masse_cy + (wy - cy_lot) * masse_paper_scale
            )

        # ── 5.A Voisins (UNIQUEMENT les 2 plus proches) ──
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
            # Label voisin centré
            vc_x = sum(p[0] for p in pts_v) / len(pts_v)
            vc_y = sum(p[1] for p in pts_v) / len(pts_v)
            vmx, vmy = world_to_masse(vc_x, vc_y)
            add_text(nom_v, vmx, vmy, t_small, align='CENTER')

        # ── 5.B Carroyage cadastral (Croix + aux coordonnées rondes) ──
        # Déterminer la zone de coordonnées couverte
        all_masse_x = list(xs_pts)
        all_masse_y = list(ys_pts)
        for pts_v in masse_voisins.values():
            all_masse_x.extend(p[0] for p in pts_v)
            all_masse_y.extend(p[1] for p in pts_v)

        min_mx, max_mx = min(all_masse_x), max(all_masse_x)
        min_my, max_my = min(all_masse_y), max(all_masse_y)
        grid_step = 50.0 if max(max_mx - min_mx, max_my - min_my) >= 50.0 else 25.0

        x_grid_start = math.floor((min_mx - 20.0) / grid_step) * grid_step
        x_grid_end = math.ceil((max_mx + 20.0) / grid_step) * grid_step
        y_grid_start = math.floor((min_my - 20.0) / grid_step) * grid_step
        y_grid_end = math.ceil((max_my + 20.0) / grid_step) * grid_step

        masse_top_limit = content_top - sit_h - scale_box_h - 4.0
        masse_bot_limit = footer_top + 4.0

        gx = x_grid_start
        while gx <= x_grid_end:
            gy = y_grid_start
            while gy <= y_grid_end:
                pmx, pmy = world_to_masse(gx, gy)
                # Vérifier que la croix est dans la zone du plan de masse
                if (ox + 8.0 <= pmx <= sep_x - 8.0) and (masse_bot_limit <= pmy <= masse_top_limit):
                    # Tracer petite croix (+)
                    cr_len = 1.8
                    msp.add_line((pmx - cr_len, pmy), (pmx + cr_len, pmy),
                                 dxfattribs={'layer': 'CARROYAGE'})
                    msp.add_line((pmx, pmy - cr_len), (pmx, pmy + cr_len),
                                 dxfattribs={'layer': 'CARROYAGE'})
                gy += grid_step
            gx += grid_step

        # ── 5.C Lot principal & Bornes ──
        masse_lot_pts = [world_to_masse(p[0], p[1]) for p in points]
        msp.add_lwpolyline(masse_lot_pts, close=True, dxfattribs={'layer': 'PARCELLE'})

        for i, p in enumerate(points):
            mx, my = world_to_masse(p[0], p[1])
            # Cercle de borne
            msp.add_circle((mx, my), radius=0.8, dxfattribs={'layer': 'BORNES'})

            # Libellé de borne poussé vers l'extérieur du polygone
            dx = mx - masse_cx
            dy = my - masse_cy
            norm = math.hypot(dx, dy) or 1.0
            lbl_x = mx + (dx / norm) * 2.8
            lbl_y = my + (dy / norm) * 2.8
            add_text(f"B{i + 1}", lbl_x, lbl_y, t_small, layer='BORNES', align='CENTER')

            # Cotation sur le segment vers la borne suivante
            p2 = points[(i + 1) % len(points)]
            dist = math.hypot(p2[0] - p[0], p2[1] - p[1])
            mid_wx = (p[0] + p2[0]) / 2.0
            mid_wy = (p[1] + p2[1]) / 2.0
            mid_mx, mid_my = world_to_masse(mid_wx, mid_wy)

            # Angle du texte
            angle = math.degrees(math.atan2(p2[1] - p[1], p2[0] - p[0]))
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180

            perp_angle = math.radians(angle + 90)
            offset = 1.8
            add_text(
                f"{dist:.3f}",
                mid_mx + offset * math.cos(perp_angle),
                mid_my + offset * math.sin(perp_angle),
                h=2.0, layer='TEXTES', align='CENTER', rotation=angle
            )

        # ══════════════════════════════════════════════════════
        # 6. PANNEAU DROIT — TABLEAU DES COORDONNÉES
        # ══════════════════════════════════════════════════════
        right_panel_w = W - sep_x   # 176.4 mm

        # Titre centré
        title_cx = sep_x + right_panel_w / 2.0
        title_y = oy + H - 12.0
        add_text("TABLEAU DES COORDONNEES", title_cx, title_y, t_title,
                 align='CENTER', layer='TEXTES_BOLD')
        add_text("ITRF96-1998,2 /Ellipsoïde du WGS 84 UTM FUSEAU 30N",
                 title_cx, title_y - 6.0, t_small, align='CENTER')

        # Structure du tableau : 5 colonnes
        # BORNES | X | Y | ANGLES | DISTANCES
        col_widths = [18.0, 34.0, 34.0, 27.0, 27.0]
        total_table_w = sum(col_widths)  # 140.0 mm
        row_h = 7.0

        # Centrage du tableau dans le panneau droit
        tab_x = sep_x + (right_panel_w - total_table_w) / 2.0
        tab_start_y = title_y - 14.0

        def draw_cell(x, y, w, h, text="", text_h=t_small, bold=False):
            # Contour cellule
            msp.add_lwpolyline(
                [(x, y), (x + w, y), (x + w, y - h), (x, y - h)],
                close=True, dxfattribs={'layer': 'TABLEAU'}
            )
            if text:
                layer = 'TEXTES_BOLD' if bold else 'TEXTES'
                add_text(str(text), x + w / 2.0, y - h / 2.0, text_h,
                         layer=layer, align='MIDDLE_CENTER')

        # Ligne 0 : En-tête du tableau
        cur_cell_x = tab_x
        header_cols = ["BORNES", "X", "Y", "ANGLES", "DISTANCES"]
        for idx, col_name in enumerate(header_cols):
            draw_cell(cur_cell_x, tab_start_y, col_widths[idx], row_h,
                      col_name, t_small, bold=True)
            cur_cell_x += col_widths[idx]

        # Données des lignes (conforme au standard topographique cadastral)
        # Ligne 1 : B1 | X1 | Y1 | 100.000 | (vide)
        # Ligne 2 : B2 | X2 | Y2 | 100.000 | dist(B1->B2)
        # Ligne 3 : B3 | X3 | Y3 | 100.000 | dist(B2->B3)
        # ...
        # Ligne N+1 : B1 | (vide) | (vide) | (vide) | dist(BN->B1)
        cy_row = tab_start_y - row_h
        n_pts = len(points)

        for i in range(n_pts):
            p_cur = points[i]
            nom = f"B{i + 1}"
            x_str = f"{p_cur[0]:.3f}"
            y_str = f"{p_cur[1]:.3f}"
            ang_str = "100.000"

            if i == 0:
                dist_str = ""
            else:
                p_prev = points[i - 1]
                d = math.hypot(p_cur[0] - p_prev[0], p_cur[1] - p_prev[1])
                dist_str = f"{d:.3f}"

            row_vals = [nom, x_str, y_str, ang_str, dist_str]
            cx_c = tab_x
            for c_idx, val_str in enumerate(row_vals):
                draw_cell(cx_c, cy_row, col_widths[c_idx], row_h, val_str, t_small, bold=(c_idx == 0))
                cx_c += col_widths[c_idx]

            cy_row -= row_h

        # Ligne de fermeture : retour sur B1
        last_dist = math.hypot(points[0][0] - points[-1][0], points[0][1] - points[-1][1])
        closing_vals = ["B1", "", "", "", f"{last_dist:.3f}"]
        cx_c = tab_x
        for c_idx, val_str in enumerate(closing_vals):
            draw_cell(cx_c, cy_row, col_widths[c_idx], row_h, val_str, t_small, bold=(c_idx == 0))
            cx_c += col_widths[c_idx]

        # ══════════════════════════════════════════════════════
        # 7. VIEWPORT PAR DÉFAUT (centré sur la feuille A3)
        # ══════════════════════════════════════════════════════
        try:
            doc.set_modelspace_vport(
                center=(W / 2.0, H / 2.0),
                height=H * 1.05
            )
        except Exception:
            pass

        # ── Sauvegarde du fichier DXF ──
        output_path = filename if os.path.isabs(filename) else os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
