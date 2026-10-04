import os
import base64
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
import math
from io import BytesIO
# pyrefly: ignore [missing-import]
from jinja2 import Template

class PDFGenerator:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir
        
        self.html_template = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {
                    font-family: 'Helvetica';
                    font-weight: normal;
                    font-style: normal;
                }
                body { 
                    font-family: 'Helvetica', 'Arial', sans-serif; 
                    margin: 0;
                    padding: 0;
                }
                .page-break { page-break-before: always; }
                
                /* =======================
                   PAGE 1 - GARDE
                   ======================= */
                @page garde_page { 
                    size: A4 portrait;
                    margin: 1cm;
                }
                .page-border {
                    border: 1px solid black;
                    padding: 40px;
                    height: 1000px; /* Force page height approximation */
                    box-sizing: border-box;
                    position: relative;
                }
                
                .header-flex {
                    display: flex;
                    justify-content: space-between;
                    font-size: 8pt;
                    font-weight: bold;
                }
                .header-flex div {
                    text-align: center;
                    line-height: 1.6;
                }
                
                .garde-title-box {
                    border: 3px solid black;
                    padding: 30px;
                    text-align: center;
                    margin: 80px 10%;
                    box-shadow: 2px 2px 0px black; /* simulate outline if needed */
                }
                .garde-title-box h1 {
                    font-size: 40pt;
                    font-weight: bold;
                    margin: 0;
                    letter-spacing: 2px;
                    color: black;
                }
                
                .garde-subtitle {
                    text-align: center;
                    font-size: 20pt;
                    font-weight: bold;
                    text-decoration: underline;
                    text-decoration-thickness: 1px;
                    text-underline-offset: 4px;
                    margin: 60px 0;
                }
                
                .garde-info {
                    text-align: center;
                    font-size: 12pt;
                    font-weight: bold;
                    line-height: 2.5;
                    margin-top: 50px;
                }
                
                .bottom-left-ref {
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    font-size: 6pt;
                }
                
                /* =======================
                   PAGE 2 - RAPPORT
                   ======================= */
                .rapport-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    font-weight: bold;
                    margin-bottom: 40px;
                }
                .rapport-header div {
                    text-align: center;
                    line-height: 1.2;
                }
                
                .rapport-title {
                    text-align: center;
                    font-size: 18pt;
                    font-weight: bold;
                    text-decoration: underline;
                    text-decoration-thickness: 3px;
                    text-underline-offset: 4px;
                    margin-bottom: 40px;
                }
                
                .rapport-details {
                    display: flex;
                    justify-content: space-between;
                    font-size: 11pt;
                    font-weight: bold;
                    line-height: 1.8;
                    margin-bottom: 30px;
                }
                
                .rapport-table {
                    width: 60%;
                    margin: 30px auto;
                    border-collapse: collapse;
                }
                .rapport-table th, .rapport-table td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: center;
                    font-size: 12pt;
                    font-weight: bold;
                }
                
                .calcul-table {
                    width: 90%;
                    margin: 0 auto 20px auto;
                    border-collapse: collapse;
                }
                .calcul-table th, .calcul-table td {
                    border: 1px solid black;
                    padding: 10px 8px;
                    text-align: center;
                    font-size: 10pt;
                }
                .calcul-table th { font-weight: bold; }
                
                /* =======================
                   PAGE 4 - PLAN EXTRAIT
                   ======================= */
                @page plan_page {
                    size: A3 landscape;
                    margin: 0.5cm;
                }
                .plan-container {
                    width: 100%;
                    height: 285mm;
                    border: 1px solid black;
                    border-collapse: collapse;
                    page-break-inside: avoid;
                    break-inside: avoid;
                    font-family: 'Times New Roman', 'Liberation Serif', 'Nimbus Roman', Times, serif;
                }
                .plan-container td {
                    vertical-align: top;
                    padding: 6px 10px;
                }
                .plan-left {
                    width: 58%;
                    border-right: 1px solid black;
                }
                .plan-right {
                    width: 42%;
                }
                
                .plan-header {
                    width: 100%;
                    font-size: 8.5pt;
                    border-bottom: 1px solid black;
                    margin-bottom: 8px;
                    padding-bottom: 6px;
                }
                .plan-header td {
                    vertical-align: top;
                    border: none;
                    padding: 0 4px;
                }
                .plan-header-col1 { width: 24%; line-height: 1.4; text-align: center; }
                .plan-header-col2 { width: 20%; line-height: 1.5; }
                .plan-header-col3 { width: 56%; line-height: 1.4; }
                
                .plan-header-col2 span { display: inline-block; width: 65px; }
                
                .plan-content {
                    width: 100%;
                }
                
                .situation-row {
                    display: table;
                    width: 100%;
                    margin-bottom: 8px;
                }
                .situation-col1 {
                    display: table-cell;
                    width: 40%;
                    vertical-align: top;
                }
                .situation-arrow {
                    display: table-cell;
                    width: 8%;
                    vertical-align: middle;
                    text-align: center;
                }
                .situation-col2 {
                    display: table-cell;
                    width: 52%;
                    vertical-align: middle;
                    padding-left: 10px;
                    font-size: 9.5pt;
                }
                
                .map-situation {
                    width: 100%;
                    border: 1px solid black;
                    background: white;
                    text-align: center;
                    overflow: hidden;
                }
                .map-situation img {
                    width: 100%;
                    height: 185px;
                    object-fit: contain;
                    display: block;
                    margin: 0 auto;
                }
                .scale-box {
                    border-top: 1px solid black;
                    text-align: center;
                    font-size: 9pt;
                    font-weight: bold;
                    background: white;
                    padding: 3px 0;
                }
                
                .map-masse {
                    width: 100%;
                    text-align: center;
                    margin: 2px 0 0 0;
                }
                .map-masse img {
                    max-width: 100%;
                    max-height: 490px;
                    height: auto;
                    object-fit: contain;
                    display: block;
                    margin: 0 auto;
                }
                
                .plan-footer {
                    width: 100%;
                    font-size: 7.5pt;
                    margin-top: 2px;
                    line-height: 1.3;
                }
                .plan-footer td {
                    vertical-align: bottom;
                    border: none;
                }
                .plan-footer-left { width: 38%; line-height: 1.4; }
                .plan-footer-center { width: 24%; text-align: center; font-weight: bold; font-size: 9.5pt; }
                .plan-footer-right { width: 38%; text-align: center; line-height: 1.3; }
                
                .coord-title {
                    text-align: center;
                    font-size: 14pt;
                    font-weight: bold;
                    margin: 15px 0 4px 0;
                }
                .coord-subtitle {
                    text-align: center;
                    font-size: 8.5pt;
                    margin-bottom: 15px;
                }
                .table-coord-main {
                    width: 82%;
                    margin: 0 auto;
                    border-collapse: collapse;
                    font-size: 8.5pt;
                }
                .table-coord-main th, .table-coord-main td {
                    border: 1px solid black;
                    padding: 6px 4px;
                    text-align: center;
                    vertical-align: middle;
                }
                .table-coord-main th {
                    font-weight: bold;
                    background-color: #fafafa;
                }
            </style>
        </head>
        <body>
        
            <!-- PAGE 1: Garde -->
            <div style="page: garde_page;">
                <div class="page-border">
                    <div class="header-flex">
                        <div>
                            MINISTERE DES FINANCES ET DU BUDGET<br><br>
                            DIRECTION GENERALE DES IMPOTS<br><br>
                            DIRECTION DU CADASTRE
                        </div>
                        <div>
                            REPUBLIQUE DE COTE D'IVOIRE<br><br>
                            Union – Discipline - Travail
                        </div>
                    </div>
                    
                    <div class="garde-title-box">
                        <h1>DOSSIER DE<br>CALCULS</h1>
                    </div>
                    
                    <div class="garde-subtitle">
                        <span style="border-bottom: 1px solid black; padding-bottom: 2px;">
                            DOSSIER TECHNIQUE DE MORCELLEMENT
                        </span>
                    </div>
                    
                    <div class="garde-info">
                        CENTRE : {{ centre }}<br><br>
                        Ilot : {{ ilot }} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Lot : {{ lot }}<br><br>
                        Demandeur : {{ demandeur }}
                    </div>
                    
                    <div class="bottom-left-ref">N°:{{ dossier }}</div>
                </div>
            </div>
            
            <!-- PAGE 2: Rapport -->
            <div style="page: garde_page;">
                <div class="page-border">
                    <div class="rapport-header">
                        <div>
                            MINISTERE DES FINANCES ET DU BUDGET<br>
                            DIRECTION DES IMPOTS<br>
                            <span style="font-size: 11pt;">DIRECTION DU CADASTRE</span>
                        </div>
                        <div>REPUBLIQUE DE COTE D'IVOIRE</div>
                    </div>
                    
                    <div class="rapport-title">
                        RAPPORT DU GEOMETRE
                    </div>
                    
                    <div class="rapport-details">
                        <div>
                            Livre Foncier : {{ livre_foncier }}<br>
                            Lotissement : {{ lotissement }}<br>
                            Morcellement de TF : {{ tf }}
                        </div>
                        <div>
                            Centre : {{ centre }}<br>
                            Ilot : {{ ilot }} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Lot : {{ lot }}<br>
                            Section : {{ section }}
                        </div>
                    </div>
                    
                    <div style="font-size: 11pt; line-height: 1.5; margin-bottom: 30px;">
                        Date de bornage fait sur le terrain par le Géomètre : Antérieure<br>
                        Date de consultation des documents cadastraux : {{ date_consultation }}
                    </div>
                    
                    <div style="font-size: 11pt; line-height: 1.5; margin-bottom: 30px;">
                        <strong>DOCUMENTS DE BASE UTILISES</strong><br>
                        CADASTRE :<br>
                        N° de la section du plan : {{ section }}<br>
                        N° du dossier : {{ dossier }}<br>
                        GEOMETRE PRIVE :<br>
                        Nom du cabinet : {{ cabinet_nom }}
                    </div>
                    
                    <div style="text-align: center; font-style: italic; font-weight: bold; font-size: 10pt;">
                        LES COORDONNEES DOIVENT ETRE CELLES DU SYSTEME WGS 84 UTM FUSEAU 30N<br>
                        COORDONNEES DES SOMMETS DE L'ILOT UTILISE OU POLYGONATION
                    </div>
                    
                    <h4 style="text-align: center; font-style: italic; font-size: 14pt; margin: 15px 0;">ILOT {{ ilot }}</h4>
                    
                    <table class="rapport-table">
                        <tr><th>Bornes</th><th>X</th><th>Y</th></tr>
                        {% for borne in bornes %}
                        <tr>
                            <td>B{{ loop.index }}</td>
                            <td>{{ "%.3f"|format(borne[0]) }}</td>
                            <td>{{ "%.3f"|format(borne[1]) }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    
                    <div class="bottom-left-ref">N°:{{ dossier }}</div>
                </div>
            </div>
            
            <!-- PAGE 3: Calcul Retour -->
            <div style="page: garde_page;">
                <div class="page-border">
                    <div class="rapport-header">
                        <div>
                            REPUBLIQUE DE CÔTE D'IVOIRE<br>
                            MINISTERE DES FINANCES<br>ET DU BUDGET<br>
                            DIRECTION DES IMPOTS<br>
                            <span style="font-size: 11pt;">DIRECTION DU CADASTRE</span>
                        </div>
                        <div style="text-align: left;">
                            Centre : <strong>{{ centre }}</strong><br>
                            Ilot : <strong>{{ ilot }}</strong> &nbsp;&nbsp;&nbsp;&nbsp; Lot : <strong>{{ lot }}</strong><br>
                            Morcellement du TF : <strong>{{ tf }}</strong><br>
                            Section : <strong>{{ section }}</strong><br>
                            Livre Foncier : <strong>{{ livre_foncier }}</strong><br>
                            Cédant : <strong>ETAT DE CI</strong><br>
                            Demandeur : <strong>{{ demandeur }}</strong>
                        </div>
                    </div>
                    
                    <div class="rapport-title" style="margin-top: 40px; margin-bottom: 30px; font-size: 16pt; line-height: 1.5;">
                        TABLEAU DE COORDONNEES<br>
                        <span style="font-style: italic; font-size: 14pt;">CALCUL RETOUR ET CALCUL DE SURFACE</span>
                    </div>
                    
                    <table class="calcul-table">
                        <tr>
                            <th colspan="4">CALCUL DE SURFACE</th>
                            <th colspan="3"></th>
                        </tr>
                        <tr>
                            <td colspan="2" style="font-weight: bold;">ILOT : {{ ilot }}</td>
                            <td style="font-weight: bold;">LOT : {{ lot }}</td>
                            <td style="font-weight: bold;">SURFACE : {{ surface }}</td>
                            <td colspan="3" style="font-weight: bold;">{{ surface_ha_a_ca_formatted_text }}</td>
                        </tr>
                        <tr>
                            <th colspan="4">COORDONNEES</th>
                            <th colspan="3">CALCUL RETOUR</th>
                        </tr>
                        <tr>
                            <th>POINT</th>
                            <th>BORNE</th>
                            <th>X</th>
                            <th>Y</th>
                            <th>ANGLES</th>
                            <th>DISTANCES</th>
                            <th>GISEMENTS</th>
                        </tr>
                        {% for b in bornes_calc %}
                        <tr>
                            <td>{{ b.point if b.point else "" }}</td>
                            <td>{{ b.nom }}</td>
                            <td>{% if b.x %}<strong>{{ "%.3f"|format(b.x) }}</strong>{% endif %}</td>
                            <td>{% if b.y %}<strong>{{ "%.3f"|format(b.y) }}</strong>{% endif %}</td>
                            <td>{% if b.angle %}{{ "%.3f"|format(b.angle) }}{% endif %}</td>
                            <td>{% if b.dist %}{{ "%.3f"|format(b.dist) }}{% endif %}</td>
                            <td>{% if b.gis %}{{ "%.3f"|format(b.gis) }}{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            </div>
            
            <!-- PAGE 4: Plan Extrait (Landscape) -->
            <div style="page: plan_page; page-break-before: always; break-before: always;">
                <table class="plan-container">
                    <tr>
                    <td class="plan-left">
                        <table class="plan-header">
                            <tr>
                            <td class="plan-header-col1">
                                Republique de Côte d'Ivoire<br>
                                Ministère des Finances et du Budget<br>
                                Direction du Cadastre<br>
                                Bureau de {{ centre }}
                            </td>
                            <td class="plan-header-col2">
                                <span>T.F.No:</span> {{ tf }}<br>
                                <span>Section:</span> {{ section }}<br>
                                <span>No du Plan:</span> ......
                            </td>
                            <td class="plan-header-col3">
                                Centre: <strong>{{ centre }}</strong><br>
                                Ilot: <strong>{{ ilot }}</strong> &nbsp;&nbsp;&nbsp;&nbsp; Lot: <strong>{{ lot }}</strong> &nbsp;&nbsp;&nbsp;&nbsp; Parcelle: ......<br>
                                Morcellement du TF: <strong>{{ tf }}</strong><br>
                                Fusion des TF.....: ......<br>
                                Requisition ......: ......<br>
                                Livre Foncier de : <strong>{{ livre_foncier }}</strong><br>
                                Cédant: <strong>ETAT DE CI</strong><br>
                                Demandeur: <strong>{{ demandeur }}</strong>
                            </td>
                            </tr>
                        </table>
                        
                        <div class="plan-content">
                            <div class="situation-row">
                                <div class="situation-col1">
                                    <div class="map-situation">
                                        <img src="data:image/png;base64,{{ img_situation }}" alt="Situation">
                                        <div class="scale-box">ECHELLE : {{ echelle_1 }}</div>
                                    </div>
                                </div>
                                <div class="situation-arrow">
                                    <svg width="20" height="52" viewBox="0 0 20 52">
                                        <polygon points="10,2 4,22 10,18" fill="black" />
                                        <polygon points="10,2 16,22 10,18" fill="white" stroke="black" stroke-width="0.8" />
                                        <line x1="10" y1="18" x2="10" y2="36" stroke="black" stroke-width="1.2" />
                                        <text x="10" y="48" font-family="'Times New Roman', serif" font-size="11" font-weight="bold" text-anchor="middle">N</text>
                                    </svg>
                                </div>
                                <div class="situation-col2">
                                    <div style="font-size: 8.5pt; text-align: center; margin-bottom: 22px;">
                                        NOTA: Toute reproduction officielle doit obligatoirement<br>comporter le timbre sec du Service du Cadastre
                                    </div>
                                    <div style="text-align: center; font-size: 10pt;">
                                        Contenance: &nbsp;&nbsp; <strong>{{ surface_ha_a_ca_formatted }}</strong>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="map-masse">
                                <img src="data:image/png;base64,{{ img_masse }}" alt="Masse">
                            </div>
                        </div>
                        
                        <table class="plan-footer">
                            <tr>
                            <td class="plan-footer-left">
                                Copie certifiée conforme<br>
                                {{ centre.capitalize() if centre else '......' }}, le :<br>
                                Le Géomètre Assermenté du Cadastre<br><br>
                                <span style="font-size: 7pt;">N°: {{ dossier }}</span>
                            </td>
                            <td class="plan-footer-center">
                                ECHELLE : {{ echelle_2 }}
                            </td>
                            <td class="plan-footer-right">
                                Levé et Dressé par <strong>{{ cabinet_nom }}</strong><br>
                                {{ cabinet_adresse }}<br>
                                {{ centre.upper() if centre else '......' }}, le {{ date_consultation }}<br><br>
                                <strong>{{ signataire_nom }}</strong><br>
                                {{ signataire_titre }}
                            </td>
                            </tr>
                        </table>
                    </td>
                    
                    <td class="plan-right">
                        <div class="coord-title">TABLEAU DES COORDONNEES</div>
                        <div class="coord-subtitle">ITRF96-1998.2 /Ellipsoïde du WGS 84 UTM FUSEAU 30N</div>
                        
                        <table class="table-coord-main">
                            <tr>
                                <th style="width: 16%;">BORNES</th>
                                <th style="width: 24%;">X</th>
                                <th style="width: 24%;">Y</th>
                                <th style="width: 18%;">ANGLES</th>
                                <th style="width: 18%;">DISTANCES</th>
                            </tr>
                            {% for b in bornes_calc %}
                            <tr>
                                <td><strong>{{ b.nom }}</strong></td>
                                <td>{{ "%.3f"|format(b.x) if b.x is not none else "" }}</td>
                                <td>{{ "%.3f"|format(b.y) if b.y is not none else "" }}</td>
                                <td>{{ "%.3f"|format(b.angle) if b.angle is not none else "" }}</td>
                                <td>{{ "%.3f"|format(b.dist) if b.dist is not none else "" }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </td>
                    </tr>
                </table>
            </div>
            
        </body>
        </html>
        """
        
    def render_plot_to_base64(self, bornes, voisins=None, zoom_out=False, show_grid_ticks=True, scale=5000, all_ilots=None, background_layers=None):
        """Génère une image PNG en base64 du plan.
        
        zoom_out=True  → Plan de situation (1/5000): vue large, projette l'ensemble du lotissement
                         et remplit le lot sélectionné en noir
        zoom_out=False → Plan de masse (1/500): vue détaillée avec bornes, distances,
                         et coordonnées sur les axes
        """
        if not bornes:
            return ""

        # ── Tailles de figure adaptées au format A3 ──
        if zoom_out:
            # Aspect ratio 95mm / 70mm = 1.357
            fig = plt.figure(figsize=(4.5, 3.315))
            ax = fig.add_axes([0, 0, 1, 1])
        else:
            fig, ax = plt.subplots(figsize=(8.5, 5.8))

        # ── Calculer la bounding box et le centroïde du lot principal ──
        xs_lot = [b[0] for b in bornes]
        ys_lot = [b[1] for b in bornes]
        min_x_lot, max_x_lot = min(xs_lot), max(xs_lot)
        min_y_lot, max_y_lot = min(ys_lot), max(ys_lot)
        lot_width = max_x_lot - min_x_lot
        lot_height = max_y_lot - min_y_lot
        cx_lot = (min_x_lot + max_x_lot) / 2.0
        cy_lot = (min_y_lot + max_y_lot) / 2.0

        if zoom_out:
            # ── 1. Plan de situation (1/5000) ──
            # Le cadre sur papier mesure environ 95mm x 70mm (hauteur 185px).
            # À l'échelle 1/5000 -> 0.095 * 5000 = 475m de large, 0.070 * 5000 = 350m de haut sur le terrain.
            w_view = 0.095 * scale
            h_view = 0.070 * scale
            ax_min, ax_max = cx_lot - w_view / 2.0, cx_lot + w_view / 2.0
            ay_min, ay_max = cy_lot - h_view / 2.0, cy_lot + h_view / 2.0

            # NOTE: Les calques d'arrière-plan (background_layers) sont retirés de la projection 1/5000.

            # ── Dessiner tous les lots du lotissement ──
            if all_ilots:
                for i_name, ilot_data in all_ilots.items():
                    for l_name, lot_info in ilot_data.get('lots', {}).items():
                        l_bornes = lot_info.get('bornes', [])
                        if len(l_bornes) >= 3:
                            lx = [p[0] for p in l_bornes] + [l_bornes[0][0]]
                            ly = [p[1] for p in l_bornes] + [l_bornes[0][1]]
                            ax.plot(lx, ly, 'k-', linewidth=0.5, alpha=0.75, zorder=2)
                            
                            # Afficher le numéro de lot si le lot est dans le champ de vision
                            lcx = sum(p[0] for p in l_bornes) / len(l_bornes)
                            lcy = sum(p[1] for p in l_bornes) / len(l_bornes)
                            if (ax_min <= lcx <= ax_max) and (ay_min <= lcy <= ay_max):
                                # Ne pas afficher le texte par-dessus le lot principal noir
                                if math.hypot(lcx - cx_lot, lcy - cy_lot) > max(lot_width, lot_height) * 0.6:
                                    ax.text(lcx, lcy, str(l_name), fontsize=4.5, ha='center', va='center',
                                            color='#333333', alpha=0.85, zorder=3)
            elif voisins:
                for nom_voisin, pts_voisin in voisins.items():
                    if len(pts_voisin) >= 3:
                        vx = [p[0] for p in pts_voisin] + [pts_voisin[0][0]]
                        vy = [p[1] for p in pts_voisin] + [pts_voisin[0][1]]
                        ax.plot(vx, vy, 'k-', linewidth=0.5, alpha=0.75, zorder=2)
                        vcx = sum(p[0] for p in pts_voisin) / len(pts_voisin)
                        vcy = sum(p[1] for p in pts_voisin) / len(pts_voisin)
                        ax.text(vcx, vcy, str(nom_voisin), fontsize=4.5, ha='center', va='center',
                                color='#333333', zorder=3)

            # ── Dessiner le lot principal rempli en noir ──
            xs = xs_lot + [bornes[0][0]]
            ys = ys_lot + [bornes[0][1]]
            ax.plot(xs, ys, 'k-', linewidth=1.2, zorder=10)
            ax.fill(xs, ys, 'k', zorder=10)

            ax.set_xlim(ax_min, ax_max)
            ax.set_ylim(ay_min, ay_max)

        else:
            # ── 2. Plan de masse (1/500) ──
            if voisins:
                def get_neighbor_distance(pts):
                    min_d = min(math.hypot(px - lx, py - ly) for px, py in pts for lx, ly in bornes)
                    vcx = sum(p[0] for p in pts) / len(pts)
                    vcy = sum(p[1] for p in pts) / len(pts)
                    cd = math.hypot(vcx - cx_lot, vcy - cy_lot)
                    return (min_d, cd)

                valid_voisins = [
                    (name, pts) for name, pts in voisins.items()
                    if pts and len(pts) >= 3
                ]
                valid_voisins.sort(key=lambda item: get_neighbor_distance(item[1]))
                voisins = dict(valid_voisins[:2])

                for nom_voisin, pts_voisin in voisins.items():
                    if len(pts_voisin) >= 3:
                        vx = [p[0] for p in pts_voisin] + [pts_voisin[0][0]]
                        vy = [p[1] for p in pts_voisin] + [pts_voisin[0][1]]
                        ax.plot(vx, vy, 'k--', linewidth=1.2, alpha=0.65)
                        vcx = sum(p[0] for p in pts_voisin) / len(pts_voisin)
                        vcy = sum(p[1] for p in pts_voisin) / len(pts_voisin)
                        ax.text(vcx, vcy, nom_voisin, fontsize=11,
                                ha='center', va='center', alpha=0.85, fontweight='bold')

            # Dessiner le lot principal
            xs = xs_lot + [bornes[0][0]]
            ys = ys_lot + [bornes[0][1]]
            ax.plot(xs, ys, 'k-', linewidth=2.5)

            # Définir les limites du plan de masse (1/500) avec marge généreuse pour "respirer au milieu"
            all_x = list(xs_lot)
            all_y = list(ys_lot)
            if voisins:
                for pts_v in voisins.values():
                    if pts_v:
                        all_x.extend(p[0] for p in pts_v)
                        all_y.extend(p[1] for p in pts_v)
            ax_min, ax_max = min(all_x), max(all_x)
            ay_min, ay_max = min(all_y), max(all_y)
            view_w = ax_max - ax_min
            view_h = ay_max - ay_min

            # Marge confortable (35%) pour laisser le dessin respirer au milieu
            margin_w = max(view_w * 0.35, 12.0)
            margin_h = max(view_h * 0.35, 12.0)

            total_w = view_w + 2 * margin_w
            total_h = view_h + 2 * margin_h

            target_ratio = 8.5 / 5.8
            current_ratio = total_w / total_h

            if current_ratio < target_ratio:
                total_w = total_h * target_ratio
            else:
                total_h = total_w / target_ratio

            cx = (ax_min + ax_max) / 2.0
            cy = (ay_min + ay_max) / 2.0

            ax.set_xlim(cx - total_w / 2.0, cx + total_w / 2.0)
            ax.set_ylim(cy - total_h / 2.0, cy + total_h / 2.0)

            # Bornes + distances
            for i, (bx, by) in enumerate(bornes):
                ax.plot(bx, by, 'ko', markersize=5)
                ax.text(bx, by, f'  B{i+1}', fontsize=11, fontweight='bold',
                        verticalalignment='bottom')

                p1 = bornes[i]
                p2 = bornes[(i + 1) % len(bornes)]
                dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2

                angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
                if angle > 90:
                    angle -= 180
                elif angle < -90:
                    angle += 180

                ax.text(mid_x, mid_y, f"{dist:.3f}", fontsize=9.5,
                        ha='center', va='bottom', rotation=angle, fontweight='bold')

        ax.set_aspect('equal')

        # ── Grille et axes ──
        if show_grid_ticks and not zoom_out:
            import matplotlib.ticker as mticker
            ax.grid(False)
            ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=6, integer=False))
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, integer=False))
            ax.tick_params(axis='both', which='major', labelsize=8, direction='inout', length=5)
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
            xticks = ax.get_xticks()
            yticks = ax.get_yticks()
            for xt in xticks:
                for yt in yticks:
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    if xlim[0] <= xt <= xlim[1] and ylim[0] <= yt <= ylim[1]:
                        ax.plot(xt, yt, marker='+', color='grey', markersize=8, alpha=0.4)
            for xt in xticks:
                xlim = ax.get_xlim()
                if xlim[0] <= xt <= xlim[1]:
                    ax.axvline(x=xt, color='grey', linewidth=0.3, alpha=0.25, linestyle=':')
            for yt in yticks:
                ylim = ax.get_ylim()
                if ylim[0] <= yt <= ylim[1]:
                    ax.axhline(y=yt, color='grey', linewidth=0.3, alpha=0.25, linestyle=':')
        elif not show_grid_ticks and zoom_out:
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.tick_params(axis='both', length=0)
        else:
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.tick_params(axis='both', length=0)

        # ── Flèche Nord (plan de situation) ──
        if zoom_out:
            ax.annotate('N', xy=(0.92, 0.92), xycoords='axes fraction',
                        xytext=(0.92, 0.78), textcoords='axes fraction',
                        arrowprops=dict(facecolor='black', width=2.5, headwidth=10),
                        fontsize=14, ha='center', va='top', fontweight='bold')

        # ── Bordures ──
        if zoom_out:
            for spine in ax.spines.values():
                spine.set_visible(False)
        else:
            # Plan de masse: pas de cadre rectangulaire autour du dessin (comme le document de référence)
            for spine in ax.spines.values():
                spine.set_visible(False)

        if not zoom_out:
            plt.tight_layout()

        buf = BytesIO()
        if zoom_out:
            plt.savefig(buf, format='png', dpi=200, transparent=False, facecolor='white')
        else:
            plt.savefig(buf, format='png', dpi=200, transparent=True,
                        bbox_inches='tight', pad_inches=0.08)
        plt.close(fig)

        return base64.b64encode(buf.getvalue()).decode('utf-8')
        
    def _format_surface_html(self, surface_m2):
        ha = int(surface_m2 // 10000)
        a = int((surface_m2 % 10000) // 100)
        ca = int(surface_m2 % 100)
        return f"{ha:02d} <span style='font-weight:normal; font-style:italic;'>ha</span> {a:02d} <span style='font-weight:normal; font-style:italic;'>a</span> {ca:02d} <span style='font-weight:normal; font-style:italic;'>ca</span>"

    def _format_surface_text(self, surface_m2):
        ha = int(surface_m2 // 10000)
        a = int((surface_m2 % 10000) // 100)
        ca = int(surface_m2 % 100)
        return f"{ha:02d} Ha {a:02d} A {ca:02d} Ca"

    def generate_pdf(self, filename, data):
        def v(val):
            return val if val and str(val).strip() else "......"
            
        bornes = data.get("bornes", [])
        
        bornes_calc = []
        if bornes:
            for i in range(len(bornes)):
                b1 = bornes[i]
                bornes_calc.append({
                    "point": f"P{i+1}",
                    "nom": f"B{i+1}",
                    "x": b1[0],
                    "y": b1[1],
                    "angle": 100.000, 
                    "dist": None,
                    "gis": None 
                })
                
            for i in range(len(bornes)):
                b1 = bornes[i]
                b2 = bornes[(i+1)%len(bornes)]
                dx = b2[0] - b1[0]
                dy = b2[1] - b1[1]
                dist = math.sqrt(dx**2 + dy**2)
                
                # Calcul du gisement (en grades)
                gis = math.atan2(dx, dy) * 200 / math.pi
                if gis < 0: gis += 400
                
                if i == len(bornes) - 1:
                    bornes_calc.append({
                        "point": "P1",
                        "nom": "B1",
                        "x": None,
                        "y": None,
                        "angle": None,
                        "dist": dist,
                        "gis": gis
                    })
                else:
                    if i + 1 < len(bornes_calc):
                        bornes_calc[i+1]["dist"] = dist
                        bornes_calc[i+1]["gis"] = gis

        def parse_surface(surf_str):
            try:
                clean = str(surf_str).replace("m²", "").replace(" ", "").replace(",", ".").strip()
                return float(clean)
            except (ValueError, TypeError):
                return 0.0

        surface_val = parse_surface(data.get("surface", "0.0"))

        template = Template(self.html_template)
        html_out = template.render(
            demandeur=v(data.get("demandeur")),
            centre=v(data.get("centre")),
            dossier=v(data.get("dossier")),
            lotissement=v(data.get("lotissement")),
            ilot=v(data.get("ilot")),
            lot=v(data.get("lot")),
            tf=v(data.get("tf")),
            livre_foncier=v(data.get("livre_foncier")),
            section=v(data.get("section")),
            date_consultation=v(data.get("date_consultation")),
            cabinet_nom=v(data.get("cabinet_nom", "CABINET KOUAMELAN")),
            cabinet_adresse=v(data.get("cabinet_adresse")),
            signataire_nom=v(data.get("signataire_nom")),
            signataire_titre=v(data.get("signataire_titre")),
            surface=data.get("surface", "0.0"),
            surface_ha_a_ca_formatted=self._format_surface_html(surface_val),
            surface_ha_a_ca_formatted_text=self._format_surface_text(surface_val),
            bornes=bornes,
            bornes_calc=bornes_calc,
            img_situation=self.render_plot_to_base64(
                bornes,
                data.get("voisins", {}),
                zoom_out=True,
                show_grid_ticks=False,
                scale=data.get("scale_5000", 5000),
                all_ilots=data.get("all_ilots"),
                background_layers=data.get("background_layers")
            ),
            img_masse=self.render_plot_to_base64(bornes, data.get("voisins", {}), zoom_out=False, show_grid_ticks=True),
            echelle_1=v(data.get("echelle_1")),
            echelle_2=v(data.get("echelle_2"))
        )
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 1. Tenter avec WeasyPrint (si GTK/gobject est installé)
        try:
            # pyrefly: ignore [missing-import]
            from weasyprint import HTML
            HTML(string=html_out).write_pdf(output_path)
            return output_path
        except Exception as e_weasy:
            # 2. Fallback automatique avec QtWebEngine (inclus dans PySide6, fonctionne sur Windows sans GTK)
            try:
                return self._generate_pdf_with_qt(html_out, output_path)
            except Exception as e_qt:
                # 3. Secours avec QTextDocument
                try:
                    return self._generate_pdf_with_text_document(html_out, output_path)
                except Exception as e_doc:
                    raise Exception(
                        f"Impossible de générer le PDF. Erreurs :\n"
                        f"- WeasyPrint: {str(e_weasy)}\n"
                        f"- QtWebEngine: {str(e_qt)}\n"
                        f"- QTextDocument: {str(e_doc)}"
                    ) from e_doc

    def _generate_pdf_with_qt(self, html_content, output_path):
        # pyrefly: ignore [missing-import]
        from PySide6.QtWidgets import QApplication
        # pyrefly: ignore [missing-import]
        from PySide6.QtWebEngineCore import QWebEnginePage
        # pyrefly: ignore [missing-import]
        from PySide6.QtCore import QEventLoop
        import os

        app = QApplication.instance()
        if not app:
            app = QApplication([])

        page = QWebEnginePage()
        page.setHtml(html_content)

        loop = QEventLoop()
        page.loadFinished.connect(loop.quit)
        loop.exec()

        pdf_loop = QEventLoop()
        result = {"success": False}

        def on_pdf_finished(path, success):
            result["success"] = success
            pdf_loop.quit()

        page.pdfPrintingFinished.connect(on_pdf_finished)
        page.printToPdf(output_path)
        pdf_loop.exec()

        if not result["success"] or not os.path.exists(output_path):
            raise Exception("La génération du PDF via QtWebEngine a échoué.")
        return output_path

    def _generate_pdf_with_text_document(self, html_content, output_path):
        # pyrefly: ignore [missing-import]
        from PySide6.QtGui import QTextDocument, QPdfWriter, QPageSize
        import os

        doc = QTextDocument()
        doc.setHtml(html_content)

        writer = QPdfWriter(output_path)
        writer.setPageSize(QPageSize(QPageSize.A4))
        doc.print_(writer)

        if not os.path.exists(output_path):
            raise Exception("La génération du PDF via QTextDocument a échoué.")
        return output_path

