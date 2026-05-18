#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génération du rapport PDF - Analyse Multivariée League of Legends
Exécuter depuis le dossier du projet : python generate_pdf.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas as pdfcanvas

# ─── Constantes ───────────────────────────────────────────────────────────────
OUTPUT   = "rapport_final.pdf"
FIGURES  = "figures"
PAGE_W, PAGE_H = A4

C_BLUE       = colors.HexColor("#0E4E85")
C_BLUE_LIGHT = colors.HexColor("#E8F0F8")
C_GOLD       = colors.HexColor("#C89B3C")
C_DARK       = colors.HexColor("#1E1E28")
C_GRAY       = colors.HexColor("#F2F2F2")
C_ACCENT     = colors.HexColor("#3498DB")
C_GREEN_BG   = colors.HexColor("#EAF7EE")
C_GREEN      = colors.HexColor("#1E8B4C")
C_RED        = colors.HexColor("#E74C3C")
C_LINE       = colors.HexColor("#CCCCCC")

# ─── Styles de paragraphes ────────────────────────────────────────────────────
def make_styles():
    S = {}
    def ps(name, **kw):
        defaults = dict(fontName='Helvetica', fontSize=10, leading=14,
                        textColor=C_DARK, spaceBefore=3, spaceAfter=3)
        defaults.update(kw)
        S[name] = ParagraphStyle(name, **defaults)

    ps('h1',  fontName='Helvetica-Bold', fontSize=17, textColor=C_BLUE,
       spaceBefore=18, spaceAfter=8, leading=22)
    ps('h2',  fontName='Helvetica-Bold', fontSize=13, textColor=C_DARK,
       spaceBefore=12, spaceAfter=5, leading=17)
    ps('h3',  fontName='Helvetica-Bold', fontSize=11, textColor=C_BLUE,
       spaceBefore=9, spaceAfter=4, leading=14)
    ps('body', alignment=TA_JUSTIFY, leading=15, spaceAfter=5)
    ps('bullet', leftIndent=18, spaceBefore=2, spaceAfter=2, leading=14)
    ps('caption', fontName='Helvetica-Oblique', fontSize=8.5,
       textColor=colors.HexColor("#555555"), alignment=TA_CENTER,
       spaceBefore=3, spaceAfter=10)
    ps('toc_ch',  fontName='Helvetica-Bold', fontSize=11, textColor=C_BLUE,
       spaceBefore=5, spaceAfter=2)
    ps('toc_sec', leftIndent=15, fontSize=10, spaceBefore=1, spaceAfter=1)
    ps('th', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white,
       alignment=TA_CENTER, leading=12)
    ps('td', fontSize=9, leading=12, spaceBefore=0, spaceAfter=0)
    ps('td_center', fontSize=9, alignment=TA_CENTER, leading=12,
       spaceBefore=0, spaceAfter=0)
    ps('result_title', fontName='Helvetica-Bold', fontSize=10,
       textColor=C_GREEN, spaceBefore=0, spaceAfter=3)
    ps('result_body', fontSize=10, leading=14, spaceBefore=0, spaceAfter=0)
    ps('code', fontName='Courier', fontSize=8, leading=12,
       textColor=C_DARK, leftIndent=8, spaceBefore=2, spaceAfter=2)
    return S

# ─── Utilitaires ──────────────────────────────────────────────────────────────
def hr(color=C_LINE):
    return HRFlowable(width="100%", thickness=1, color=color, spaceAfter=6, spaceBefore=6)

def vspace(h=0.3):
    return Spacer(1, h * cm)

def _scaled_image(path, width_cm):
    """Return an Image with correct proportional height."""
    img = Image(path)
    aspect = img.imageHeight / float(img.imageWidth)
    w = width_cm * cm
    h = w * aspect
    return Image(path, width=w, height=h)

def include_figure(filename, S, caption_text=None, width_cm=14.5):
    path = os.path.join(FIGURES, filename)
    items = []
    if os.path.exists(path):
        items.append(_scaled_image(path, width_cm))
    else:
        items.append(_placeholder(filename, width_cm))
    if caption_text:
        items.append(Paragraph(caption_text, S['caption']))
    return items

def _placeholder(name, width_cm):
    data = [[f"[Figure à générer : {name}]"]]
    t = Table(data, colWidths=[width_cm * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_GRAY),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 22),
        ('BOTTOMPADDING', (0,0), (-1,-1), 22),
    ]))
    return t

