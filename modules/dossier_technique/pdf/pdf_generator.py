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
                    size: A4 landscape;
                    margin: 1cm;
                }
                .plan-container {
                    width: 100%;
                    border: 1px solid black;
                    border-collapse: collapse;
                    page-break-inside: avoid;
                }
                .plan-container td {
                    vertical-align: top;
                    padding: 5px;
                }
                .plan-left {
                    width: 68%;
                    border-right: 1px solid black;
                }
                .plan-right {
                    width: 32%;
                }
                
                .plan-header {
                    width: 100%;
                    font-size: 7.5pt;
                    border-bottom: 1px solid black;
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                }
                .plan-header td {
                    vertical-align: top;
                    border: none;
                    padding: 0 5px;
                }
                .plan-header-col1 { width: 30%; line-height: 1.3; text-align: center; }
                .plan-header-col2 { width: 30%; line-height: 1.5; }
                .plan-header-col3 { width: 40%; line-height: 1.2; }
                
                .plan-header-col2 span { display: inline-block; width: 60px; }
                
                .plan-content {
                    width: 100%;
                }
                
                .situation-row {
                    display: table;
                    width: 100%;
                    margin-bottom: 10px;
                }
                .situation-col1 {
                    display: table-cell;
                    width: 40%;
                    vertical-align: top;
                }
                .situation-col2 {
                    display: table-cell;
                    width: 60%;
                    vertical-align: top;
                    padding-left: 20px;
                    font-size: 10pt;
                }
                
                .map-situation {
                    width: 100%;
                    border: 1px solid black;
                    background: white;
                    text-align: center;
                }
                .map-situation img { max-width: 100%; max-height: 130px; object-fit: contain; }
                .scale-box {
                    border-top: 1px solid black;
                    text-align: center;
                    font-size: 8pt;
                    font-weight: bold;
                    background: white;
                    padding: 2px 0;
                }
                
                .map-masse {
                    width: 100%;
                    text-align: center;
                }
                .map-masse img { max-width: 100%; max-height: 290px; object-fit: contain; }
                .map-masse-scale {
                    font-size: 9pt;
                    font-weight: bold;
                    margin-top: -10px;
                }
                
                .plan-footer {
                    width: 100%;
                    font-size: 7.5pt;
                    margin-top: 10px;
                }
                .plan-footer td {
                    vertical-align: top;
                    border: none;
                }
                .plan-footer-left { width: 50%; line-height: 1.4; font-weight: bold; }
                .plan-footer-right { width: 50%; text-align: center; line-height: 1.2; }
                
                .coord-title {
                    text-align: center;
                    font-size: 14pt;
                    margin: 0 0 5px 0;
                }
                .coord-subtitle {
                    text-align: center;
                    font-size: 9pt;
                    margin-bottom: 10px;
                }
                .table-coord-main {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 8pt;
                }
                .table-coord-main th, .table-coord-main td {
                    border: 1px solid black;
                    padding: 4px;
                    text-align: center;
                    vertical-align: middle;
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
            <div style="page: plan_page;">
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
                                <div class="situation-col2">
                                    <div style="font-size: 9pt; text-align: center; margin-bottom: 30px;">
                                        NOTA: Toute reproduction officielle doit obligatoirement<br>comporter le timbre sec du Service du Cadastre
                                    </div>
                                    <div style="text-align: center;">
                                        Contenance: &nbsp;&nbsp; <strong>{{ surface_ha_a_ca_formatted }}</strong>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="map-masse">
                                <img src="data:image/png;base64,{{ img_masse }}" alt="Masse">
                                <div class="map-masse-scale">ECHELLE : {{ echelle_2 }}</div>
                            </div>
                        </div>
                        
                        <table class="plan-footer">
                            <tr>
                            <td class="plan-footer-left">
                                N°: {{ dossier }}<br><br>
                                Copie certifiée conforme<br>
                                {{ centre.capitalize() if centre else '......' }}, le :<br>
                                Le Géomètre Assermenté du Cadastre
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
                                <th>BORNES</th>
                                <th>X</th>
                                <th>Y</th>
                                <th>ANGLES</th>
                                <th>DISTANCES</th>
                            </tr>
                            {% for b in bornes_calc %}
                            {% if b.x %}
                            <tr>
                                <td>{{ b.nom }}</td>
                                <td>{{ "%.3f"|format(b.x) }}</td>
                                <td>{{ "%.3f"|format(b.y) }}</td>
                                <td>{{ "%.3f"|format(b.angle) if b.angle else "100.000" }}</td>
                                {% if loop.index0 < (bornes_calc|length - 1) %}
                                <td rowspan="2" style="vertical-align: middle;">{{ "%.3f"|format(b.dist) if b.dist else "" }}</td>
                                {% endif %}
                            </tr>
                            {% else %}
                            <tr>
                                <td>{{ b.nom }}</td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                            {% endif %}
                            {% endfor %}
                        </table>
                    </td>
                    </tr>
                </table>
            </div>
            
        </body>
        </html>
        """
        
    def render_plot_to_base64(self, bornes, voisins=None, zoom_out=False, show_grid_ticks=True):
        if not bornes:
            return ""
            
        fig, ax = plt.subplots(figsize=(8, 6) if not zoom_out else (4, 4))
        
        # Dessiner les voisins (maillage) en premier plan/arrière plan
        if voisins:
            for nom_voisin, pts_voisin in voisins.items():
                if len(pts_voisin) >= 3:
                    vx = [p[0] for p in pts_voisin]
                    vy = [p[1] for p in pts_voisin]
                    vx.append(vx[0])
                    vy.append(vy[0])
                    # Ligne pointillée fine pour les voisins
                    ax.plot(vx, vy, 'k--', linewidth=0.5, alpha=0.6)
                    # Label du voisin
                    cx = sum(vx[:-1]) / len(pts_voisin)
                    cy = sum(vy[:-1]) / len(pts_voisin)
                    ax.text(cx, cy, nom_voisin, fontsize=7 if zoom_out else 9, 
                            ha='center', va='center', alpha=0.8, fontweight='bold')
                            
        # Dessiner le lot principal (trait plein, plus épais)
        # Dessiner le polygone principal
        xs = [b[0] for b in bornes] + [bornes[0][0]]
        ys = [b[1] for b in bornes] + [bornes[0][1]]
        ax.plot(xs, ys, 'k-', linewidth=2)
        
        if zoom_out:
            # Pour la carte de situation (1/5000), remplir le lot en noir
            ax.fill(xs, ys, 'k')
        
        # Définir les limites de la carte pour se concentrer sur le lot principal
        if not zoom_out:
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x
            height = max_y - min_y
            # Margin = 30% of the size, or at least 10 meters (pour agrandir les lots)
            margin_x = max(width * 0.3, 10)
            margin_y = max(height * 0.3, 10)
            ax.set_xlim(min_x - margin_x, max_x + margin_x)
            ax.set_ylim(min_y - margin_y, max_y + margin_y)
            
        # Placer les noms des bornes et les distances (seulement pour la carte de masse 1/500)
        if not zoom_out:
            for i, (x, y) in enumerate(bornes):
                ax.plot(x, y, 'ko', markersize=3)
                ax.text(x, y, f' B{i+1}', fontsize=10, verticalalignment='bottom')
                
                # Add distances on the edges
                if i < len(bornes):
                    p1 = bornes[i]
                    p2 = bornes[(i+1)%len(bornes)]
                dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                mid_x = (p1[0] + p2[0]) / 2
                mid_y = (p1[1] + p2[1]) / 2
                
                # Calculate angle for text rotation
                angle = math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))
                if angle > 90: angle -= 180
                elif angle < -90: angle += 180
                
                ax.text(mid_x, mid_y, f"{dist:.3f}", fontsize=8, 
                        ha='center', va='bottom', rotation=angle)
        
        ax.set_aspect('equal')
        
        # Grid customization
        if show_grid_ticks:
            ax.grid(False)
            ax.set_xticks(ax.get_xticks(), minor=False)
            ax.set_yticks(ax.get_yticks(), minor=False)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.tick_params(axis='both', which='major', length=0)
            # Add grid crosses manually inside the plot
            for xt in ax.get_xticks():
                for yt in ax.get_yticks():
                    ax.plot(xt, yt, marker='+', color='grey', markersize=8, alpha=0.5)
        else:
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.tick_params(axis='both', length=0)
            
        # Draw North arrow if zoom_out
        if zoom_out:
            ax.annotate('N', xy=(0.9, 0.9), xycoords='axes fraction', 
                        xytext=(0.9, 0.75), textcoords='axes fraction',
                        arrowprops=dict(facecolor='black', width=2, headwidth=8),
                        fontsize=12, ha='center', va='top')
                        
        # Hide spines for cleaner look
        for spine in ax.spines.values():
            spine.set_linewidth(1)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=200, transparent=True, bbox_inches='tight', pad_inches=0.1)
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
            img_situation=self.render_plot_to_base64(bornes, data.get("voisins", {}), zoom_out=True, show_grid_ticks=False),
            img_masse=self.render_plot_to_base64(bornes, data.get("voisins", {}), zoom_out=False, show_grid_ticks=True),
            echelle_1=v(data.get("echelle_1")),
            echelle_2=v(data.get("echelle_2"))
        )
        
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            # pyrefly: ignore [missing-import]
            from weasyprint import HTML
            HTML(string=html_out).write_pdf(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"Impossible de générer le PDF : {str(e)}") from e
