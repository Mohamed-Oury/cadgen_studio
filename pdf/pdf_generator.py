import os
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from jinja2 import Template
from weasyprint import HTML, CSS

class PDFGenerator:
    def __init__(self, output_dir="."):
        self.output_dir = output_dir
        
        self.html_template = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Dossier Technique</title>
            <style>
                @page { 
                    size: A4 portrait; 
                    margin: 1.5cm; 
                }
                body { 
                    font-family: 'Helvetica', 'Arial', sans-serif; 
                    font-size: 12pt;
                    line-height: 1.5;
                }
                .page-break { page-break-before: always; }
                
                /* Page 1 - Garde */
                .garde-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 80px;
                    font-size: 10pt;
                }
                .garde-title-box {
                    border: 3px solid black;
                    padding: 20px;
                    text-align: center;
                    margin: 40px 10%;
                }
                .garde-title-box h1 {
                    font-size: 36pt;
                    font-weight: normal;
                    margin: 0;
                    letter-spacing: 2px;
                }
                .garde-subtitle {
                    text-align: center;
                    font-size: 24pt;
                    text-decoration: underline;
                    text-decoration-thickness: 2px;
                    text-underline-offset: 5px;
                    margin: 50px 0 80px 0;
                }
                .garde-info {
                    text-align: center;
                    font-size: 14pt;
                    font-weight: bold;
                    line-height: 2;
                }
                
                /* Page 2 - Rapport */
                .rapport-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    font-weight: bold;
                    margin-bottom: 40px;
                }
                .rapport-title {
                    text-align: center;
                    font-size: 20pt;
                    font-weight: bold;
                    text-decoration: underline;
                    text-decoration-thickness: 2px;
                    margin-bottom: 30px;
                }
                .rapport-details {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }
                .rapport-table {
                    width: 60%;
                    margin: 30px auto;
                    border-collapse: collapse;
                }
                .rapport-table th, .rapport-table td {
                    border: 2px solid black;
                    padding: 8px;
                    text-align: center;
                    font-size: 14pt;
                    font-weight: bold;
                }
                
                /* Page 3 - Coordonnees */
                .coord-header {
                    text-align: center;
                    font-size: 9pt;
                    font-weight: bold;
                    margin-bottom: 30px;
                }
                .coord-title {
                    text-align: center;
                    font-size: 20pt;
                    font-weight: bold;
                    text-decoration: underline;
                    margin-bottom: 30px;
                }
                .coord-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .coord-table th, .coord-table td {
                    border: 1px solid black;
                    padding: 10px;
                    text-align: center;
                }
                
                /* Page 4 - Plan Extrait */
                @page plan_page {
                    size: A4 landscape;
                    margin: 1cm;
                }
                .plan-container {
                    page: plan_page;
                    display: flex;
                    height: 100%;
                    border: 2px solid black;
                }
                .plan-left {
                    width: 65%;
                    border-right: 2px solid black;
                    padding: 10px;
                    display: flex;
                    flex-direction: column;
                }
                .plan-right {
                    width: 35%;
                    padding: 10px;
                }
                .plan-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 9pt;
                    border-bottom: 1px solid black;
                    padding-bottom: 10px;
                    margin-bottom: 10px;
                }
                .plan-images {
                    display: flex;
                    flex-direction: column;
                    flex-grow: 1;
                }
                .plan-image-box {
                    flex: 1;
                    border: 1px solid black;
                    margin-bottom: 10px;
                    position: relative;
                }
                .plan-image-box img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }
                .plan-scale {
                    position: absolute;
                    bottom: 5px;
                    left: 5px;
                    background: white;
                    border: 1px solid black;
                    padding: 2px 10px;
                    font-weight: bold;
                }
                .plan-cartouche {
                    border-top: 1px solid black;
                    padding-top: 10px;
                    font-size: 8pt;
                    display: flex;
                    justify-content: space-between;
                }
            </style>
        </head>
        <body>
            <!-- PAGE 1: Garde -->
            <div class="garde-header">
                <div>
                    MINISTERE DES FINANCES ET DU BUDGET<br><br>
                    DIRECTION GENERALE DES IMPOTS<br><br>
                    DIRECTION DU CADASTRE
                </div>
                <div style="text-align: right;">
                    REPUBLIQUE DE COTE D'IVOIRE<br><br>
                    Union – Discipline - Travail
                </div>
            </div>
            
            <div class="garde-title-box">
                <h1>DOSSIER DE<br>CALCULS</h1>
            </div>
            
            <div class="garde-subtitle">DOSSIER TECHNIQUE DE MORCELLEMENT</div>
            
            <div class="garde-info">
                CENTRE : {{ centre }}<br><br>
                Ilot : {{ ilot }} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Lot : {{ lot }}<br><br>
                Demandeur : {{ demandeur }}
            </div>
            
            <div class="page-break"></div>
            
            <!-- PAGE 2: Rapport -->
            <div class="rapport-header">
                <div>
                    MINISTERE DES FINANCES ET DU BUDGET<br>
                    DIRECTION DES IMPOTS<br>
                    <span style="font-size: 12pt;">DIRECTION DU CADASTRE</span>
                </div>
                <div>REPUBLIQUE DE COTE D'IVOIRE</div>
            </div>
            
            <div class="rapport-title">RAPPORT DU GEOMETRE</div>
            
            <div class="rapport-details">
                <div>
                    Livre Foncier : {{ livre_foncier }}<br>
                    Lotissement : {{ centre.split('-')[1] if '-' in centre else '......' }}<br>
                    Morcellement de TF : {{ tf }}
                </div>
                <div>
                    Centre : {{ centre }}<br>
                    Ilot : {{ ilot }} &nbsp;&nbsp;&nbsp;&nbsp; Lot : {{ lot }}<br>
                    Section : {{ section }}
                </div>
            </div>
            
            <p>Date de bornage fait sur le terrain par le Géomètre : Antérieure<br>
            Date de consultation des documents cadastraux : {{ date_consultation }}</p>
            
            <p><strong>DOCUMENTS DE BASE UTILISES</strong><br>
            CADASTRE :<br>
            N° de la section du plan : ......<br>
            N° du dossier : {{ dossier }}<br>
            GEOMETRE PRIVE :<br>
            Nom du cabinet : CABINET KOUAMELAN 0707074850</p>
            
            <p style="text-align: center; font-style: italic; font-weight: bold;">
                LES COORDONNEES DOIVENT ETRE CELLES DU SYSTEME WGS 84 UTM FUSEAU 30N<br>
                COORDONNEES DES SOMMETS DE L'ILOT UTILISE OU POLYGONATION
            </p>
            
            <h4 style="text-align: center; font-style: italic; font-size: 16pt;">ILOT {{ ilot }}</h4>
            
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
            
            <div class="page-break"></div>
            
            <!-- PAGE 3: Tableau -->
            <div class="coord-header">
                REPUBLIQUE DE COTE D'IVOIRE &nbsp;&nbsp;&nbsp;&nbsp; Centre : {{ centre }}<br>
                MINISTERE DES FINANCES &nbsp;&nbsp;&nbsp;&nbsp; Ilot : {{ ilot }} &nbsp;&nbsp;&nbsp;&nbsp; Lot : {{ lot }}<br>
                ET DU BUDGET &nbsp;&nbsp;&nbsp;&nbsp; Morcellement de TF : {{ tf }}<br>
                DIRECTION DES IMPOTS &nbsp;&nbsp;&nbsp;&nbsp; Livre Foncier : {{ livre_foncier }}<br>
                <span style="font-size: 12pt;">DIRECTION DU CADASTRE</span> &nbsp;&nbsp;&nbsp;&nbsp; Demandeur : {{ demandeur }}
            </div>
            
            <div class="coord-title">TABLEAU DE COORDONNEES<br>CALCUL RETOUR ET CALCUL DE SURFACE</div>
            
            <table class="coord-table">
                <tr>
                    <td colspan="3" style="font-weight: bold;">CALCUL DE SURFACE</td>
                    <td colspan="4"></td>
                </tr>
                <tr>
                    <td colspan="2" style="font-weight: bold;">ILOT : {{ ilot }}</td>
                    <td colspan="1" style="font-weight: bold;">LOT : {{ lot }}</td>
                    <td colspan="4" style="font-weight: bold;">SURFACE : {{ "%.3f"|format(surface) }} m² &nbsp;&nbsp;&nbsp;&nbsp; {{ surface_ha_a_ca }}</td>
                </tr>
                <tr style="font-weight: bold;">
                    <td colspan="4">COORDONNEES</td>
                    <td colspan="3">CALCUL RETOUR</td>
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
                    <td>{{ b.point }}</td>
                    <td>{{ b.nom }}</td>
                    <td style="font-weight: bold;">{{ "%.3f"|format(b.x) if b.x else "" }}</td>
                    <td style="font-weight: bold;">{{ "%.3f"|format(b.y) if b.y else "" }}</td>
                    <td>{{ "%.3f"|format(b.angle) if b.angle else "" }}</td>
                    <td>{{ "%.3f"|format(b.dist) if b.dist else "" }}</td>
                    <td>{{ "%.3f"|format(b.gis) if b.gis else "" }}</td>
                </tr>
                {% endfor %}
            </table>
            
            <div class="page-break"></div>
            
            <!-- PAGE 4: Plan Extrait (Landscape) -->
            <div class="plan-container">
                <div class="plan-left">
                    <div class="plan-header">
                        <div>
                            Republique de Côte d'Ivoire<br>
                            Ministère des Finances et du Budget<br>
                            Direction du Cadastre<br>
                            Bureau de {{ centre.split('-')[0] if '-' in centre else '......' }}
                        </div>
                        <div>
                            Centre: <strong>{{ centre }}</strong><br>
                            Ilot: <strong>{{ ilot }}</strong> &nbsp;&nbsp; Lot: <strong>{{ lot }}</strong><br>
                            Demandeur: <strong>{{ demandeur }}</strong>
                        </div>
                    </div>
                    
                    <div class="plan-images">
                        <div class="plan-image-box">
                            <img src="data:image/png;base64,{{ img_situation }}" alt="Plan Situation">
                            <div class="plan-scale">ECHELLE : {{ echelle_1 }}</div>
                        </div>
                        <div class="plan-image-box" style="flex: 2;">
                            <img src="data:image/png;base64,{{ img_masse }}" alt="Plan Masse">
                            <div class="plan-scale">ECHELLE : {{ echelle_2 }}</div>
                        </div>
                    </div>
                    
                    <div class="plan-cartouche">
                        <div>
                            Copie certifiée conforme<br>
                            Le Géomètre Assermenté du Cadastre
                        </div>
                        <div style="text-align: center;">
                            <strong>CABINET KOUAMELAN</strong><br>
                            Géomètre-Expert Agréé<br>
                            Médiateur Professionnel
                        </div>
                    </div>
                </div>
                
                <div class="plan-right">
                    <h3 style="text-align: center; margin-top: 0;">TABLEAU DES COORDONNEES</h3>
                    <p style="text-align: center; font-size: 9pt;">ITRF96-1998.2 / Ellipsoïde du WGS 84 UTM FUSEAU 30N</p>
                    <table class="coord-table" style="font-size: 10pt;">
                        <tr>
                            <th>BORNES</th>
                            <th>X</th>
                            <th>Y</th>
                            <th>DISTANCES</th>
                        </tr>
                        {% for b in bornes_calc %}
                        {% if b.x %}
                        <tr>
                            <td>{{ b.nom }}</td>
                            <td>{{ "%.3f"|format(b.x) }}</td>
                            <td>{{ "%.3f"|format(b.y) }}</td>
                            <td>{{ "%.3f"|format(b.dist) if b.dist else "" }}</td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </table>
                </div>
            </div>
            
        </body>
        </html>
        """
        
    def render_plot_to_base64(self, bornes, zoom_out=False):
        if not bornes:
            return ""
            
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Extraire X et Y
        xs = [b[0] for b in bornes]
        ys = [b[1] for b in bornes]
        # Fermer le polygone
        xs.append(xs[0])
        ys.append(ys[0])
        
        ax.plot(xs, ys, 'k-', linewidth=2)
        
        for i, (x, y) in enumerate(bornes):
            ax.plot(x, y, 'ko', markersize=4)
            ax.text(x, y, f' B{i+1}', fontsize=9, verticalalignment='bottom')
            
        ax.set_aspect('equal')
        
        # Grid et axes
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Marge
        margin_x = (max(xs) - min(xs)) * (2.0 if zoom_out else 0.2)
        margin_y = (max(ys) - min(ys)) * (2.0 if zoom_out else 0.2)
        
        # Pour éviter margin = 0
        margin_x = max(margin_x, 10.0)
        margin_y = max(margin_y, 10.0)
        
        ax.set_xlim(min(xs) - margin_x, max(xs) + margin_x)
        ax.set_ylim(min(ys) - margin_y, max(ys) + margin_y)
        
        # Cacher les labels d'axes pour un style plus plan
        ax.tick_params(axis='both', which='major', labelsize=8)
        
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close(fig)
        
        return base64.b64encode(buf.getvalue()).decode('utf-8')
        
    def _format_surface_ha(self, surface_m2):
        ha = int(surface_m2 // 10000)
        a = int((surface_m2 % 10000) // 100)
        ca = int(surface_m2 % 100)
        return f"{ha:02d} Ha {a:02d} A {ca:02d} Ca"

    def generate_pdf(self, filename, data):
        # Valider les champs vides avec "......"
        def v(val):
            return val if val and str(val).strip() else "......"
            
        bornes = data.get("bornes", [])
        
        # Calculer les distances et gisements virtuels
        import math
        bornes_calc = []
        for i in range(len(bornes)):
            b1 = bornes[i]
            b2 = bornes[(i+1)%len(bornes)]
            dist = math.sqrt((b2[0]-b1[0])**2 + (b2[1]-b1[1])**2)
            # Ajout du point
            bornes_calc.append({
                "point": f"P{i+1}",
                "nom": f"B{i+1}",
                "x": b1[0],
                "y": b1[1],
                "angle": 100.000, # Fake angle pour l'exemple
                "dist": dist,
                "gis": 100.000 # Fake gisement
            })
            
        # Ajouter une ligne vide de bouclage
        if len(bornes_calc) > 0:
            bornes_calc.append({
                "point": "", "nom": "B1", "x": None, "y": None, 
                "angle": None, "dist": bornes_calc[-1]["dist"], "gis": bornes_calc[-1]["gis"]
            })
            bornes_calc[-2]["dist"] = None
            bornes_calc[-2]["gis"] = None

        template = Template(self.html_template)
        html_out = template.render(
            demandeur=v(data.get("demandeur")),
            centre=v(data.get("centre")),
            dossier=v(data.get("dossier")),
            ilot=v(data.get("ilot")),
            lot=v(data.get("lot")),
            tf=v(data.get("tf")),
            livre_foncier=v(data.get("livre_foncier")),
            section=v(data.get("section")),
            date_consultation=v(data.get("date_consultation")),
            surface=float(data.get("surface", "0.0").replace(" m²", "")),
            surface_ha_a_ca=self._format_surface_ha(float(data.get("surface", "0.0").replace(" m²", ""))),
            bornes=bornes,
            bornes_calc=bornes_calc,
            img_situation=self.render_plot_to_base64(bornes, zoom_out=True),
            img_masse=self.render_plot_to_base64(bornes, zoom_out=False),
            echelle_1=v(data.get("echelle_1")),
            echelle_2=v(data.get("echelle_2"))
        )
        
        output_path = os.path.join(self.output_dir, filename)
        HTML(string=html_out).write_pdf(output_path)
        return output_path