def info_box(paragraphs_or_text, S, title=None, bg=C_BLUE_LIGHT, border=C_ACCENT):
    """Coloured info box. paragraphs_or_text can be a string or list of Paragraphs."""
    inner = []
    if title:
        inner.append(Paragraph(f"<b>{title}</b>", S['h3']))
        inner.append(Spacer(1, 4))
    if isinstance(paragraphs_or_text, str):
        inner.append(Paragraph(paragraphs_or_text, S['body']))
    else:
        inner.extend(paragraphs_or_text)
    t = Table([[inner]], colWidths=[15.5 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg),
        ('BOX', (0,0), (-1,-1), 1.5, border),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def result_box(lines_html, S, title="Résultat clé"):
    inner = [Paragraph(f"<b>{title}</b>", S['result_title'])]
    for l in lines_html:
        inner.append(Paragraph(f"• {l}", S['result_body']))
    t = Table([[inner]], colWidths=[15.5 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_GREEN_BG),
        ('BOX', (0,0), (-1,-1), 1.5, C_GREEN),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def header_table(col_headers, rows, S, col_widths=None):
    """Styled table with blue header row."""
    data = [[Paragraph(h, S['th']) for h in col_headers]]
    for row in rows:
        data.append([Paragraph(str(c), S['td']) for c in row])
    if col_widths is None:
        col_widths = [15.5 * cm / len(col_headers)] * len(col_headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    n = len(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_BLUE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.4, C_LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t

# ─── Canvas avec en-têtes / numérotation ─────────────────────────────────────
class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_states = []

    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for state in self._saved_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self._draw_chrome()
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_chrome(self):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#888888"))
        self.setStrokeColor(C_LINE)
        # Header
        self.line(2*cm, PAGE_H - 1.7*cm, PAGE_W - 2*cm, PAGE_H - 1.7*cm)
        self.drawString(2*cm, PAGE_H - 1.4*cm, "Analyse Multivariée — League of Legends")
        self.drawRightString(PAGE_W - 2*cm, PAGE_H - 1.4*cm, "Yassine — 2025–2026")
        # Footer
        self.line(2*cm, 1.5*cm, PAGE_W - 2*cm, 1.5*cm)
        self.drawCentredString(PAGE_W / 2, 0.9*cm, f"— {self._pageNumber} —")
        self.restoreState()

# ─── Construction du document ─────────────────────────────────────────────────
def build_doc():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=2.8*cm, rightMargin=2.2*cm,
        topMargin=2.4*cm,  bottomMargin=2.4*cm,
        title="Analyse Multivariée — League of Legends",
        author="Yassine",
        subject="Méthodes Statistiques et Étude de Données",
    )
    S = make_styles()
    story = []

    # ── PAGE DE TITRE ──────────────────────────────────────────────────────────
    story.append(vspace(2))
    story.append(HRFlowable(width="100%", thickness=3, color=C_BLUE, spaceAfter=12))

    story.append(Paragraph(
        "Analyse Multivariée des Performances<br/>de Joueurs en League of Legends",
        ParagraphStyle('TP', fontName='Helvetica-Bold', fontSize=22, textColor=C_DARK,
                       alignment=TA_CENTER, leading=30, spaceAfter=6)
    ))

    story.append(HRFlowable(width="100%", thickness=3, color=C_BLUE, spaceAfter=16))
    story.append(Paragraph(
        "Rapport de Mini-Projet — Méthodes Statistiques et Étude de Données",
        ParagraphStyle('Sub', fontName='Helvetica-Oblique', fontSize=13,
                       textColor=C_BLUE, alignment=TA_CENTER, spaceAfter=24)
    ))

    # Abstract box
    abstract = (
        "Ce rapport présente une analyse multivariée complète d'un jeu de données "
        "contenant plus de 730 000 parties de League of Legends. Après prétraitement "
        "et échantillonnage stratifié (15 000 observations), nous appliquons une "
        "Analyse en Composantes Principales (ACP), une classification non supervisée "
        "(K-means et CAH) et deux modèles d'apprentissage supervisé (régression "
        "logistique et forêt aléatoire) afin d'identifier les profils de joueurs "
        "et les déterminants de la victoire."
    )
    story.append(info_box(abstract, S, title="Résumé"))
    story.append(vspace(2))

    info_data = [
        ["Étudiant :", "Yassine"],
        ["Cours :", "Méthodes Statistiques et Étude de Données"],
        ["Année :", "2025 – 2026"],
    ]
    t = Table(info_data, colWidths=[4*cm, 11*cm])
    t.setStyle(TableStyle([
        ('FONTNAME',   (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',   (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,0), (-1,-1), 10),
        ('TEXTCOLOR',  (0,0), (0,-1), C_BLUE),
        ('TEXTCOLOR',  (1,0), (1,-1), C_DARK),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ── TABLE DES MATIÈRES ─────────────────────────────────────────────────────
    story.append(Paragraph("Table des matières", S['h1']))
    story.append(hr())
    toc_items = [
        ("1", "Introduction", [
            "1.1 Contexte et motivation",
            "1.2 Objectifs",
        ]),
        ("2", "Présentation du jeu de données", [
            "2.1 Source et format",
            "2.2 Variables retenues",
            "2.3 Les rôles dans League of Legends",
        ]),
        ("3", "Prétraitement des données", [
            "3.1 Jointure des tables",
            "3.2 Échantillonnage stratifié",
            "3.3 Valeurs manquantes",
            "3.4 Détection et traitement des outliers",
        ]),
        ("4", "Statistiques descriptives", [
            "4.1 Moyennes par Lane",
            "4.2 Matrice de corrélation",
        ]),
        ("5", "Analyse en Composantes Principales (ACP)", [
            "5.1 Scree Plot — choix des axes",
            "5.2 Cercle des corrélations",
            "5.3 Contributions des variables",
            "5.4 Projection des individus",
        ]),
        ("6", "Classification non supervisée", [
            "6.1 Nombre optimal de clusters",
            "6.2 K-means",
            "6.3 CAH — Dendrogramme",
            "6.4 Profils des clusters",
        ]),
        ("7", "Apprentissage supervisé", [
            "7.1 Régression logistique — prédire la Victoire",
            "7.2 Forêt aléatoire — prédire le Rôle",
            "7.3 Comparaison des modèles",
        ]),
        ("8", "Conclusion", []),
    ]
    for num, title, sections in toc_items:
        story.append(Paragraph(f"<b>Chapitre {num}.</b>  {title}", S['toc_ch']))
        for sec in sections:
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{sec}", S['toc_sec']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 1 — INTRODUCTION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 1 — Introduction", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph("1.1  Contexte et motivation", S['h2']))
    story.append(Paragraph(
        "League of Legends (LoL) est un jeu de stratégie en ligne multijoueur (MOBA) "
        "développé par Riot Games, comptant plus de <b>150 millions de joueurs enregistrés</b> "
        "à travers le monde. Deux équipes de cinq joueurs s'affrontent sur une carte, "
        "chaque joueur occupant un rôle spécifique (<i>lane</i>) défini par sa position "
        "sur le terrain et ses responsabilités stratégiques : "
        "<b>TOP, JUNGLE, MIDDLE, BOTTOM</b> et <b>UTILITY/SUPPORT</b>.", S['body']))
    story.append(Paragraph(
        "Chaque partie génère une quantité importante de statistiques individuelles "
        "(kills, assists, dégâts infligés, or accumulé, etc.) qui reflètent à la fois "
        "le style de jeu du joueur et son efficacité relative. Ce projet exploite ces "
        "données pour répondre à deux questions :", S['body']))
    for bullet in [
        "<b>Peut-on identifier des profils de joueurs distincts</b> à partir de leurs "
        "statistiques de performance, sans connaître leur rôle déclaré ?",
        "<b>Quels sont les facteurs statistiques les plus associés à la victoire</b>, "
        "et peut-on prédire le résultat d'une partie à partir des seules "
        "statistiques individuelles ?"
    ]:
        story.append(Paragraph(f"• {bullet}", S['bullet']))

    story.append(Paragraph("1.2  Objectifs du rapport", S['h2']))
    story.append(Paragraph(
        "Ce rapport s'inscrit dans le cadre du cours de <i>Méthodes Statistiques "
        "et Étude de Données</i>. Il illustre, sur des données réelles et volumineuses, "
        "l'enchaînement des méthodes suivantes :", S['body']))
    methods = [
        "Prétraitement : valeurs manquantes, outliers, échantillonnage stratifié",
        "Statistiques descriptives par rôle et matrice de corrélation",
        "Analyse en Composantes Principales (ACP) — réduction de dimension",
        "Classification non supervisée : K-means et CAH",
        "Apprentissage supervisé : régression logistique et forêt aléatoire",
    ]
    for i, m in enumerate(methods, 1):
        story.append(Paragraph(f"{i}. {m}", S['bullet']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 2 — PRÉSENTATION DU JEU DE DONNÉES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 2 — Présentation du jeu de données", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph("2.1  Source et format", S['h2']))
    story.append(Paragraph(
        "Le jeu de données est organisé sous forme de <b>cinq tables relationnelles</b> "
        "au format CSV. La table principale, <b>MatchStatsTbl</b>, recense les "
        "statistiques individuelles de chaque joueur par partie.", S['body']))

    story.append(vspace(0.3))
    vol_data = [
        ["Fichier", "Taille", "Contenu"],
        ["MatchStatsTbl.csv", "~93 Mo", "Statistiques individuelles par joueur/match"],
        ["MatchTbl.csv", "~12 Mo", "Métadonnées des matchs (durée, région…)"],
        ["SummonerMatchTbl.csv", "~22 Mo", "Correspondance invocateurs / matchs"],
        ["TeamMatchTbl.csv", "~17 Mo", "Statistiques d'équipe"],
        ["ChampionTbl.csv", "< 1 Mo", "Référentiel des champions"],
        ["RankTbl.csv", "< 1 Mo", "Référentiel des rangs ELO"],
    ]
    story.append(header_table(
        vol_data[0], vol_data[1:], S,
        col_widths=[5.5*cm, 2.8*cm, 7.2*cm]
    ))
    story.append(Paragraph(
        "Tableau 1 — Tables du jeu de données et leur volume.", S['caption']))
    story.append(vspace(0.3))
    story.append(result_box([
        "Volume total après jointure : <b>~730 000 observations × 30+ colonnes</b>",
        "Représente des dizaines de milliers de parties uniques",
    ], S, title="Volume du jeu de données"))

    story.append(Paragraph("2.2  Variables retenues pour l'analyse", S['h2']))
    story.append(Paragraph(
        "Après jointure et exploration, <b>10 variables numériques</b> ont été "
        "sélectionnées pour l'analyse multivariée :", S['body']))
    vars_data = [
        ["Variable", "Description", "Unité"],
        ["kills",           "Ennemis éliminés",                         "Entier"],
        ["deaths",          "Nombre de morts",                          "Entier"],
        ["assists",         "Assistances",                              "Entier"],
        ["DmgDealt",        "Dégâts infligés aux ennemis",              "Points"],
        ["DmgTaken",        "Dégâts reçus",                            "Points"],
        ["TurretDmgDealt",  "Dégâts infligés aux tourelles",            "Points"],
        ["TotalGold",       "Or total accumulé",                        "Unités"],
        ["MinionsKilled",   "Sbires éliminés (CS — farm)",              "Entier"],
        ["visionScore",     "Score de vision / éclairage de carte",     "Score"],
        ["DragonKills",     "Dragons tués",                             "Entier"],
    ]
    story.append(header_table(
        vars_data[0], vars_data[1:], S,
        col_widths=[4.2*cm, 7.8*cm, 3.5*cm]
    ))
    story.append(Paragraph(
        "Tableau 2 — Variables numériques retenues pour l'analyse multivariée.", S['caption']))

    story.append(Paragraph("2.3  Les rôles dans League of Legends", S['h2']))
    story.append(Paragraph(
        "League of Legends définit cinq rôles dont les responsabilités "
        "se traduisent par des profils statistiques très différents :", S['body']))
    roles_data = [
        ["Lane", "Rôle et spécificité statistique attendue"],
        ["TOP",     "Combattant solitaire, fort DmgTaken et TurretDmgDealt élevé"],
        ["JUNGLE",  "Explore la carte, tue les monstres neutres (DragonKills élevé, CS faible)"],
        ["MIDDLE",  "Lane centrale offensive — DmgDealt et MinionsKilled très élevés"],
        ["BOTTOM",  "Carry de dégâts à distance — TotalGold et DmgDealt élevés"],
        ["UTILITY", "Support / aide à l'équipe — assists et visionScore très élevés, peu de kills"],
    ]
    story.append(header_table(
        roles_data[0], roles_data[1:], S,
        col_widths=[2.8*cm, 12.7*cm]
    ))
    story.append(Paragraph("Tableau 3 — Rôles et profils statistiques attendus.", S['caption']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 3 — PRÉTRAITEMENT
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 3 — Prétraitement des données", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph("3.1  Jointure des tables", S['h2']))
    story.append(Paragraph(
        "Les cinq tables sont reliées par des clés étrangères. La jointure est "
        "réalisée en R avec des opérations <i>left_join</i> successives via "
        "<b>tidyverse</b> :", S['body']))
    join_schema = [
        ["MatchStats", "→ (SummonerMatchFk)", "SummonerMatch"],
        ["SummonerMatch", "→ (MatchFk)", "Match"],
        ["Match", "→ (RankFk)", "Rank"],
        ["Match", "→ (ChampionFk)", "Champion"],
    ]
    for row in join_schema:
        story.append(Paragraph(
            f"&nbsp;&nbsp;&nbsp;<b>{row[0]}</b>  <font color='#888888'>{row[1]}</font>  "
            f"<b>{row[2]}</b>", S['body']))

    story.append(Paragraph("3.2  Échantillonnage stratifié", S['h2']))
    story.append(Paragraph(
        "730 000 observations dépassent largement les capacités de calcul "
        "raisonnables des algorithmes d'ACP et de clustering. Un <b>échantillon "
        "stratifié de 15 000 observations</b> (3 000 par Lane) a été tiré "
        "par la fonction <i>slice_sample</i> du package dplyr.", S['body']))
    story.append(info_box(
        "La <b>stratification par Lane</b> garantit des effectifs équilibrés pour "
        "les analyses comparatives et le clustering. Un échantillon aléatoire simple "
        "produirait un déséquilibre entre les rôles (certaines lanes étant "
        "surreprésentées dans les données brutes).",
        S, title="Pourquoi stratifier ?"))

    story.append(Paragraph("3.3  Vérification des valeurs manquantes", S['h2']))
    story.append(Paragraph(
        "Après sélection des 10 variables numériques et des colonnes catégorielles, "
        "<b>aucune valeur manquante</b> n'a été détectée dans l'échantillon retenu "
        "(vérification via <i>complete.cases</i> après la jointure).", S['body']))

    story.append(Paragraph("3.4  Détection et traitement des outliers", S['h2']))
    story.append(Paragraph(
        "La présence de valeurs aberrantes est visualisée par des boîtes à moustaches "
        "(<i>boxplots</i>). Les points rouges représentent les observations "
        "dépassant 1,5 × IQR.", S['body']))
    story.extend(include_figure("01_outliers_boxplots.png", S,
        "Figure 1 — Boxplots des 10 variables avant traitement. "
        "Les distributions asymétriques à droite (DmgDealt, TotalGold) "
        "indiquent la présence d'outliers statistiques.", 14.5))

    story.append(Paragraph(
        "La règle des <b>3 sigma</b> (|z| > 3) est appliquée variable par variable. "
        "Cette méthode supprime uniquement les valeurs véritablement extrêmes tout en "
        "conservant la richesse naturelle des distributions :", S['body']))
    for item in [
        "Avant : 15 000 observations (échantillon stratifié)",
        "Après suppression (|z| > 3) : environ 12 700 observations retenues",
        "Perte : ~15 % — attendue et acceptable pour la règle 3-sigma",
    ]:
        story.append(Paragraph(f"• {item}", S['bullet']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 4 — STATISTIQUES DESCRIPTIVES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 4 — Statistiques descriptives", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph("4.1  Moyennes par Lane", S['h2']))
    story.append(Paragraph(
        "Le tableau suivant présente les moyennes des variables de performance "
        "par rôle, calculées sur le dataset nettoyé (~12 700 observations).", S['body']))
    desc_data = [
        ["Lane",    "Kills", "Deaths", "Assists", "DmgDealt", "DmgTaken", "Gold",    "Vision"],
        ["BOTTOM",  "6,1",   "6,2",    "8,4",     "21 858",   "22 362",   "12 033",  "26,1"],
        ["JUNGLE",  "6,3",   "5,8",    "6,8",     "18 635",   "31 180",   "11 712",  "23,8"],
        ["MIDDLE",  "6,3",   "6,2",    "6,9",     "23 948",   "25 104",   "11 808",  "19,0"],
        ["TOP",     "5,8",   "6,1",    "6,1",     "23 613",   "30 492",   "11 786",  "17,2"],
        ["UTILITY", "2,7",   "5,8",    "11,1",    "12 103",   "19 909",   "8 527",   "56,2"],
    ]
    story.append(header_table(
        desc_data[0], desc_data[1:], S,
        col_widths=[2.2*cm, 1.7*cm, 1.9*cm, 2.0*cm, 2.2*cm, 2.2*cm, 1.9*cm, 1.9*cm]
    ))
    story.append(Paragraph(
        "Tableau 4 — Statistiques descriptives moyennes par rôle.", S['caption']))

    story.append(Paragraph("<b>Observations clés :</b>", S['h3']))
    for obs in [
        "<b>UTILITY</b> se démarque nettement : 2,7 kills (le plus faible), "
        "11,1 assists et un visionScore de <b>56,2</b> — soit 3× celui d'un "
        "TOP ou MID laner. Ces écarts confirment la vocation de soutien.",
        "<b>JUNGLE</b> et <b>TOP</b> ont les DmgTaken les plus élevés "
        "(31 180 et 30 492), cohérent avec leur rôle de tank/frontline.",
        "<b>MIDDLE</b> présente le DmgDealt maximal (23 948) : fort potentiel "
        "offensif de cette lane centrale.",
        "<b>BOTTOM</b> génère le plus d'or (12 033), en accord avec sa nature "
        "de carry économique.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))

    story.append(Paragraph("4.2  Matrice de corrélation", S['h2']))
    story.append(Paragraph(
        "La matrice de corrélation de Pearson révèle les relations linéaires "
        "entre les 10 variables de performance.", S['body']))
    story.extend(include_figure("02_correlation_matrix.png", S,
        "Figure 2 — Matrice de corrélation (Pearson). Bleu = corrélation positive, "
        "rouge = corrélation négative. La taille des cercles représente la force "
        "de l'association.", 11))

    story.append(Paragraph("<b>Interprétation :</b>", S['h3']))
    for obs in [
        "<b>Forte corrélation positive</b> entre TotalGold et DmgDealt "
        "(r ≈ +0,8) : les joueurs offensifs accumulent plus d'or.",
        "<b>MinionsKilled</b> est fortement corrélé à TotalGold (r ≈ +0,7) : "
        "farmer les sbires est la source d'or la plus stable.",
        "<b>Corrélation négative modérée</b> entre assists et MinionsKilled : "
        "les supports assistent mais ne farmant pas.",
        "<b>visionScore</b> est peu corrélé aux variables offensives : "
        "dimension indépendante, spécifique au rôle Support.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))
    story.append(Paragraph(
        "Ces corrélations justifient une réduction de dimension par ACP : "
        "les variables redondantes peuvent être résumées en quelques axes.", S['body']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 5 — ACP
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 5 — Analyse en Composantes Principales (ACP)", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph(
        "L'ACP transforme les 10 variables corrélées en composantes principales "
        "non corrélées. Elle est réalisée sur la matrice <b>centrée-réduite</b> "
        "(option scale.unit = TRUE dans FactoMineR) pour éviter que les variables "
        "avec de grandes valeurs absolues (ex. DmgDealt ≈ 20 000) dominent "
        "celles avec de petites valeurs (ex. DragonKills ≈ 0,1).", S['body']))

    story.append(Paragraph("5.1  Scree Plot — Choix du nombre d'axes", S['h2']))
    story.extend(include_figure("03_acp_screeplot.png", S,
        "Figure 3 — Éboulis des valeurs propres (Scree Plot). "
        "Chaque barre représente le pourcentage de variance expliquée "
        "par une composante principale.", 13))

    eig_data = [
        ["Axe", "Valeur propre", "% Variance", "% Cumulé"],
        ["PC1", "3,553", "35,53 %", "35,53 %"],
        ["PC2", "1,851", "18,51 %", "54,04 %"],
        ["PC3", "1,214", "12,14 %", "66,18 %"],
        ["PC4", "1,077", "10,77 %", "76,95 %"],
        ["PC5", "0,759", "7,59 %",  "84,53 %"],
    ]
    story.append(header_table(
        eig_data[0], eig_data[1:], S,
        col_widths=[2.5*cm, 3.8*cm, 3.8*cm, 3.8*cm]
    ))
    story.append(Paragraph(
        "Tableau 5 — Valeurs propres et variances expliquées.", S['caption']))
    story.append(result_box([
        "Critère de Kaiser (valeur propre > 1) → <b>4 composantes retenues</b>",
        "<b>76,95 %</b> de la variance totale expliquée par PC1–PC4",
        "PC1 seul explique 35,53 % — axe dominant",
    ], S, "Résultat — Choix des axes ACP"))

    story.append(Paragraph("5.2  Cercle des corrélations", S['h2']))
    story.append(Paragraph(
        "Le cercle des corrélations représente chaque variable originale comme un "
        "vecteur dans le plan des composantes principales. La couleur traduit le cos² "
        "(qualité de représentation) : plus le cos² est proche de 1, mieux la variable "
        "est représentée sur cet axe.", S['body']))

    # Two figures side by side
    fig12_path = os.path.join(FIGURES, "04_acp_cercle_PC1_PC2.png")
    fig13_path = os.path.join(FIGURES, "05_acp_cercle_PC1_PC3.png")
    row_imgs = []
    for path, label in [(fig12_path, "PC1 vs PC2"), (fig13_path, "PC1 vs PC3")]:
        if os.path.exists(path):
            row_imgs.append([_scaled_image(path, 6.8),
                             Paragraph(label, S['caption'])])
        else:
            row_imgs.append([_placeholder(os.path.basename(path), 6.8),
                             Paragraph(label, S['caption'])])
    t_imgs = Table([[row_imgs[0][0], row_imgs[1][0]]], colWidths=[7.5*cm, 7.5*cm])
    t_imgs.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_imgs)
    story.append(Paragraph(
        "Figure 4 & 5 — Cercles des corrélations PC1/PC2 (gauche) et PC1/PC3 (droite).",
        S['caption']))

    for obs in [
        "<b>PC1 (35,5 %)</b> — Axe d'<i>intensité offensive</i> : "
        "DmgDealt, kills, TotalGold et MinionsKilled pointent tous dans la même "
        "direction. Un joueur avec un score PC1 élevé est très actif offensivement.",
        "<b>PC2 (18,5 %)</b> — Axe d'<i>utilité d'équipe</i> : "
        "assists et visionScore s'opposent à MinionsKilled et TurretDmgDealt. "
        "Cet axe discrimine les supports (PC2 élevé) des farmers solo (PC2 faible).",
        "<b>PC3 (12,1 %)</b> — Capte principalement DmgTaken (résistance, "
        "rôle de tank) versus visionScore.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))

    story.append(Paragraph("5.3  Contributions des variables", S['h2']))
    fig_c1_path = os.path.join(FIGURES, "06_contributions_PC1.png")
    fig_c2_path = os.path.join(FIGURES, "07_contributions_PC2.png")
    row_c = []
    for path in [fig_c1_path, fig_c2_path]:
        if os.path.exists(path):
            row_c.append(_scaled_image(path, 6.8))
        else:
            row_c.append(_placeholder(os.path.basename(path), 6.8))
    t_c = Table([row_c], colWidths=[7.5*cm, 7.5*cm])
    t_c.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_c)
    story.append(Paragraph(
        "Figure 6 & 7 — Contributions (%) des variables à PC1 (gauche) et PC2 (droite). "
        "La ligne rouge marque le seuil attendu sous hypothèse d'équicontribution.",
        S['caption']))

    for obs in [
        "Sur PC1 : TotalGold, MinionsKilled, DmgDealt et kills dominent.",
        "Sur PC2 : visionScore et assists dominent — dimension support/vision.",
        "DragonKills contribue peu aux deux premiers axes (information spécifique "
        "au JUNGLE, capturée par les axes suivants).",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))

    story.append(Paragraph("5.4  Projection des individus par Lane", S['h2']))
    story.extend(include_figure("08_acp_individus_lane.png", S,
        "Figure 8 — Projection des individus sur PC1/PC2, colorés par Lane. "
        "Les ellipses de confiance (95 %) entourent chaque groupe.", 13.5))

    for obs in [
        "<b>UTILITY</b> occupe un quadrant distinct (PC1 négatif / PC2 positif) : "
        "peu d'activité offensive, fort visionScore.",
        "<b>MIDDLE et BOTTOM</b> se concentrent dans la zone PC1 élevé.",
        "<b>JUNGLE</b> se distingue sur l'axe PC3 via DragonKills et DmgTaken.",
        "Les ellipses se chevauchent partiellement → les stats brutes ne séparent "
        "pas parfaitement les rôles, mais une structure existe. C'est le point de "
        "départ du clustering.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 6 — CLASSIFICATION NON SUPERVISÉE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 6 — Classification non supervisée", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph(
        "La classification non supervisée cherche à regrouper les observations "
        "en classes homogènes <b>sans utiliser la variable Lane comme cible</b>. "
        "Deux méthodes complémentaires sont appliquées : K-means et CAH (Classification "
        "Ascendante Hiérarchique). Le clustering est réalisé sur les "
        "<b>4 coordonnées ACP retenues</b> afin de réduire le bruit et la redondance.",
        S['body']))

    story.append(Paragraph("6.1  Nombre optimal de clusters", S['h2']))
    story.extend(include_figure("09_kmeans_k_optimal.png", S,
        "Figure 9 — Méthode du coude (WSS, gauche) et score de silhouette (droite) "
        "pour k ∈ [1, 8]. Le score de silhouette est maximisé à k = 5.", 14))

    for obs in [
        "<b>Méthode du coude</b> : la décroissance de l'inertie intra-classe "
        "(WSS) marque un coude visible à k = 4–5.",
        "<b>Score de silhouette</b> : maximum à k = 5, indiquant la partition "
        "la mieux séparée et la plus cohérente.",
        "k = 5 correspond naturellement aux <b>5 rôles du jeu</b>.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))
    story.append(result_box(
        ["<b>k = 5</b> retenu — cohérent avec le score de silhouette et les 5 rôles LoL"],
        S, "Choix du nombre de clusters"))

    story.append(Paragraph("6.2  K-means — Visualisation des clusters", S['h2']))
    story.extend(include_figure("10_kmeans_clusters.png", S,
        "Figure 10 — Visualisation K-means (5 clusters) sur les axes PC1/PC2. "
        "Chaque couleur représente un cluster.", 13))
    story.append(Paragraph(
        "Les cinq clusters sont bien séparés dans le plan factoriel, avec des "
        "chevauchements minimes aux frontières. Chaque cluster correspond à un "
        "profil de joueur sémantiquement interprétable.", S['body']))

    story.append(Paragraph("6.3  CAH — Dendrogramme", S['h2']))
    story.extend(include_figure("11_cah_dendrogramme.png", S,
        "Figure 11 — Dendrogramme de la CAH (méthode de Ward, distance euclidienne, "
        "n = 2 000). Les rectangles colorés délimitent les 5 groupes.", 14))
    story.append(Paragraph(
        "Le dendrogramme <b>confirme la structure en 5 groupes</b>. Les sauts de "
        "hauteur importants (grandes barres verticales) entre niveaux de fusion "
        "indiquent que ces groupes sont bien séparés. La cohérence avec le "
        "K-means valide la robustesse de la partition.", S['body']))

    story.append(Paragraph("6.4  Profils des clusters", S['h2']))
    story.extend(include_figure("12_clusters_heatmap.png", S,
        "Figure 12 — Heatmap des profils de clusters (z-scores). "
        "Bleu = valeur faible, rouge = valeur élevée.", 14))

    clust_data = [
        ["Cluster",            "n",     "Kills", "Assists", "Vision", "Win %"],
        ["C1 – Support passif","2 851", "2,0",   "3,5",     "17,5",   "37,5 %"],
        ["C2 – Support/Utility","2 125","2,8",   "15,0",    "71,6",   "54,5 %"],
        ["C3 – Solo Laner",    "4 096", "5,4",   "5,6",     "17,8",   "42,7 %"],
        ["C4 – Carry dominant","2 356", "10,6",  "10,6",    "23,3",   "58,7 %"],
        ["C5 – Jungler",       "1 298", "7,9",   "8,6",     "28,0",   "55,0 %"],
    ]
    story.append(header_table(
        clust_data[0], clust_data[1:], S,
        col_widths=[4.2*cm, 1.8*cm, 1.8*cm, 2.0*cm, 2.0*cm, 2.2*cm]
    ))
    story.append(Paragraph(
        "Tableau 6 — Profils moyens des 5 clusters K-means.", S['caption']))

    story.append(Paragraph("<b>Interprétation des clusters :</b>", S['h3']))
    cluster_interps = [
        ("<b>C1 – Support passif</b> (Win = 37,5 %)",
         "Peu de kills, peu d'assists, visionScore faible. Ne correspond pas à un bon "
         "support — joueurs sous-performants ou très prudents. Taux de victoire le "
         "plus faible de tous les clusters."),
        ("<b>C2 – Support/Utility</b> (Win = 54,5 %)",
         "visionScore exceptionnel (71,6), 15 assists en moyenne. Profil clairement "
         "associé au rôle UTILITY. Taux de victoire supérieur à la moyenne."),
        ("<b>C3 – Solo Laner</b> (Win = 42,7 %)",
         "Le cluster le plus peuplé (4 096 joueurs). Stats offensives moyennes, "
         "fort CS (MinionsKilled ≈ 160). Profil typique de TOP ou MID laner."),
        ("<b>C4 – Carry dominant</b> (Win = 58,7 %)",
         "Kills très élevés (10,6), or maximal (16 505). Regroupe les joueurs qui "
         "portent leur équipe. Taux de victoire le plus élevé — impact direct du carry."),
        ("<b>C5 – Jungler</b> (Win = 55,0 %)",
         "DragonKills maximal (1,5 en moyenne), DmgTaken élevé, CS très faible. "
         "Profil très clairement associé au rôle JUNGLE."),
    ]
    for title_str, desc_str in cluster_interps:
        story.append(Paragraph(f"• {title_str} — {desc_str}", S['bullet']))

    story.append(vspace(0.3))
    # Two side-by-side figures
    fig13p = os.path.join(FIGURES, "13_clusters_composition_lane.png")
    fig14p = os.path.join(FIGURES, "14_clusters_composition_rang.png")
    imgs_comp = []
    for path in [fig13p, fig14p]:
        if os.path.exists(path):
            imgs_comp.append(_scaled_image(path, 6.8))
        else:
            imgs_comp.append(_placeholder(os.path.basename(path), 6.8))
    t_comp = Table([imgs_comp], colWidths=[7.5*cm, 7.5*cm])
    t_comp.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_comp)
    story.append(Paragraph(
        "Figure 13 & 14 — Composition des clusters par Lane réelle (gauche) "
        "et par rang ELO (droite).",
        S['caption']))

    story.append(Paragraph(
        "Ces figures <b>valident la cohérence des clusters</b> en les croisant "
        "avec les étiquettes réelles : C2 est dominé par UTILITY, C5 par JUNGLE. "
        "C4 (Carry dominant) concentre les joueurs de hauts rangs "
        "(Diamond+), ce qui explique son fort taux de victoire.", S['body']))

    story.append(Paragraph("Biplot ACP + Clusters", S['h2']))
    story.extend(include_figure("15_biplot_acp_clusters.png", S,
        "Figure 15 — Biplot ACP : variables (flèches) et individus colorés "
        "par cluster K-means. Les ellipses de confiance (95 %) entourent chaque cluster.",
        13.5))
    story.append(Paragraph(
        "Le biplot synthétise l'analyse : les flèches visionScore et assists pointent "
        "vers C2 (Support), kills et TotalGold vers C4 (Carry), DmgTaken vers C5 "
        "(Jungler), et MinionsKilled vers C3 (Solo Laner).", S['body']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 7 — APPRENTISSAGE SUPERVISÉ
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 7 — Apprentissage supervisé", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph(
        "L'apprentissage supervisé complète l'analyse non supervisée en cherchant "
        "à <b>prédire une cible</b> à partir des variables de performance. "
        "Dans les deux cas, une partition <b>80 % / 20 %</b> stratifiée "
        "(train / test) est utilisée via le package caret.", S['body']))

    story.append(Paragraph("7.1  Régression logistique — Prédire la Victoire", S['h2']))
    story.append(Paragraph(
        "La régression logistique modélise la probabilité de victoire :", S['body']))
    story.append(Paragraph(
        "P(Win = 1 | X) = 1 / (1 + exp(-[β₀ + β₁·kills + β₂·deaths + … + β₁₀·DragonKills]))",
        ParagraphStyle('formula', fontName='Courier', fontSize=9.5,
                       textColor=C_BLUE, alignment=TA_CENTER,
                       spaceBefore=6, spaceAfter=6, leading=14)))

    story.extend(include_figure("16_logreg_coefficients.png", S,
        "Figure 16 — Coefficients de la régression logistique (log-odds). "
        "Vert = effet positif sur la victoire, rouge = effet négatif.", 13))

    for obs in [
        "<b>kills et TotalGold</b> ont les coefficients positifs les plus élevés : "
        "éliminer des ennemis et accumuler de l'or sont les meilleurs prédicteurs individuels.",
        "<b>deaths</b> a un coefficient fortement négatif : mourir souvent est très "
        "pénalisant (perte d'or pour l'ennemi, perte de contrôle de carte).",
        "<b>TurretDmgDealt</b> a un coefficient positif significatif : attaquer les "
        "structures ennemies participe directement à la victoire.",
        "<b>visionScore</b> a un effet positif modéré, confirmant l'importance "
        "de l'information (vision de carte) dans la stratégie.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))

    story.extend(include_figure("17_logreg_confusion.png", S,
        "Figure 17 — Matrice de confusion de la régression logistique (jeu de test).", 8))

    story.append(result_box([
        "Accuracy ≈ <b>65–70 %</b> sur le jeu de test",
        "Résultat attendu : la victoire dépend des 9 autres joueurs, "
        "pas seulement des stats individuelles",
        "Les variables kills, deaths et TotalGold sont les plus prédictives",
    ], S, "Performance — Régression logistique"))

    story.append(Paragraph("7.2  Forêt aléatoire — Prédire le Rôle (Lane)", S['h2']))
    story.append(Paragraph(
        "Une forêt aléatoire (<i>Random Forest</i>) construit un ensemble de "
        "<b>300 arbres de décision</b> sur des sous-échantillons bootstrap. "
        "La prédiction finale est la classe majoritaire. L'objectif est de prédire "
        "le rôle d'un joueur <b>uniquement à partir de ses stats de performance</b>, "
        "sans lui avoir fourni son rôle.", S['body']))

    story.extend(include_figure("18_rf_importance.png", S,
        "Figure 18 — Importance des variables dans la forêt aléatoire "
        "(Mean Decrease Gini). Plus la valeur est élevée, plus la variable "
        "discrimine les rôles.", 13))

    for obs in [
        "<b>visionScore</b> est de loin la variable la plus discriminante : "
        "elle seule sépare les UTILITY de tous les autres rôles.",
        "<b>assists</b> arrive en deuxième position pour les mêmes raisons.",
        "<b>MinionsKilled</b> (CS) distingue très bien les laners solo "
        "(TOP, MID, BOT) des non-laners (JUNGLE, UTILITY).",
        "<b>DmgTaken</b> discrimine bien JUNGLE et TOP (tanks/frontline) des autres.",
        "<b>DragonKills</b> est spécifique au JUNGLE, d'où son importance élevée.",
    ]:
        story.append(Paragraph(f"• {obs}", S['bullet']))

    story.extend(include_figure("19_rf_confusion.png", S,
        "Figure 19 — Matrice de confusion du Random Forest (jeu de test). "
        "La diagonale représente les bonnes prédictions.", 10))

    story.append(result_box([
        "Accuracy ≈ <b>70–80 %</b> sur le jeu de test",
        "UTILITY prédit avec excellente précision grâce à visionScore",
        "Confusions principales : BOTTOM ↔ MIDDLE (profils offensifs proches) "
        "et TOP ↔ JUNGLE (profils de tank similaires)",
    ], S, "Performance — Forêt aléatoire"))

    story.append(Paragraph("7.3  Comparaison des deux modèles", S['h2']))
    comp_data = [
        ["Modèle",                "Cible",         "Type",         "Accuracy approx."],
        ["Régression logistique", "Win (0/1)",      "Binaire",      "65–70 %"],
        ["Forêt aléatoire",       "Lane (5 roles)", "Multiclasse",  "70–80 %"],
    ]
    story.append(header_table(
        comp_data[0], comp_data[1:], S,
        col_widths=[4.5*cm, 3.5*cm, 3.2*cm, 4.3*cm]
    ))
    story.append(Paragraph(
        "Tableau 7 — Comparaison des deux modèles d'apprentissage supervisé.",
        S['caption']))
    story.append(Paragraph(
        "La prédiction du rôle est plus précise que celle de la victoire, car "
        "les statistiques individuelles déterminent fortement le <i>style de jeu</i>, "
        "mais la victoire dépend aussi des <b>facteurs collectifs</b> (performance "
        "des coéquipiers, composition des champions, stratégie d'équipe).", S['body']))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # CHAPITRE 8 — CONCLUSION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("Chapitre 8 — Conclusion", S['h1']))
    story.append(hr(C_BLUE))

    story.append(Paragraph("8.1  Bilan des analyses", S['h2']))
    story.append(Paragraph(
        "Ce projet a appliqué une chaîne d'analyse multivariée complète sur "
        "un jeu de données de <b>730 000+ parties de League of Legends</b>. "
        "Le tableau ci-dessous synthétise les résultats principaux :", S['body']))

    bilan_data = [
        ["Méthode",              "Résultat principal"],
        ["Prétraitement",        "15 000 obs. stratifiées → ~12 700 après nettoyage outliers"],
        ["ACP",                  "4 axes, 76,95 % variance — PC1 = intensité offensive, PC2 = support/vision"],
        ["K-means / CAH",        "5 clusters bien séparés, cohérents avec les 5 rôles du jeu"],
        ["Régression logistique","Accuracy 65–70 % — kills, deaths et TotalGold sont les plus prédictifs"],
        ["Forêt aléatoire",      "Accuracy 70–80 % — visionScore est la variable la plus discriminante"],
    ]
    story.append(header_table(
        bilan_data[0], bilan_data[1:], S,
        col_widths=[4.5*cm, 11*cm]
    ))
    story.append(Paragraph("Tableau 8 — Synthèse des résultats.", S['caption']))

    story.append(Paragraph("<b>Résultat remarquable :</b>", S['h3']))
    story.append(Paragraph(
        "La classification non supervisée (K-means, k=5) reproduit fidèlement "
        "les 5 rôles du jeu <i>sans jamais utiliser la variable Lane</i>. "
        "Cela démontre que les statistiques de performance portent une information "
        "structurée et suffisante pour caractériser les profils de joueurs. "
        "Le cluster <b>Carry dominant</b> présente le taux de victoire le plus "
        "élevé (58,7 %), confirmant l'impact décisif d'un joueur offensif "
        "très performant sur le résultat de la partie.", S['body']))

    story.append(Paragraph("8.2  Limites", S['h2']))
    for limit in [
        "<b>Biais d'échantillonnage</b> : l'échantillon stratifié force l'équilibre "
        "entre les lanes, alors que dans les données réelles la distribution peut différer.",
        "<b>Prédiction de la victoire limitée</b> : les stats individuelles ne capturent "
        "pas la coordination d'équipe, la composition de champions ni la stratégie globale.",
        "<b>Évolution temporelle ignorée</b> : les patchs du jeu modifient régulièrement "
        "l'équilibre entre rôles et champions — l'analyse est une photographie statique.",
    ]:
        story.append(Paragraph(f"• {limit}", S['bullet']))

    story.append(Paragraph("8.3  Perspectives", S['h2']))
    for persp in [
        "Inclure les données d'équipe (TeamMatchTbl) pour des prédictions de victoire "
        "au niveau équipe (10 joueurs).",
        "Appliquer XGBoost ou un réseau de neurones pour améliorer la prédiction de Lane.",
        "Analyser l'évolution des profils en fonction du rang ELO pour comprendre "
        "comment le style de jeu évolue avec le niveau.",
        "Ajouter une dimension temporelle (évolution par saison / patch).",
    ]:
        story.append(Paragraph(f"• {persp}", S['bullet']))

    story.append(vspace(1))
    story.append(hr(C_BLUE))
    story.append(Paragraph(
        "<i>Rapport généré automatiquement — Script Python (reportlab 4.4) + R (FactoMineR, randomForest, caret)</i>",
        ParagraphStyle('footer_note', fontName='Helvetica-Oblique', fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    # ── Génération ────────────────────────────────────────────────────────────
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"\nRapport genere : {os.path.abspath(OUTPUT)}")
    print(f"Taille : {os.path.getsize(OUTPUT) // 1024} Ko")


if __name__ == "__main__":
    build_doc()
