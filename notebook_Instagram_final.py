"""Rush 4 — Usage d'Instagram et bien-être : application Streamlit finale.

Lancement depuis le dossier du projet :

    streamlit run notebook_Instagram_final.py

Règle de confidentialité : l'application ne manipule que des résultats agrégés.
Aucune ligne individuelle n'est affichée, et aucun groupe de moins de 100 utilisateurs.
"""
import inspect
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Rush 4 · Instagram et bien-être", layout="wide")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DOSSIER = Path(__file__).resolve().parent
FICHIER = DOSSIER / "data" / "instagram_usage_lifestyleSafe.csv"
FICHIER_AUTRE = DOSSIER / "data" / "instagram_users_lifestyleSafe.csv"

STRESS = "perceived_stress_score"
BONHEUR = "self_reported_happiness"
TEMPS = "daily_active_minutes_instagram"
MIN_N = 100  # taille minimale d'un groupe affiché

SEGMENTS = ["S1 Très occasionnel", "S2 Occasionnel", "S3 Modéré", "S4 Soutenu", "S5 Intensif", "S6 Très intensif"]
BORNES_SEGMENTS = [0, 20, 88, 188, 240, 290, np.inf]
DUREES_SEGMENTS = ["< 20 min", "20–88 min", "88–188 min", "188–240 min", "240–290 min", "> 290 min"]
COURTS = ["S1", "S2", "S3", "S4", "S5", "S6"]
TRANCHES_AGE = ["13–17 ans", "18–24 ans", "25–34 ans", "35–44 ans", "45–54 ans", "55–65 ans"]
GROUPES_AGE = ["13–17 ans", "18–34 ans", "35–54 ans", "55–65 ans"]
BORNES_GROUPES_AGE = [13, 18, 35, 55, 66]
PROFILS = ["Serein et heureux", "Serein mais peu heureux", "Stressé mais heureux", "Stressé et peu heureux"]
PROFILS_PUBLICATION = ["Consommateur (0 à 3 publications)", "Intermédiaire (4 à 7)", "Créateur (8 et plus)"]
QUINTILES = ["Q1 le plus public", "Q2", "Q3", "Q4", "Q5 le plus privé"]
COMPTES = {"Public": "Public", "Friends only": "Amis seulement", "Private": "Privé"}
PAYS = {"United States": "États-Unis", "India": "Inde", "Brazil": "Brésil", "Other": "Autres pays",
        "United Kingdom": "Royaume-Uni", "Canada": "Canada", "Australia": "Australie",
        "South Korea": "Corée du Sud", "Germany": "Allemagne", "Japan": "Japon"}

# Couleurs (palette vérifiée pour les daltonismes les plus courants)
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLEU, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMPE_4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


# ---------------------------------------------------------------------------
# Outils de mise en forme
# ---------------------------------------------------------------------------
def fr(valeur, decimales=1):
    """Écrit un nombre à la française : virgule décimale, espace pour les milliers."""
    if pd.isna(valeur):
        return "—"
    if round(valeur, decimales) == 0:
        valeur = 0.0
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def pourcent(valeur, decimales=0, signe=False):
    texte = fr(valeur, decimales)
    return f"+{texte} %" if signe and round(valeur, decimales) > 0 else f"{texte} %"


def tableau(table, decimales=1):
    """Tableau agrégé avec des nombres au format français."""
    def formater(v):
        if isinstance(v, (bool, np.bool_)):
            return "oui" if v else "non"
        if isinstance(v, (int, np.integer)):
            return fr(v, 0)
        if isinstance(v, (float, np.floating)):
            return fr(v, decimales)
        return v
    st.table(table.apply(lambda colonne: colonne.map(formater)))


def chiffres(table, decimales=1, titre="Voir les chiffres"):
    with st.expander(titre):
        tableau(table, decimales)


def habiller(graphique):
    """Style commun à tous les graphiques."""
    return (graphique
            .configure(background=SURFACE, font="system-ui, -apple-system, Segoe UI, sans-serif")
            .configure_view(strokeWidth=0)
            .configure_mark(tooltip=False)  # seules les infobulles prévues s'affichent
            .configure_axis(gridColor=GRID, domainColor=AXIS, tickColor=AXIS, labelColor=INK2,
                            titleColor=INK2, labelFontSize=12, titleFontSize=12, titleFontWeight=400,
                            labelPadding=6, titlePadding=10)
            .configure_legend(orient="bottom", direction="horizontal", labelColor=INK2, titleColor=INK2,
                              labelFontSize=12, titleFontSize=12, columnPadding=18, symbolStrokeWidth=0, labelLimit=360)
            .configure_title(color=INK, fontSize=15, fontWeight=600, anchor="start", subtitleColor=INK2,
                             subtitleFontSize=12.5, subtitlePadding=6, offset=14))


_LARGEUR = ({"width": "stretch"} if "width" in inspect.signature(st.altair_chart).parameters
            else {"use_container_width": True})


def montrer(graphique):
    st.altair_chart(habiller(graphique), theme=None, **_LARGEUR)


def titre(texte, sous_titre):
    return alt.TitleParams(texte, subtitle=sous_titre)


AXE_HEURES = alt.Axis(values=list(range(0, 9)), labelExpr="datum.value + ' h'", grid=True)
AXE_POURCENT = alt.Axis(labelExpr="datum.value + ' %'")


def retenir(texte):
    st.success(f"**Ce qu'on retient :** {texte}")


def conclusion_produit(texte):
    st.info(f"**Conclusion pour les équipes produit :** {texte}")


def barres_simples(data, x, y, etiquette, titre_graphique, x_titre, y_titre, ordre, domaine_y,
                   tooltip, couleur=BLEU, hauteur=320, axe_y=None, angle=0):
    """Barres verticales avec la valeur écrite au-dessus de chaque barre."""
    base = alt.Chart(data).encode(
        x=alt.X(f"{x}:N", sort=ordre, title=x_titre, axis=alt.Axis(labelAngle=angle, labelLimit=160)),
        y=alt.Y(f"{y}:Q", title=y_titre, scale=alt.Scale(domain=domaine_y), axis=axe_y),
    )
    barres = base.mark_bar(size=34, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=couleur).encode(tooltip=tooltip)
    textes = base.mark_text(dy=-9, fontSize=12.5, color=INK).encode(text=f"{etiquette}:N")
    return (barres + textes).properties(title=titre_graphique, height=hauteur)


def barres_groupees(data, x, serie, y, etiquette, ordre_x, series, couleurs, titre_graphique, x_titre, y_titre,
                    domaine_y, tooltip, hauteur=330, axe_y=None, angle=0):
    """Barres groupées : une couleur par série, la valeur au-dessus de chaque barre."""
    base = alt.Chart(data).encode(
        x=alt.X(f"{x}:N", sort=ordre_x, title=x_titre, axis=alt.Axis(labelAngle=angle, labelLimit=170)),
        xOffset=alt.XOffset(f"{serie}:N", sort=series),
        y=alt.Y(f"{y}:Q", title=y_titre, scale=alt.Scale(domain=domaine_y), axis=axe_y),
    )
    barres = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        color=alt.Color(f"{serie}:N", scale=alt.Scale(domain=series, range=couleurs), title=None,
                        legend=alt.Legend(columns=len(series))),
        tooltip=tooltip)
    textes = base.mark_text(dy=-8, fontSize=10.5, color=INK2).encode(text=f"{etiquette}:N")
    return (barres + textes).properties(title=titre_graphique, height=hauteur)


def carte_chaleur(data, x, y, valeur, etiquette, ordre_x, ordre_y, domaine, titre_legende, seuil_blanc,
                  tooltip, titre_graphique, x_titre, hauteur=290, surligner=None):
    base = alt.Chart(data).encode(
        x=alt.X(f"{x}:N", sort=ordre_x, title=x_titre, axis=alt.Axis(labelAngle=0, ticks=False, domain=False, labelLimit=160)),
        y=alt.Y(f"{y}:N", sort=ordre_y, title=None, axis=alt.Axis(ticks=False, domain=False)))
    cases = base.mark_rect(stroke=SURFACE, strokeWidth=2).encode(
        color=alt.Color(f"{valeur}:Q", scale=alt.Scale(domain=domaine, range=SEQ),
                        legend=alt.Legend(title=titre_legende, orient="right", direction="vertical", gradientLength=170)),
        tooltip=tooltip)
    textes = base.mark_text(fontSize=12.5).encode(
        text=f"{etiquette}:N", color=alt.condition(f"datum.{valeur} >= {seuil_blanc}", alt.value("white"), alt.value(INK)))
    couches = cases + textes
    if surligner is not None:
        couches = couches + alt.Chart(pd.DataFrame([surligner])).mark_rect(fill=None, stroke=ORANGE, strokeWidth=4).encode(
            x=alt.X(f"{x}:N", sort=ordre_x), y=alt.Y(f"{y}:N", sort=ordre_y))
    return couches.properties(title=titre_graphique, height=hauteur)


def libelle_tranche(minutes, largeur=30):
    fin = minutes + largeur
    return f"{minutes // 60} h {minutes % 60:02d} à {fin // 60} h {fin % 60:02d}"


# ---------------------------------------------------------------------------
# Calculs (résultats agrégés uniquement)
# ---------------------------------------------------------------------------
def agreger(data, cles, **mesures):
    table = data.groupby(cles, observed=True).agg(n=(STRESS, "size"), **mesures)
    return table[table["n"] >= MIN_N]


def part_expliquee(data, y, cles):
    moyenne_groupe = data.groupby(cles, observed=True)[y].transform("mean")
    return 1 - ((data[y] - moyenne_groupe) ** 2).sum() / ((data[y] - data[y].mean()) ** 2).sum()


def a_temps_egal(data, colonne, groupes="tranche_10min"):
    """Valeur ramenée à temps passé égal : écart à la moyenne de la même tranche de 10 min, plus la moyenne générale."""
    return data[colonne] - data.groupby(groupes)[colonne].transform("mean") + data[colonne].mean()


def lien_a_temps_egal(data, colonne, cible=STRESS):
    rx, ry = data[colonne].rank(pct=True), data[cible].rank(pct=True)
    rx = rx - rx.groupby(data["tranche_10min"]).transform("mean")
    ry = ry - ry.groupby(data["tranche_10min"]).transform("mean")
    return float(np.corrcoef(rx, ry)[0, 1])


@st.cache_data(show_spinner="Calcul des résultats…")
def calculer():
    df = pd.read_csv(FICHIER)
    r = {"n": len(df), "n_colonnes": df.shape[1], "manquants": int(df.isna().sum().sum()),
         "doublons": int(df.drop(columns="user_id").duplicated().sum()),
         "doublons_id": int(df["user_id"].duplicated().sum())}

    # --- Nettoyage : incohérences métier (signalées, pas supprimées)
    age_creation = df["age"] - (2025 - df["account_creation_year"])
    drapeaux = pd.DataFrame({
        "flag_compte_avant_13_ans": age_creation < 13,
        "flag_mineur_salarie": (df["age"] < 18) & df["employment_status"].isin(["Full-time employed", "Part-time", "Freelancer"]),
        "flag_mineur_marie": (df["age"] < 18) & df["relationship_status"].isin(["Married", "Divorced", "Widowed"]),
        "flag_sans_emploi_avec_heures": df["employment_status"].isin(["Unemployed", "Retired"]) & (df["weekly_work_hours"] > 0),
    })
    r["drapeaux"] = pd.DataFrame({
        "règle": ["Compte créé avant 13 ans (âge − ancienneté du compte)", "Mineur salarié (temps plein, partiel ou indépendant)",
                  "Mineur marié, divorcé ou veuf", "Sans emploi (chômeur ou retraité) qui déclare des heures de travail"],
        "part des lignes (%)": drapeaux.mean().mul(100).to_numpy(),
    }, index=list(drapeaux.columns)).rename_axis("indicateur")
    signalees = drapeaux.any(axis=1)
    r["part_signalees"] = float(signalees.mean() * 100)
    propre = df[~signalees]
    moyenne_propre = propre.groupby(propre[TEMPS] // 10)[STRESS].transform("mean")
    r["r2_sans_signalees"] = float(1 - ((propre[STRESS] - moyenne_propre) ** 2).sum() / ((propre[STRESS] - propre[STRESS].mean()) ** 2).sum())
    r["inutiles"] = pd.DataFrame({
        "constat": [f"une seule valeur : « {df['app_name'].iloc[0]} »",
                    f"variation de {fr(df['daily_steps_count'].std() / df['daily_steps_count'].mean() * 100, 1)} % autour de la moyenne",
                    f"égale aux minutes ÷ sessions (écart maximal : {fr((df[TEMPS] / df['sessions_per_day'] - df['average_session_length_minutes']).abs().max(), 2)} min)"],
    }, index=["app_name", "daily_steps_count", "average_session_length_minutes"]).rename_axis("colonne")

    # --- Choix du fichier
    r["comparaison"] = None
    if FICHIER_AUTRE.exists():
        autre = pd.read_csv(FICHIER_AUTRE)
        differences = pd.Series({c: int((df[c].astype(str) != autre[c].astype(str)).sum()) for c in autre.columns})
        mineurs = df["age"] < 18
        utilisees = [STRESS, BONHEUR, TEMPS, "age", "sleep_hours_per_night", "daily_steps_count", "exercise_hours_per_week",
                     "sessions_per_day", "average_session_length_minutes", "likes_given_per_day", "comments_written_per_day",
                     "posts_created_per_week", "dms_sent_per_week", "privacy_setting_level", "country"]
        r["comparaison"] = {
            "identiques": int((differences == 0).sum()), "total": len(differences),
            "differences": differences[differences > 0].rename("lignes différentes").to_frame().rename_axis("colonne"),
            "mineurs": pd.DataFrame({
                "fichier usage (analysé)": {
                    "part déclarée salariée à temps plein (%)": (df.loc[mineurs, "employment_status"] == "Full-time employed").mean() * 100,
                    "heures de travail par semaine (moyenne)": df.loc[mineurs, "weekly_work_hours"].mean()},
                "fichier users (autre version)": {
                    "part déclarée salariée à temps plein (%)": (autre.loc[mineurs, "employment_status"] == "Full-time employed").mean() * 100,
                    "heures de travail par semaine (moyenne)": autre.loc[mineurs, "weekly_work_hours"].mean()}}),
            "n_mineurs": int(mineurs.sum()),
            "utilisees_identiques": all(df[c].astype(str).equals(autre[c].astype(str)) for c in utilisees),
        }
        del autre

    # --- Variables construites
    df["heures"] = df[TEMPS] / 60
    df["tranche_10min"] = (df[TEMPS] // 10).astype(int)
    df["tranche_30min"] = ((df[TEMPS] // 30) * 30).astype(int)
    df["segment"] = pd.cut(df[TEMPS], BORNES_SEGMENTS, right=False, labels=SEGMENTS)
    df["tranche_age"] = pd.cut(df["age"], [13, 18, 25, 35, 45, 55, 66], right=False, labels=TRANCHES_AGE)
    df["groupe_age"] = pd.cut(df["age"], BORNES_GROUPES_AGE, right=False, labels=GROUPES_AGE)
    df["stress_eleve"] = df[STRESS] >= 27
    df["tres_heureux"] = df[BONHEUR] >= 9
    df["tres_malheureux"] = df[BONHEUR] <= 2
    df["tranche_10min_age"] = df["tranche_10min"].astype(str) + "_" + df["age"].astype(str)

    r["apport"] = pd.DataFrame({"part du stress expliquée (%)": [
        part_expliquee(df, STRESS, ["tranche_10min"]) * 100,
        part_expliquee(df, STRESS, ["segment"]) * 100,
        part_expliquee(df, STRESS, ["segment", "groupe_age"]) * 100,
    ]}, index=["temps passé, par tranches de 10 min (référence)", "6 segments de temps passé (S1 à S6)",
               "6 segments × 4 groupes d'âge (notre segmentation)"])
    niveaux = pd.cut(df[STRESS], [-1, 13, 26, 40], labels=["faible (0–13)", "modéré (14–26)", "élevé (27–40)"])
    r["niveaux"] = niveaux.value_counts(normalize=True).mul(100).sort_index().to_frame("part (%)").rename_axis("niveau")

    # --- 1. Hypothèses non concluantes
    r["sommeil"] = agreger(df, "segment", sommeil_moyen=("sleep_hours_per_night", "mean"),
                           part_moins_de_6h=("sleep_hours_per_night", lambda s: (s < 6).mean() * 100))
    r["activite"] = agreger(df, "segment", pas_par_jour=("daily_steps_count", "mean"),
                            sport_heures_semaine=("exercise_hours_per_week", "mean"))
    noms_vie = (("sleep_hours_per_night", "Sommeil"), ("daily_steps_count", "Pas par jour"), ("exercise_hours_per_week", "Sport"))
    r["correlations_vie"] = pd.DataFrame({
        "lien avec le temps passé": {nom: df[c].corr(df[TEMPS], method="spearman") for c, nom in noms_vie},
        "lien avec le stress": {nom: df[c].corr(df[STRESS], method="spearman") for c, nom in noms_vie},
        "lien avec le bonheur": {nom: df[c].corr(df[BONHEUR], method="spearman") for c, nom in noms_vie}})
    r["pas_bornes"] = (df["daily_steps_count"].quantile(0.01), df["daily_steps_count"].quantile(0.99))
    df["stress_temps_egal"] = a_temps_egal(df, STRESS)
    df["bonheur_temps_egal"] = a_temps_egal(df, BONHEUR)
    pays = agreger(df, "country", minutes=(TEMPS, "mean"), stress=(STRESS, "mean"), bonheur=(BONHEUR, "mean"),
                   stress_temps_egal=("stress_temps_egal", "mean"), bonheur_temps_egal=("bonheur_temps_egal", "mean"))
    pays.index = [PAYS[p] for p in pays.index]
    r["pays"] = pays.sort_values("n", ascending=False)

    # --- 2. Temps passé
    r["segments_temps"] = agreger(df, "segment", minutes=(TEMPS, "mean"), stress=(STRESS, "mean"), bonheur=(BONHEUR, "mean"),
                                  part_stress_eleve=("stress_eleve", lambda s: s.mean() * 100))
    r["stress_30min"] = agreger(df, "tranche_30min", stress=(STRESS, "mean"), bonheur=(BONHEUR, "mean"),
                                q1=(STRESS, lambda s: s.quantile(0.25)), q3=(STRESS, lambda s: s.quantile(0.75)))
    r["pente"] = float(np.polyfit(df["heures"], df[STRESS], 1)[0])
    r["r2_stress"] = part_expliquee(df, STRESS, ["tranche_10min"])
    r["r2_bonheur"] = part_expliquee(df, BONHEUR, ["tranche_10min"])
    r["bonheur_segments"] = agreger(df, "segment", part_tres_heureux=("tres_heureux", lambda s: s.mean() * 100),
                                    part_tres_malheureux=("tres_malheureux", lambda s: s.mean() * 100))
    r["profils_temps"] = pd.DataFrame({
        groupe: {"temps médian par jour (min)": df.loc[masque, TEMPS].median(),
                 "le quart qui y passe le moins : moins de (min)": df.loc[masque, TEMPS].quantile(0.25),
                 "sessions par jour": df.loc[masque, "sessions_per_day"].mean()}
        for groupe, masque in (("Plus heureux (9–10)", df["tres_heureux"]), ("Autres", ~df["tres_heureux"]),
                               ("Moins heureux (1–2)", df["tres_malheureux"]))})
    activite = {"likes_given_per_day": "Likes donnés", "stories_viewed_per_day": "Stories vues",
                "time_on_feed_per_day": "Temps sur le fil", "time_on_reels_per_day": "Temps sur les Reels",
                "comments_written_per_day": "Commentaires", "dms_received_per_week": "Messages reçus",
                "ads_viewed_per_day": "Publicités vues", "sessions_per_day": "Sessions par jour"}
    r["copies"] = pd.Series({nom: df[c].corr(df[TEMPS], method="spearman") for c, nom in activite.items()},
                            name="corrélation avec le temps passé").to_frame()

    # --- 3. Âge
    r["age_s4"] = agreger(df[df["segment"] == "S4 Soutenu"], "tranche_age", minutes=(TEMPS, "mean"), stress=(STRESS, "mean"))
    r["grille_age"] = agreger(df, ["tranche_age", "segment"], stress=(STRESS, "mean"))
    ecart = df[STRESS] - df.groupby("tranche_10min")[STRESS].transform("mean")
    r["pente_age"] = float(np.polyfit(df["age"], ecart, 1)[0] * 10)
    r["exposition"] = agreger(df, "tranche_age", minutes=(TEMPS, "mean"),
                              part_3h_ou_plus=(TEMPS, lambda s: (s >= 180).mean() * 100))

    # --- 4. Habitudes d'utilisation
    comportements = {"sessions_per_day": "Sessions par jour", "reels_watched_per_day": "Reels vus par jour",
                     "stories_viewed_per_day": "Stories vues par jour", "likes_given_per_day": "Likes donnés par jour",
                     "comments_written_per_day": "Commentaires par jour", "dms_sent_per_week": "Messages envoyés par semaine",
                     "time_on_feed_per_day": "Temps sur le fil (min par jour)", "time_on_reels_per_day": "Temps sur les Reels (min par jour)",
                     TEMPS: "Temps total sur Instagram (min par jour)", "user_engagement_score": "Score d'engagement"}
    lignes = []
    for colonne, nom in comportements.items():
        moins, plus = df.loc[df["tres_malheureux"], colonne].mean(), df.loc[df["tres_heureux"], colonne].mean()
        if colonne == TEMPS:
            moins_egal = plus_egal = np.nan
        else:
            valeur_egale = a_temps_egal(df, colonne)
            moins_egal, plus_egal = valeur_egale[df["tres_malheureux"]].mean(), valeur_egale[df["tres_heureux"]].mean()
        lignes.append((nom, moins, plus, (moins / plus - 1) * 100, (moins_egal / plus_egal - 1) * 100))
    r["usage_bonheur"] = pd.DataFrame(lignes, columns=["comportement", "moins heureux (1–2)", "plus heureux (9–10)",
                                                       "différence (%)", "différence à temps égal (%)"]).set_index("comportement")
    r["n_moins_plus"] = (int(df["tres_malheureux"].sum()), int(df["tres_heureux"].sum()))
    df["interactions_par_minute"] = (df["likes_given_per_day"] + df["comments_written_per_day"]) / df[TEMPS]
    r["engagement_liens"] = (float(df["user_engagement_score"].corr(df[TEMPS], method="spearman")),
                             float(df["user_engagement_score"].corr(df["interactions_par_minute"], method="spearman")))

    df["profil_publication"] = pd.cut(df["posts_created_per_week"], [-1, 3, 7, 1000], labels=PROFILS_PUBLICATION)
    df["bonheur_temps_age_egaux"] = a_temps_egal(df, BONHEUR, "tranche_10min_age")
    df["stress_temps_age_egaux"] = a_temps_egal(df, STRESS, "tranche_10min_age")
    createurs = agreger(df, "profil_publication", age=("age", "mean"), minutes=(TEMPS, "mean"), bonheur=(BONHEUR, "mean"),
                        tres_heureux=("tres_heureux", lambda s: s.mean() * 100),
                        tres_malheureux=("tres_malheureux", lambda s: s.mean() * 100), stress=(STRESS, "mean"),
                        bonheur_egal=("bonheur_temps_age_egaux", "mean"), stress_egal=("stress_temps_age_egaux", "mean"))
    createurs.insert(1, "part", createurs["n"] / len(df) * 100)
    r["createurs"] = createurs
    r["publications_age"] = agreger(df, "tranche_age", publications=("posts_created_per_week", "mean"))

    df["part_privee"] = (df["dms_sent_per_week"] / 7) / (df["dms_sent_per_week"] / 7 + df["likes_given_per_day"] + df["comments_written_per_day"]) * 100
    df["quintile_prive"] = pd.qcut(df["part_privee"].rank(method="first"), 5, labels=QUINTILES)
    vers_90 = df[(df[TEMPS] >= 75) & (df[TEMPS] <= 105)]
    r["n_vers_90"] = len(vers_90)
    prive = {}
    for groupe, ordre in (("quintile_prive", QUINTILES), ("privacy_setting_level", list(COMPTES))):
        prive[groupe] = pd.DataFrame({
            "minutes": df.groupby(groupe, observed=True)[TEMPS].mean(),
            "stress": df.groupby(groupe, observed=True)[STRESS].mean(),
            "stress_temps_egal": df.groupby(groupe, observed=True)["stress_temps_egal"].mean(),
            "stress_vers_90": vers_90.groupby(groupe, observed=True)[STRESS].mean(),
            "bonheur": df.groupby(groupe, observed=True)[BONHEUR].mean(),
            "bonheur_temps_egal": df.groupby(groupe, observed=True)["bonheur_temps_egal"].mean(),
            "bonheur_vers_90": vers_90.groupby(groupe, observed=True)[BONHEUR].mean(),
            "n_vers_90": vers_90.groupby(groupe, observed=True).size(),
        }).reindex(ordre)
    prive["privacy_setting_level"].index = [COMPTES[c] for c in prive["privacy_setting_level"].index]
    r["prive"] = prive

    mediane_sessions, mediane_duree = df["sessions_per_day"].median(), df["average_session_length_minutes"].median()
    reflexe = (df["sessions_per_day"] > mediane_sessions) & (df["average_session_length_minutes"] < mediane_duree)
    immersion = (df["sessions_per_day"] < mediane_sessions) & (df["average_session_length_minutes"] > mediane_duree)
    df["profil_connexion"] = np.select([reflexe, immersion], ["Réflexe", "Immersion"], default="Autre")
    connexion = agreger(df[df["profil_connexion"] != "Autre"], "profil_connexion", sessions=("sessions_per_day", "mean"),
                        duree=("average_session_length_minutes", "mean"), minutes=(TEMPS, "mean"),
                        stress=(STRESS, "mean"), bonheur=(BONHEUR, "mean")).reindex(["Réflexe", "Immersion"])
    meme_temps = df[(df[TEMPS] >= 120) & (df[TEMPS] < 180) & (df["profil_connexion"] != "Autre")]
    connexion_meme_temps = agreger(meme_temps, "profil_connexion", minutes=(TEMPS, "mean"), stress=(STRESS, "mean"),
                                   bonheur=(BONHEUR, "mean")).reindex(["Réflexe", "Immersion"])
    r["connexion"] = connexion
    r["connexion_meme_temps"] = connexion_meme_temps
    r["medianes_connexion"] = (float(mediane_sessions), float(mediane_duree))

    # --- 6. Segmentation
    segments = agreger(df, ["groupe_age", "segment"], stress=(STRESS, "mean"),
                       part_stress_eleve=("stress_eleve", lambda s: s.mean() * 100))
    r["segments"] = segments
    grille = segments["part_stress_eleve"].unstack("segment")
    moitie = np.where(df["user_id"] % 2 == 0, "A", "B")
    stabilite = (df.assign(moitie=moitie).groupby(["moitie", "groupe_age", "segment"], observed=True)["stress_eleve"]
                 .mean().mul(100).unstack("moitie"))
    ecarts_age = grille.max() - grille.min()
    r["criteres"] = pd.DataFrame([
        ("1. Distingue bien le bien-être", "part en stress élevé, du segment le plus bas au plus haut",
         f"de {fr(grille.min().min(), 0)} % à {fr(grille.max().max(), 0)} %"),
        ("2. Apporte plus que le temps seul", "plus grand écart entre groupes d'âge dans un même segment de temps",
         f"{fr(ecarts_age.max(), 0)} points ({ecarts_age.idxmax()})"),
        ("3. S'applique à tout utilisateur", "valeurs manquantes dans l'âge et le temps passé",
         str(int(df[["age", TEMPS]].isna().sum().sum()))),
        ("4. Est stable", "plus grand écart entre deux moitiés du fichier",
         f"{fr((stabilite['A'] - stabilite['B']).abs().max(), 1)} points"),
        ("5. N'isole personne", "plus petit segment",
         f"{fr(df.groupby(['groupe_age', 'segment'], observed=True).size().min(), 0)} utilisateurs"),
        ("6. Aucune donnée de santé", "variables utilisées", "âge et temps passé par jour"),
    ], columns=["critère", "mesure", "résultat"]).set_index("critère")
    profil = np.select([~df["stress_eleve"] & (df[BONHEUR] >= 7), ~df["stress_eleve"] & (df[BONHEUR] < 7),
                        df["stress_eleve"] & (df[BONHEUR] >= 7)], PROFILS[:3], default=PROFILS[3])
    r["profils"] = pd.crosstab(df["segment"], profil, normalize="index").mul(100)[PROFILS]

    # --- 7. Protection des données
    r["segment_max"] = segments["part_stress_eleve"].idxmax()
    r["part_max"] = float(segments["part_stress_eleve"].max())
    revelateurs = segments[segments["part_stress_eleve"] >= 80]
    r["revelateurs"] = (len(revelateurs), len(segments), float(revelateurs["n"].sum() / len(df) * 100))
    r["tailles"] = pd.Series({
        "segments de temps (S1 à S6)": df.groupby("segment", observed=True).size().min(),
        "segments âge × temps": df.groupby(["groupe_age", "segment"], observed=True).size().min(),
        "âge × temps (tranches fines)": df.groupby(["tranche_age", "segment"], observed=True).size().min(),
    }, name="plus petit groupe (utilisateurs)").to_frame()

    # --- 8. Limites : le lien caché entre stress et bonheur
    residu = lambda c: df[c] - df.groupby("tranche_10min")[c].transform("mean")  # noqa: E731
    r["corr_globale"] = float(df[STRESS].corr(df[BONHEUR]))
    r["corr_temps_egal"] = float(np.corrcoef(residu(STRESS), residu(BONHEUR))[0, 1])
    niveau_bonheur = pd.cut(df[BONHEUR], [0, 2, 4, 6, 8, 10], labels=["1–2", "3–4", "5–6", "7–8", "9–10"])
    r["lien_cache"] = agreger(df[df["segment"] == "S3 Modéré"].assign(niveau_bonheur=niveau_bonheur),
                              "niveau_bonheur", stress_moyen=(STRESS, "mean"))
    return r


if not FICHIER.exists():
    st.error(f"Fichier introuvable : `{FICHIER}`. Placez ce fichier à côté du dossier `data/`.")
    st.stop()

R = calculer()


def segment_vers_court(index):
    return [s.split(" ")[0] for s in index]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_introduction():
    st.title("Segmentation des utilisateurs d'Instagram : usage et bien-être")
    st.caption("Rush 4 · Bootcamp Data · livrable final · version interactive du notebook notebook_Instagram_final.ipynb")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Utilisateurs", fr(R["n"], 0))
    c2.metric("Stress expliqué", f"{fr(R['r2_stress'] * 100, 0)} %",
              help="Part des écarts de stress entre utilisateurs expliquée par le temps passé sur Instagram")
    c3.metric("Stress par heure", f"+{fr(R['pente'])}",
              help="Points de stress (sur 40) en plus pour chaque heure passée sur Instagram")
    c4.metric("Segments", f"{len(R['segments'])}", help="6 segments de temps passé × 4 groupes d'âge")

    st.header("Objectif")
    st.markdown("""
**Étudier les relations entre l'utilisation d'Instagram et le bien-être des utilisateurs**, à partir d'un jeu de données de 200 000 personnes.

Le département Innovation d'Instagram nous demande de **livrer une segmentation des utilisateurs** qui :
- **repose sur leur usage** de l'application ;
- **explique le lien entre l'usage et le bien-être** ;
- est **utilisable par les équipes produit** ;
- est **défendue devant un jury**.
""")
    st.header("Le contexte")
    st.markdown("""
Les réseaux sociaux doivent prouver qu'ils ne nuisent pas à leurs utilisateurs : les régulateurs posent des questions, la presse publie des études et les annonceurs ne veulent pas être associés à une plateforme qui rend les gens malheureux. Instagram veut **sa propre réponse, fondée sur ses propres données**.

- Les données de **bien-être et de santé** (stress, bonheur, sommeil…) viennent d'un **panel de volontaires** qui ont accepté une étude bien-être.
- Les données d'**usage** (temps passé, sessions, likes…) et de **profil** (âge, pays…) existent pour **tous** les utilisateurs.
- Nous travaillons sur une **réplique synthétique** du panel, fournie par l'équipe vie privée. Nos recommandations, elles, s'appliqueront à de vrais utilisateurs.
""")
    st.header("Définitions")
    st.markdown("""
- **Bien-être :** l'Organisation mondiale de la santé définit la santé comme « un état de complet bien-être physique, mental et social », qui ne se réduit pas à l'absence de maladie ([constitution de l'OMS](https://www.who.int/fr/about/governance/constitution)). La santé mentale y est décrite comme un état de bien-être qui permet notamment de surmonter les tensions normales de la vie ([Santé publique France, sante.fr](https://www.sante.fr/toutes-et-tous-une-sante-mentale)). Nous mesurons le bien-être avec **deux indicateurs** : le stress et le bonheur.
- **Bonheur :** une **auto-évaluation** de sa propre vie sur une échelle, comme l'échelle de Cantril (de 0 à 10) utilisée par le [World Happiness Report](https://www.worldhappiness.report/faq/). Dans nos données, le **bonheur déclaré** (`self_reported_happiness`) va de 1 à 10.
- **Stress :** le **stress perçu** (`perceived_stress_score`) va de 0 à 40. C'est la plage de l'échelle **PSS-10**, sans que la documentation le confirme. On considère le stress comme **élevé à partir de 27**, une convention de lecture courante et non un seuil de diagnostic ([guide de cotation, NovoPsych](https://novopsych.com.au/wp-content/uploads/2022/02/pss-10-report-PDF.pdf)).
- **Plus heureux / moins heureux :** les utilisateurs au bonheur de **9 ou 10** (20 % des utilisateurs) et de **1 ou 2** (20 % des utilisateurs).
""")
    st.header("Les règles suivies")
    st.markdown("""
- **Aucune donnée individuelle n'est affichée** : seulement des moyennes de groupes, et jamais un groupe de **moins de 100 utilisateurs**.
- **Résultats identiques à chaque exécution** : aucun tirage aléatoire.
- **« À temps égal »** : on compare des utilisateurs qui passent le même temps sur Instagram (par tranches de 10 minutes). C'est ce qui permet de savoir si une habitude compte **en plus** du temps passé.
- **Ce sont des corrélations**, pas des preuves de cause à effet.

Utilisez le menu à gauche pour parcourir les parties.
""")


def page_donnees():
    st.title("0 · Nettoyage et données")

    st.header("Contrôles de base")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Utilisateurs", fr(R["n"], 0))
    c2.metric("Colonnes", str(R["n_colonnes"]))
    c3.metric("Valeurs manquantes", str(R["manquants"]))
    c4.metric("Doublons", str(R["doublons"] + R["doublons_id"]))

    st.header("Incohérences métier : signalées, pas supprimées")
    c1, c2 = st.columns([1, 2])
    c1.metric("Lignes avec au moins une incohérence", f"{fr(R['part_signalees'], 0)} %")
    c2.metric("Stress expliqué par le temps passé, sans ces lignes",
              f"{fr(R['r2_sans_signalees'] * 100, 0)} %", help="Contre 71 % avec toutes les lignes : les résultats ne changent pas.")
    drapeaux = R["drapeaux"].reset_index()
    drapeaux["etiquette"] = drapeaux["part des lignes (%)"].map(lambda v: f"{fr(v)} %")
    graphique = alt.Chart(drapeaux).encode(
        y=alt.Y("règle:N", sort=None, title=None, axis=alt.Axis(labelLimit=460)),
        x=alt.X("part des lignes (%):Q", title="Part des lignes", scale=alt.Scale(domain=[0, 20]), axis=AXE_POURCENT))
    montrer((graphique.mark_bar(size=20, cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=BLEU).encode(
        tooltip=[alt.Tooltip("indicateur:N", title="Indicateur"), alt.Tooltip("etiquette:N", title="Part des lignes")])
             + graphique.mark_text(align="left", dx=6, fontSize=12, color=INK).encode(text="etiquette:N")).properties(
        title=titre("Quatre règles d'incohérence", "Chaque ligne concernée reçoit un indicateur flag_*, sans être supprimée"), height=200))
    st.markdown("""
- Ces incohérences touchent l'emploi, la situation de couple, les heures de travail et l'année de création du compte. **Aucune de ces colonnes ne sert à la segmentation.**
- Sans les lignes signalées, le temps passé explique toujours la même part du stress : **les résultats ne dépendent pas de ces lignes.**
""")

    st.header("Variables inutiles")
    tableau(R["inutiles"])

    st.header("Quel fichier croire, et sur quels champs ?")
    st.markdown("Instagram nous a envoyé **deux versions presque identiques** de la réplique (« usage » et « users »). L'une a subi un nettoyage non documenté. La consigne nous demande de décider laquelle croire, champ par champ.")
    comparaison = R["comparaison"]
    if comparaison is None:
        st.warning("Le fichier `instagram_users_lifestyleSafe.csv` est absent : la comparaison n'est pas recalculée.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Colonnes identiques", f"{comparaison['identiques']} sur {comparaison['total']}")
        c2.metric("Mineurs déclarés salariés à temps plein (fichier usage)", f"{fr(comparaison['mineurs'].iloc[0, 0], 0)} %")
        c3.metric("Colonnes utilisées identiques dans les deux fichiers", "oui" if comparaison["utilisees_identiques"] else "non")
        gauche, droite = st.columns(2)
        with gauche:
            st.markdown("**Colonnes qui diffèrent (nombre de lignes concernées)**")
            tableau(comparaison["differences"], 0)
        with droite:
            st.markdown(f"**Les 13–17 ans ({fr(comparaison['n_mineurs'], 0)} utilisateurs) dans les deux fichiers**")
            tableau(comparaison["mineurs"])
    st.markdown("""
**Notre décision**
- **Toutes les colonnes que nous utilisons** sont **identiques dans les deux fichiers** : nos résultats ne dépendent pas de ce choix. Nous travaillons sur le fichier `usage`.
- **Pour l'emploi et les heures de travail**, le fichier `users` a corrigé l'incohérence des mineurs. Nous n'utilisons pas ces colonnes.
""")

    st.header("Les variables construites")
    st.markdown("""
- **Six segments de temps passé** (S1 à S6), dont les seuils séparent les niveaux de stress et de bonheur : moins de 20 min, 20–88 min, 88–188 min, 188–240 min, 240–290 min, plus de 290 min.
- **Quatre groupes d'âge** (13–17, 18–34, 35–54, 55–65 ans) : les mineurs à part, pour des raisons légales.
- **Un indicateur « stress élevé »** (27 ou plus sur 40).
""")
    apport = R["apport"].reset_index().rename(columns={"index": "decoupage", "part du stress expliquée (%)": "part"})
    apport["etiquette"] = apport["part"].map(lambda v: f"{fr(v)} %")
    graphique = alt.Chart(apport).encode(
        y=alt.Y("decoupage:N", sort=None, title=None, axis=alt.Axis(labelLimit=420)),
        x=alt.X("part:Q", title="Part du stress expliquée", scale=alt.Scale(domain=[0, 80]), axis=AXE_POURCENT))
    montrer((graphique.mark_bar(size=22, cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=BLEU).encode(
        tooltip=[alt.Tooltip("decoupage:N", title="Découpage"), alt.Tooltip("etiquette:N", title="Part expliquée")])
             + graphique.mark_text(align="left", dx=6, fontSize=12, color=INK).encode(text="etiquette:N")).properties(
        title=titre("Six segments suffisent", "Part des écarts de stress expliquée par chaque découpage"), height=170))
    chiffres(R["niveaux"], titre="Voir la répartition des utilisateurs par niveau de stress")
    retenir("le fichier est complet et sans doublon ; les incohérences sont signalées sans changer les résultats ; six segments de temps conservent presque toute l'information du temps passé.")


def page_hypotheses():
    st.title("1 · Les hypothèses non concluantes")
    st.markdown("Plusieurs pistes, appuyées par des sources de santé publique, **ne se vérifient pas dans notre panel** : le sommeil, l'activité physique (pas et sport) et le pays. Un indicateur sans lien avec l'usage est aussi un résultat. La durée des sessions est traitée avec la fréquence de connexion (partie 3.4).")

    st.header("Le sommeil")
    st.markdown("**Questions :** Instagram fait-il baisser le nombre d'heures de sommeil ? Le manque de sommeil joue-t-il un rôle dans le bien-être ?")
    st.caption("Source : [info.gouv.fr, « Santé mentale : pourquoi le sommeil joue un rôle clé », 2025](https://www.info.gouv.fr/actualite/sante-mentale-pourquoi-le-sommeil-joue-un-role-cle) — « Avoir une bonne santé du sommeil contribue à avoir une bonne santé mentale. »")
    sommeil = R["sommeil"].reset_index()
    sommeil["court"] = segment_vers_court(sommeil["segment"])
    sommeil["etiquette"] = sommeil["sommeil_moyen"].map(lambda v: f"{fr(v)} h")
    sommeil["moins6"] = sommeil["part_moins_de_6h"].map(lambda v: f"{fr(v)} %")
    montrer(barres_simples(
        sommeil, "court", "sommeil_moyen", "etiquette",
        titre("Environ 7 h de sommeil dans tous les segments", "Sommeil moyen par segment de temps passé sur Instagram"),
        "Segment de temps passé (S1 : moins de 20 min · S6 : plus de 290 min)", "Sommeil moyen (heures par nuit)", COURTS, [0, 9],
        [alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("etiquette:N", title="Sommeil moyen"),
         alt.Tooltip("moins6:N", title="Dorment moins de 6 h")]))
    st.markdown("Le sommeil moyen est d'environ **7 h** et la part de petits dormeurs (moins de 6 h) d'environ **17 %**, dans tous les segments. Le sommeil n'est lié ni au temps passé, ni au stress, ni au bonheur (tableau plus bas).")

    st.header("L'activité physique : pas et sport")
    st.markdown("**Questions :** le temps passé sur Instagram fait-il baisser l'activité physique ? L'activité physique joue-t-elle un rôle sur le bien-être ?")
    st.caption("Source : [Ameli, « Sport et activité physique : un atout pour le bien-être »](https://www.ameli.fr/assure/sante/themes/activite-physique-sante/sport-et-activite-physique-un-atout-pour-le-bien-etre) — l'activité physique réduit le stress et l'anxiété, régule l'humeur et améliore le sommeil.")
    activite = R["activite"].reset_index()
    activite["court"] = segment_vers_court(activite["segment"])
    activite["etiquette_pas"] = activite["pas_par_jour"].map(lambda v: fr(v, 0))
    activite["etiquette_sport"] = activite["sport_heures_semaine"].map(lambda v: f"{fr(v)} h")
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_simples(activite, "court", "pas_par_jour", "etiquette_pas",
                               titre("Pas par jour", "Moyenne par segment"), "Segment de temps passé", "Pas par jour",
                               COURTS, [0, 9500], [alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("etiquette_pas:N", title="Pas par jour")]))
    with droite:
        montrer(barres_simples(activite, "court", "sport_heures_semaine", "etiquette_sport",
                               titre("Sport (heures par semaine)", "Moyenne par segment"), "Segment de temps passé",
                               "Heures de sport par semaine", COURTS, [0, 8.5],
                               [alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("etiquette_sport:N", title="Sport par semaine")]))
    st.markdown(f"Environ **8 000 pas par jour** et **7,2 h de sport par semaine** dans tous les segments. Le nombre de pas varie à peine (98 % des utilisateurs entre {fr(R['pas_bornes'][0], 0)} et {fr(R['pas_bornes'][1], 0)}) : cette variable ne permet pas de distinguer des profils.")
    st.markdown("**Liens avec le temps passé et le bien-être** (corrélations de −1 à 1, 0 = aucun lien)")
    tableau(R["correlations_vie"], 3)

    st.header("Le pays")
    pays = R["pays"].reset_index().rename(columns={"index": "pays"})
    pays["stress_txt"] = pays["stress"].map(fr)
    pays["bonheur_txt"] = pays["bonheur"].map(lambda v: fr(v, 2))
    pays["n_txt"] = pays["n"].map(lambda v: fr(v, 0))
    ordre_pays = list(pays["pays"])
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_simples(pays, "pays", "stress", "stress_txt", titre("Stress moyen par pays", "Échelle de 0 à 40"),
                               None, "Stress moyen (0–40)", ordre_pays, [0, 25],
                               [alt.Tooltip("pays:N", title="Pays"), alt.Tooltip("stress_txt:N", title="Stress moyen"),
                                alt.Tooltip("n_txt:N", title="Utilisateurs")], angle=-35))
    with droite:
        montrer(barres_simples(pays, "pays", "bonheur", "bonheur_txt", titre("Bonheur moyen par pays", "Échelle de 1 à 10"),
                               None, "Bonheur moyen (1–10)", ordre_pays, [0, 7],
                               [alt.Tooltip("pays:N", title="Pays"), alt.Tooltip("bonheur_txt:N", title="Bonheur moyen"),
                                alt.Tooltip("n_txt:N", title="Utilisateurs")], couleur=ORANGE, angle=-35))
    chiffres(R["pays"].rename_axis("pays"), 2)
    st.markdown("Dans les 10 pays, le stress moyen reste entre **19,9 et 20,3** et le bonheur entre **5,45 et 5,55**, avec le même temps passé (environ 3 h 10 par jour). À temps égal, les écarts sont inférieurs à 0,1 point.")
    retenir("le sommeil, l'activité physique et le pays **ne sont pas liés** à l'usage d'Instagram ni au bien-être dans notre panel. Nos sources laissaient attendre un effet du sommeil et du sport : c'est une limite de la réplique synthétique (partie 8).")


def page_temps():
    st.title("2 · Le temps passé sur Instagram : le cœur du lien")

    st.header("2.1 — Le temps passé est-il le facteur le plus lié au stress ?")
    segments = R["segments_temps"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Stress expliqué par le temps passé", f"{fr(R['r2_stress'] * 100, 0)} %")
    c2.metric("Stress en plus par heure", f"+{fr(R['pente'])} points")
    c3.metric("Stress élevé en S6 (plus de 290 min)", f"{fr(segments.loc['S6 Très intensif', 'part_stress_eleve'], 0)} %")

    data = R["stress_30min"].reset_index()
    data["heures"] = (data["tranche_30min"] + 15) / 60
    data["tranche"] = data["tranche_30min"].map(libelle_tranche)
    for colonne in ("stress", "q1", "q3"):
        data[f"{colonne}_txt"] = data[colonne].map(fr)
    data["n_txt"] = data["n"].map(lambda v: fr(v, 0))
    x = alt.X("heures:Q", title="Temps passé sur Instagram par jour", axis=AXE_HEURES, scale=alt.Scale(domain=[0, 8.5]))
    base = alt.Chart(data).encode(x=x)
    bande = base.mark_area(color=BLEU, opacity=0.12).encode(y=alt.Y("q1:Q", title="Stress perçu (0–40)", scale=alt.Scale(domain=[0, 40])), y2="q3:Q")
    ligne = base.mark_line(color=BLEU, strokeWidth=2).encode(y="stress:Q")
    points = base.mark_point(filled=True, size=70, color=BLEU, stroke=SURFACE, strokeWidth=1.5, opacity=1).encode(
        y="stress:Q", tooltip=[alt.Tooltip("tranche:N", title="Temps par jour"), alt.Tooltip("stress_txt:N", title="Stress moyen"),
                               alt.Tooltip("q1_txt:N", title="25 % des utilisateurs sous"), alt.Tooltip("q3_txt:N", title="25 % au-dessus de"),
                               alt.Tooltip("n_txt:N", title="Utilisateurs")])
    limites = pd.DataFrame({"x": [b / 60 for b in BORNES_SEGMENTS[1:-1]]})
    regles = alt.Chart(limites).mark_rule(color=AXIS, strokeWidth=1).encode(x="x:Q")
    noms = pd.DataFrame({"x": [10 / 60, 54 / 60, 138 / 60, 214 / 60, 265 / 60, 6.6], "y": [38.5] * 6, "texte": COURTS})
    etiquettes = alt.Chart(noms).mark_text(fontSize=11.5, color=MUTED, fontWeight=600).encode(x="x:Q", y="y:Q", text="texte:N")
    montrer((bande + regles + ligne + points + etiquettes).properties(
        title=titre("Le stress monte régulièrement avec le temps passé sur Instagram",
                    "Stress moyen par tranche de 30 minutes · zone bleue : la moitié centrale des utilisateurs · lignes : limites des segments S1 à S6"),
        height=380))

    seg = segments.reset_index()
    seg["court"] = segment_vers_court(seg["segment"])
    seg["duree"] = DUREES_SEGMENTS
    seg["stress_txt"] = seg["stress"].map(fr)
    seg["bonheur_txt"] = seg["bonheur"].map(fr)
    seg["eleve_txt"] = seg["part_stress_eleve"].map(lambda v: f"{fr(v, 0)} %")
    infobulle = [alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("duree:N", title="Temps par jour"),
                 alt.Tooltip("stress_txt:N", title="Stress moyen"), alt.Tooltip("bonheur_txt:N", title="Bonheur moyen"),
                 alt.Tooltip("eleve_txt:N", title="En stress élevé")]
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_simples(seg, "court", "stress", "stress_txt", titre("Stress moyen par segment", "Échelle de 0 à 40"),
                               "Segment de temps passé", "Stress moyen (0–40)", COURTS, [0, 40], infobulle))
    with droite:
        montrer(barres_simples(seg, "court", "bonheur", "bonheur_txt", titre("Bonheur moyen par segment", "Échelle de 1 à 10"),
                               "Segment de temps passé", "Bonheur moyen (1–10)", COURTS, [0, 9], infobulle, couleur=ORANGE))
    affichage = segments.copy()
    affichage.insert(0, "temps par jour", DUREES_SEGMENTS)
    st.markdown("**Les six segments de temps passé**")
    tableau(affichage.rename(columns={"n": "utilisateurs", "minutes": "temps moyen (min)", "stress": "stress (0–40)",
                                      "bonheur": "bonheur (1–10)", "part_stress_eleve": "stress élevé (%)"}).rename_axis("segment"))
    st.markdown("""
- Le stress **monte régulièrement** : environ **+5,4 points par heure**, de 4,3 en S1 à 33,5 en S6. Le temps passé explique à lui seul **71 %** des écarts de stress.
- Le bonheur, lui, **chute surtout aux deux extrêmes** : de 8,0 en S1 à 6,6 en S2, puis il reste entre 5,7 et 5,2 de S3 à S5, avant de tomber à 3,9 en S6.
- Les **seuils de 20 min et d'environ 4 h 50** (290 min) marquent ces deux chutes : c'est ce que la segmentation apporte de plus qu'un simple classement par temps passé.
""")
    conclusion_produit("le temps quotidien passé sur l'application est **l'indicateur numéro un** à suivre pour repérer les groupes d'utilisateurs les plus stressés. Instagram le mesure déjà pour tous ses utilisateurs, sans rien leur demander.")
    st.caption("Sources : [Riehm et al., 2019 (Johns Hopkins)](https://hub.jhu.edu/2019/09/11/social-media-teen-mental-health/) — au-delà de 3 h par jour, le risque d'anxiété et de dépression des adolescents augmente · [Liu et al., 2022, méta-analyse](https://pmc.ncbi.nlm.nih.gov/articles/PMC9103874/) — chaque heure de plus par jour va avec environ 13 % de risque de dépression en plus.")
    retenir("oui, **le temps passé est le facteur d'usage le plus lié au stress**, de façon régulière, et il est aussi lié au bonheur, surtout aux deux extrêmes.")

    st.header("2.2 — Le temps passé chaque jour est-il aussi lié au bonheur ?")
    profils = R["profils_temps"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Temps médian des plus heureux", f"{fr(profils.loc['temps médian par jour (min)', 'Plus heureux (9–10)'], 0)} min")
    c2.metric("Temps médian des moins heureux", f"{fr(profils.loc['temps médian par jour (min)', 'Moins heureux (1–2)'], 0)} min")
    c3.metric("Sessions par jour : plus heureux / autres",
              f"{fr(profils.loc['sessions par jour', 'Plus heureux (9–10)'])} / {fr(profils.loc['sessions par jour', 'Autres'])}")
    parts = R["bonheur_segments"].reset_index().melt(id_vars=["segment", "n"], value_vars=["part_tres_heureux", "part_tres_malheureux"],
                                                     var_name="groupe", value_name="part")
    parts["court"] = segment_vers_court(parts["segment"])
    parts["groupe"] = parts["groupe"].map({"part_tres_heureux": "Très heureux (bonheur 9–10)", "part_tres_malheureux": "Très malheureux (bonheur 1–2)"})
    parts["etiquette"] = parts["part"].map(lambda v: f"{fr(v)} %")
    couleurs = alt.Scale(domain=["Très heureux (bonheur 9–10)", "Très malheureux (bonheur 1–2)"], range=[BLEU, ORANGE])
    base = alt.Chart(parts).encode(
        x=alt.X("court:N", sort=COURTS, title="Segment de temps passé", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("part:Q", title="Part des utilisateurs", scale=alt.Scale(domain=[0, 55]), axis=AXE_POURCENT),
        color=alt.Color("groupe:N", scale=couleurs, title=None))
    lignes = base.mark_line(strokeWidth=2) + base.mark_point(filled=True, size=80, stroke=SURFACE, strokeWidth=1.5, opacity=1).encode(
        tooltip=[alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("groupe:N", title="Groupe"), alt.Tooltip("etiquette:N", title="Part")])
    extremites = base.mark_text(dy=-12, fontSize=12, color=INK2).encode(text="etiquette:N", color=alt.value(INK2)).transform_filter(
        alt.FieldOneOfPredicate(field="court", oneOf=["S1", "S6"]))
    medianes = pd.DataFrame({"groupe": ["Plus heureux (9–10)", "Moins heureux (1–2)"],
                             "minutes": [profils.loc["temps médian par jour (min)", "Plus heureux (9–10)"],
                                         profils.loc["temps médian par jour (min)", "Moins heureux (1–2)"]]})
    medianes["etiquette"] = medianes["minutes"].map(lambda v: f"{fr(v, 0)} min")
    gauche, droite = st.columns([2.2, 1])
    with gauche:
        montrer((lignes + extremites).properties(title=titre("La part de très heureux s'effondre avec le temps passé",
                                                             "Part des utilisateurs très heureux et très malheureux par segment · survolez les points"), height=360))
    with droite:
        base_m = alt.Chart(medianes).encode(
            x=alt.X("groupe:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelLimit=200)),
            y=alt.Y("minutes:Q", title="Temps médian par jour (min)", scale=alt.Scale(domain=[0, 290])))
        montrer((base_m.mark_bar(size=48, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            color=alt.Color("groupe:N", scale=alt.Scale(domain=list(medianes["groupe"]), range=[BLEU, ORANGE]), legend=None),
            tooltip=[alt.Tooltip("groupe:N", title="Groupe"), alt.Tooltip("etiquette:N", title="Temps médian")])
                 + base_m.mark_text(dy=-9, fontSize=12.5, color=INK).encode(text="etiquette:N")).properties(
            title=titre("Deux fois moins de temps", "Temps médian passé chaque jour"), height=360))
    chiffres(R["bonheur_segments"].rename_axis("segment"))
    st.markdown("""
- En S1 (moins de 20 min par jour), près de **la moitié** des utilisateurs sont très heureux ; en S6 (plus de 290 min), ils ne sont plus que **6 %**, et plus d'un tiers sont très malheureux.
- Les plus heureux passent **deux fois moins de temps** sur l'application que les moins heureux, et ouvrent l'application moins souvent.
""")
    st.markdown("**Note : le temps passé et l'activité disent la même chose.** Les compteurs d'activité (likes, stories, commentaires, messages, publicités, sessions) sont presque des copies du temps passé : plus on reste, plus on agit. Ils n'apportent donc pas d'information en plus (partie 3).")
    copies = R["copies"].reset_index().rename(columns={"index": "variable", "corrélation avec le temps passé": "correlation"})
    copies["etiquette"] = copies["correlation"].map(lambda v: fr(v, 2))
    base = alt.Chart(copies).encode(
        y=alt.Y("variable:N", sort="-x", title=None),
        x=alt.X("correlation:Q", title="Corrélation avec le temps passé par jour (0 à 1)", scale=alt.Scale(domain=[0, 1.05]),
                axis=alt.Axis(labelExpr="replace(format(datum.value, '.1f'), '.', ',')")))
    montrer((base.mark_bar(size=18, cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=BLEU).encode(
        tooltip=[alt.Tooltip("variable:N", title="Variable"), alt.Tooltip("etiquette:N", title="Corrélation")])
             + base.mark_text(align="left", dx=6, fontSize=12, color=INK).encode(text="etiquette:N")).properties(
        title=titre("Les compteurs d'activité suivent le temps passé", "Corrélation de chaque compteur avec le temps passé par jour"), height=250))
    retenir("le temps passé est aussi lié au bonheur : **les plus heureux sont ceux qui utilisent le moins Instagram**, en temps comme en nombre de sessions.")


def page_age():
    st.title("3 · Le rôle de l'âge")

    st.header("D'après l'âge, à usage égal, qui est le plus stressé ?")
    st.markdown("Pour comparer des utilisateurs à **usage égal**, on regarde le segment **S4 Soutenu** (188 à 240 min par jour, environ 3 h 30 en moyenne dans chaque tranche d'âge).")
    age = R["age_s4"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Stress des 13–17 ans en S4", fr(age.loc["13–17 ans", "stress"]))
    c2.metric("Stress des 55–65 ans en S4", fr(age.loc["55–65 ans", "stress"]))
    c3.metric("Stress en plus par tranche de 10 ans", f"+{fr(R['pente_age'])} point")
    donnees = age.reset_index()
    donnees["etiquette"] = donnees["stress"].map(fr)
    donnees["minutes_txt"] = donnees["minutes"].map(lambda v: f"{fr(v, 0)} min")
    montrer(barres_simples(donnees, "tranche_age", "stress", "etiquette",
                           titre("À usage égal, le stress augmente avec l'âge", "Stress moyen des utilisateurs du segment S4 (188 à 240 min par jour)"),
                           None, "Stress moyen (0–40)", TRANCHES_AGE, [0, 30],
                           [alt.Tooltip("tranche_age:N", title="Âge"), alt.Tooltip("etiquette:N", title="Stress moyen"),
                            alt.Tooltip("minutes_txt:N", title="Temps moyen par jour")]))
    grille = R["grille_age"].reset_index()
    grille["court"] = segment_vers_court(grille["segment"])
    grille["etiquette"] = grille["stress"].map(fr)
    grille["n_txt"] = grille["n"].map(lambda v: fr(v, 0))
    montrer(carte_chaleur(grille, "court", "tranche_age", "stress", "etiquette", COURTS, TRANCHES_AGE, [0, 40], "Stress moyen", 22,
                          [alt.Tooltip("tranche_age:N", title="Âge"), alt.Tooltip("segment:N", title="Segment"),
                           alt.Tooltip("etiquette:N", title="Stress moyen"), alt.Tooltip("n_txt:N", title="Utilisateurs")],
                          titre("Le même écart d'âge dans tous les segments", "Stress moyen par âge et par segment · lire chaque colonne de haut en bas"),
                          "Segment de temps passé"))
    st.markdown("""
- En S4, le stress passe de **18,9** chez les 13–17 ans à **26,6** chez les 55–65 ans.
- À temps égal, le stress augmente de **+1,2 point par tranche de 10 ans**, et le même écart se retrouve dans tous les segments.
""")
    retenir("**à usage égal, ce sont les plus âgés qui sont les plus stressés.** L'âge apporte une information en plus du temps passé.")

    st.header("Les plus jeunes passent-ils plus de temps sur Instagram ?")
    exposition = R["exposition"].reset_index()
    exposition["etiquette"] = exposition["part_3h_ou_plus"].map(lambda v: f"{fr(v)} %")
    exposition["minutes_txt"] = exposition["minutes"].map(lambda v: f"{fr(v, 0)} min")
    c1, c2 = st.columns(2)
    c1.metric("13–17 ans à 3 h ou plus par jour", exposition.loc[0, "etiquette"])
    c2.metric("55–65 ans à 3 h ou plus par jour", exposition.loc[len(exposition) - 1, "etiquette"])
    montrer(barres_simples(exposition, "tranche_age", "part_3h_ou_plus", "etiquette",
                           titre("Plus on est jeune, plus on passe de temps sur Instagram", "Part des utilisateurs qui y passent 3 h ou plus par jour"),
                           None, "Utilisateurs à 3 h ou plus par jour", TRANCHES_AGE, [0, 75],
                           [alt.Tooltip("tranche_age:N", title="Âge"), alt.Tooltip("etiquette:N", title="À 3 h ou plus"),
                            alt.Tooltip("minutes_txt:N", title="Temps moyen par jour")], axe_y=AXE_POURCENT))
    st.markdown("**63 %** des 13–17 ans passent 3 h ou plus par jour sur Instagram, contre **43 %** des 55–65 ans. Le temps moyen baisse de 223 à 159 minutes par jour.")
    conclusion_produit("les plus jeunes sont **les plus exposés** en temps passé. Ce sont eux que les outils de limitation de temps touchent le plus souvent, et ils incluent des **mineurs**, qui demandent des précautions particulières.")
    st.caption("Source : [question écrite à l'Assemblée nationale citant le rapport « Enfants et écrans » (2024)](https://www.assemblee-nationale.fr/dyn/16/questions/QANR5L16QE18298.pdf) — chez les 16–19 ans, le temps d'écran dépasse les cinq heures ; les experts évoquent la nocivité des réseaux sociaux, « facteur de risque » de dépression ou d'anxiété en cas de « vulnérabilité préexistante ».")
    retenir("deux effets opposés : les jeunes sont **plus exposés en temps**, les plus âgés sont **plus stressés à temps égal**.")


def page_habitudes():
    st.title("4 · Les habitudes d'utilisation")
    st.markdown("Ces parties comparent des **façons d'utiliser Instagram**. Chaque fois, on vérifie si l'écart tient encore **à temps passé égal**, c'est-à-dire en comparant des utilisateurs qui passent le même temps sur l'application.")

    st.header("4.1 — Les moins heureux ont un usage plus intensif")
    usage = R["usage_bonheur"]
    moins, plus = R["n_moins_plus"]
    st.markdown(f"Comparaison des **moins heureux** (bonheur de 1 ou 2, {fr(moins, 0)} utilisateurs) et des **plus heureux** (bonheur de 9 ou 10, {fr(plus, 0)} utilisateurs).")
    donnees = usage.reset_index().melt(id_vars="comportement", value_vars=["différence (%)", "différence à temps égal (%)"],
                                       var_name="serie", value_name="ecart").dropna()
    donnees["serie"] = donnees["serie"].map({"différence (%)": "Différence brute", "différence à temps égal (%)": "Différence à temps passé égal"})
    donnees["etiquette"] = donnees["ecart"].map(lambda v: pourcent(v, 0, signe=True))
    ordre = list(usage.index)
    base = alt.Chart(donnees).encode(
        y=alt.Y("comportement:N", sort=ordre, title=None, axis=alt.Axis(labelLimit=320)),
        yOffset=alt.YOffset("serie:N", sort=["Différence brute", "Différence à temps passé égal"]),
        x=alt.X("ecart:Q", title="Écart des moins heureux par rapport aux plus heureux", scale=alt.Scale(domain=[-70, 105]), axis=AXE_POURCENT))
    barres = base.mark_bar(size=11).encode(
        color=alt.Color("serie:N", scale=alt.Scale(domain=["Différence brute", "Différence à temps passé égal"], range=[BLEU, ORANGE]), title=None),
        tooltip=[alt.Tooltip("comportement:N", title="Comportement"), alt.Tooltip("serie:N", title="Mesure"), alt.Tooltip("etiquette:N", title="Écart")])
    textes = base.mark_text(fontSize=10.5, color=INK2, dx=6, align="left").encode(text="etiquette:N").transform_filter("datum.ecart >= 0")
    textes_neg = base.mark_text(fontSize=10.5, color=INK2, dx=-6, align="right").encode(text="etiquette:N").transform_filter("datum.ecart < 0")
    regle = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=AXIS).encode(x="x:Q")
    montrer((regle + barres + textes + textes_neg).properties(
        title=titre("Plus d'actions chez les moins heureux… parce qu'ils restent plus longtemps",
                    "Écart en % entre moins heureux et plus heureux · en orange : à temps passé égal"), height=520))
    chiffres(usage)
    st.markdown("""
- Les moins heureux **utilisent davantage toutes les fonctionnalités** : sessions, Reels, stories, likes, commentaires, messages. Le vrai constat est un **usage beaucoup plus intensif**, d'abord en temps (+86 %).
- Les plus heureux font moins d'actions mais ont un **score d'engagement deux fois plus élevé**. Ce score mesure surtout les interactions **par minute**, élevées chez ceux qui restent peu de temps.
- **À temps passé égal, les écarts deviennent presque nuls** (moins de 5 %), y compris celui du score d'engagement (barres orange).
""")
    lien_temps, lien_minute = R["engagement_liens"]
    st.caption(f"Le score d'engagement est corrélé à {fr(lien_temps, 2)} avec le temps passé et à {fr(lien_minute, 2)} avec le nombre de likes et commentaires par minute.")
    retenir("les moins heureux ont un usage **plus intensif**, mais à temps égal ils agissent exactement comme les plus heureux. Ce n'est pas la qualité des interactions qui les distingue, c'est **le temps passé**.")

    st.header("4.2 — Consommateurs ou créateurs de contenu ?")
    createurs = R["createurs"]
    donnees = createurs.reset_index()
    donnees["profil_court"] = donnees["profil_publication"].astype(str).str.split(" ").str[0]
    long_b = donnees.melt(id_vars=["profil_publication", "profil_court"], value_vars=["bonheur", "bonheur_egal"], var_name="serie", value_name="valeur")
    long_s = donnees.melt(id_vars=["profil_publication", "profil_court"], value_vars=["stress", "stress_egal"], var_name="serie", value_name="valeur")
    for longue in (long_b, long_s):
        longue["serie"] = longue["serie"].map({"bonheur": "Moyenne brute", "stress": "Moyenne brute",
                                               "bonheur_egal": "À temps passé et âge égaux", "stress_egal": "À temps passé et âge égaux"})
        longue["etiquette"] = longue["valeur"].map(fr)
    series = ["Moyenne brute", "À temps passé et âge égaux"]
    infobulle = [alt.Tooltip("profil_publication:N", title="Profil"), alt.Tooltip("serie:N", title="Mesure"), alt.Tooltip("etiquette:N", title="Valeur")]
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_groupees(long_b, "profil_court", "serie", "valeur", "etiquette", ["Consommateur", "Intermédiaire", "Créateur"], series, [BLEU, ORANGE],
                                titre("Bonheur selon le profil", "Échelle de 1 à 10"), None, "Bonheur moyen (1–10)", [0, 7], infobulle))
    with droite:
        montrer(barres_groupees(long_s, "profil_court", "serie", "valeur", "etiquette", ["Consommateur", "Intermédiaire", "Créateur"], series, [BLEU, ORANGE],
                                titre("Stress selon le profil", "Échelle de 0 à 40"), None, "Stress moyen (0–40)", [0, 30], infobulle))
    affichage = createurs[["part", "age", "minutes", "bonheur", "tres_heureux", "tres_malheureux", "stress"]].rename(columns={
        "part": "part des utilisateurs (%)", "age": "âge moyen", "minutes": "temps par jour (min)", "bonheur": "bonheur",
        "tres_heureux": "très heureux (%)", "tres_malheureux": "très malheureux (%)", "stress": "stress"}).rename_axis("profil")
    tableau(affichage)
    st.markdown("""
- Au premier regard, les **consommateurs** semblent plus heureux (6,0 contre 5,0) et moins stressés que les **créateurs**.
- Mais les créateurs passent **deux fois plus de temps** sur Instagram (257 min contre 117) et sont **beaucoup plus jeunes** (30 ans contre 45) : les moins de 25 ans publient environ 10 fois par semaine, contre 4 à 5 fois au-delà.
- **À temps passé et âge égaux, il ne reste aucune différence** de bonheur ni de stress (barres orange).
""")
    st.caption("Source : [Valkenburg, van Driel & Beyens, 2022, New Media & Society](https://journals.sagepub.com/doi/10.1177/14614448211065425) — sur 40 études, la plupart ne confirment pas d'effet différent de l'usage actif (publier) et passif (regarder) sur le bien-être.")
    retenir("publier ou seulement regarder ne change rien au bien-être : les créateurs semblent moins heureux parce qu'ils sont **plus jeunes et passent plus de temps** sur l'application.")

    st.header("4.3 — Activité privée ou activité publique ?")
    st.markdown("""
- **Activité privée :** les messages privés envoyés. **Activité publique :** les likes et les commentaires. Le fichier ne contient pas de colonne « story privée » ni « partages ».
- La **part d'activité privée** est la part des messages dans l'ensemble des interactions (messages, likes et commentaires), en 5 groupes de taille égale, du plus public (Q1) au plus privé (Q5).
- Le **réglage du compte** (public, amis seulement, privé) est comparé de la même façon.
""")
    series = ["Moyenne brute", "À temps passé égal", "Utilisateurs à environ 90 min par jour"]
    couleurs = [BLEU, ORANGE, AQUA]

    def longue(table, variable, cle_groupe):
        donnees = table.reset_index().rename(columns={"index": cle_groupe})
        if cle_groupe not in donnees.columns:
            donnees = donnees.rename(columns={donnees.columns[0]: cle_groupe})
        resultat = donnees.melt(id_vars=cle_groupe, value_vars=[variable, f"{variable}_temps_egal", f"{variable}_vers_90"],
                                var_name="serie", value_name="valeur")
        resultat["serie"] = resultat["serie"].map({variable: series[0], f"{variable}_temps_egal": series[1], f"{variable}_vers_90": series[2]})
        resultat["etiquette"] = resultat["valeur"].map(fr)
        return resultat

    quintiles = R["prive"]["quintile_prive"]
    comptes = R["prive"]["privacy_setting_level"]
    infobulle_q = [alt.Tooltip("groupe:N", title="Groupe"), alt.Tooltip("serie:N", title="Mesure"), alt.Tooltip("etiquette:N", title="Valeur")]
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_groupees(longue(quintiles, "stress", "groupe"), "groupe", "serie", "valeur", "etiquette", QUINTILES, series, couleurs,
                                titre("Stress selon la part d'activité privée", "Échelle de 0 à 40"), None, "Stress moyen (0–40)", [0, 30], infobulle_q, angle=-20))
    with droite:
        montrer(barres_groupees(longue(quintiles, "bonheur", "groupe"), "groupe", "serie", "valeur", "etiquette", QUINTILES, series, couleurs,
                                titre("Bonheur selon la part d'activité privée", "Échelle de 1 à 10"), None, "Bonheur moyen (1–10)", [0, 8], infobulle_q, angle=-20))
    gauche, droite = st.columns(2)
    with gauche:
        montrer(barres_groupees(longue(comptes, "stress", "groupe"), "groupe", "serie", "valeur", "etiquette", list(COMPTES.values()), series, couleurs,
                                titre("Stress selon le réglage du compte", "Échelle de 0 à 40"), None, "Stress moyen (0–40)", [0, 30], infobulle_q))
    with droite:
        montrer(barres_groupees(longue(comptes, "bonheur", "groupe"), "groupe", "serie", "valeur", "etiquette", list(COMPTES.values()), series, couleurs,
                                titre("Bonheur selon le réglage du compte", "Échelle de 1 à 10"), None, "Bonheur moyen (1–10)", [0, 8], infobulle_q))
    affichage = quintiles[["minutes", "stress", "bonheur", "stress_temps_egal", "bonheur_temps_egal"]].rename(columns={
        "minutes": "temps par jour (min)", "stress_temps_egal": "stress à temps égal", "bonheur_temps_egal": "bonheur à temps égal"}).rename_axis("groupe")
    tableau(affichage)
    st.markdown(f"""
- En moyenne brute, les utilisateurs à l'activité **la plus privée** (Q5) semblent deux fois moins stressés et plus heureux. Mais ils passent **2,5 fois moins de temps** sur Instagram (87 min contre 226) : ils envoient surtout des messages, et likent ou commentent peu.
- **À temps passé égal, les cinq groupes sont identiques** (stress de 20,0, bonheur de 5,5). Chez les {fr(R['n_vers_90'], 0)} utilisateurs qui passent environ 90 min par jour, le stress est de 10 et le bonheur de 6,0 dans tous les groupes.
- Le **réglage du compte** ne change rien : comptes publics, « amis seulement » et privés ont le même stress, le même bonheur et le même temps passé.
""")
    retenir("le caractère privé ou public de l'activité **n'est pas lié au bien-être**. L'écart apparent vient du temps passé.")

    st.header("4.4 — Utilisateurs « réflexe » ou « immersion » ?")
    mediane_sessions, mediane_duree = R["medianes_connexion"]
    st.markdown(f"""
- **Profil réflexe :** beaucoup de connexions courtes, soit plus de {fr(mediane_sessions, 0)} sessions par jour (la médiane) **et** des sessions de moins de {fr(mediane_duree)} min (la médiane).
- **Profil immersion :** peu de connexions mais longues, soit moins de {fr(mediane_sessions, 0)} sessions par jour **et** des sessions de plus de {fr(mediane_duree)} min.
""")
    connexion = R["connexion"]
    meme = R["connexion_meme_temps"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Stress des « réflexe »", f"{fr(connexion.loc['Réflexe', 'stress'])} / 40")
    c2.metric("Stress des « immersion »", f"{fr(connexion.loc['Immersion', 'stress'])} / 40")
    c3.metric("Écart de stress", pourcent((connexion.loc["Réflexe", "stress"] / connexion.loc["Immersion", "stress"] - 1) * 100, 0, signe=True))
    donnees = pd.DataFrame({
        "profil": ["Réflexe", "Immersion", "Réflexe", "Immersion"],
        "serie": ["Tous les utilisateurs du profil"] * 2 + ["Même temps total (2 à 3 h par jour)"] * 2,
        "stress": [connexion.loc["Réflexe", "stress"], connexion.loc["Immersion", "stress"], meme.loc["Réflexe", "stress"], meme.loc["Immersion", "stress"]],
        "minutes": [connexion.loc["Réflexe", "minutes"], connexion.loc["Immersion", "minutes"], meme.loc["Réflexe", "minutes"], meme.loc["Immersion", "minutes"]],
    })
    donnees["etiquette"] = donnees["stress"].map(fr)
    donnees["minutes_txt"] = donnees["minutes"].map(lambda v: f"{fr(v, 0)} min")
    gauche, droite = st.columns([1.3, 1])
    with gauche:
        montrer(barres_groupees(donnees, "profil", "serie", "stress", "etiquette", ["Réflexe", "Immersion"],
                            ["Tous les utilisateurs du profil", "Même temps total (2 à 3 h par jour)"], [BLEU, ORANGE],
                                titre("Les « réflexe » sont plus stressés… parce qu'ils passent plus de temps au total",
                                      "Stress moyen · en orange : utilisateurs qui passent le même temps total sur Instagram"),
                                None, "Stress moyen (0–40)", [0, 30],
                                [alt.Tooltip("profil:N", title="Profil"), alt.Tooltip("serie:N", title="Groupe"),
                                 alt.Tooltip("etiquette:N", title="Stress moyen"), alt.Tooltip("minutes_txt:N", title="Temps moyen par jour")]))
    with droite:
        st.markdown(f"""
- Les utilisateurs « réflexe » sont **nettement plus stressés** que les « immersion » ({fr(connexion.loc['Réflexe', 'stress'])} contre {fr(connexion.loc['Immersion', 'stress'])}).
- Mais ils passent aussi **beaucoup plus de temps au total** sur Instagram ({fr(connexion.loc['Réflexe', 'minutes'], 0)} min contre {fr(connexion.loc['Immersion', 'minutes'], 0)} par jour), car le temps total est égal aux sessions multipliées par leur durée.
- **À temps total égal (2 à 3 h par jour), l'écart disparaît** : {fr(meme.loc['Réflexe', 'stress'])} contre {fr(meme.loc['Immersion', 'stress'])}. La durée des sessions n'a donc pas de lien propre avec le stress.
""")
    affichage = connexion.rename(columns={"n": "utilisateurs", "sessions": "sessions par jour", "duree": "durée d'une session (min)",
                                          "minutes": "temps total (min par jour)", "stress": "stress (0–40)", "bonheur": "bonheur (1–10)"}).rename_axis("profil")
    tableau(affichage)
    conclusion_produit("ouvrir Instagram très souvent va avec plus de stress **parce que cela fait plus de temps au total**. Un rappel doit compter **le temps cumulé de la journée**, pas seulement la durée d'une session.")
    retenir("ce n'est pas la façon de se connecter qui compte, c'est **le temps total** passé chaque jour.")


def page_stress_bonheur():
    st.title("5 · Stress et bonheur")
    st.header("Le stress lié à l'usage s'accompagne-t-il d'une baisse de bonheur ?")
    c1, c2 = st.columns(2)
    c1.metric("Stress expliqué par le temps passé", f"{fr(R['r2_stress'] * 100, 0)} %")
    c2.metric("Bonheur expliqué par le temps passé", f"{fr(R['r2_bonheur'] * 100, 0)} %")
    data = R["stress_30min"].reset_index()
    data["heures"] = (data["tranche_30min"] + 15) / 60
    data["tranche"] = data["tranche_30min"].map(libelle_tranche)
    data["stress_txt"] = data["stress"].map(fr)
    data["bonheur_txt"] = data["bonheur"].map(lambda v: fr(v, 2))
    x = alt.X("heures:Q", title="Temps passé sur Instagram par jour", axis=AXE_HEURES, scale=alt.Scale(domain=[0, 8.5]))
    base = alt.Chart(data).encode(x=x)
    stress = (base.mark_line(color=BLEU, strokeWidth=2).encode(y=alt.Y("stress:Q", title="Stress perçu (0–40)", scale=alt.Scale(domain=[0, 40])))
              + base.mark_point(filled=True, size=45, color=BLEU, stroke=SURFACE, strokeWidth=1.2, opacity=1).encode(
                  y="stress:Q", tooltip=[alt.Tooltip("tranche:N", title="Temps par jour"), alt.Tooltip("stress_txt:N", title="Stress moyen")]))
    zones = alt.Chart(pd.DataFrame({"debut": [0, 290 / 60], "fin": [20 / 60, 8.5]})).mark_rect(color=ORANGE, opacity=0.08).encode(x="debut:Q", x2="fin:Q")
    notes = alt.Chart(pd.DataFrame({"x": [0.85, 6.8], "y": [9.3, 6.5], "texte": ["chute après 20 min", "chute après 290 min"]})).mark_text(
        fontSize=11.5, color=INK2).encode(x="x:Q", y="y:Q", text="texte:N")
    bonheur = (zones + base.mark_line(color=ORANGE, strokeWidth=2).encode(y=alt.Y("bonheur:Q", title="Bonheur déclaré (1–10)", scale=alt.Scale(domain=[1, 10])))
               + base.mark_point(filled=True, size=45, color=ORANGE, stroke=SURFACE, strokeWidth=1.2, opacity=1).encode(
                   y="bonheur:Q", tooltip=[alt.Tooltip("tranche:N", title="Temps par jour"), alt.Tooltip("bonheur_txt:N", title="Bonheur moyen")]) + notes)
    gauche, droite = st.columns(2)
    with gauche:
        montrer(stress.properties(title=titre("Le stress monte régulièrement", f"{fr(R['r2_stress'] * 100, 0)} % des écarts expliqués par le temps passé"), height=340))
    with droite:
        montrer(bonheur.properties(title=titre("Le bonheur chute aux deux extrêmes", f"{fr(R['r2_bonheur'] * 100, 0)} % des écarts expliqués par le temps passé"), height=340))
    st.markdown("""
- Le **stress** monte **régulièrement** avec le temps passé.
- Le **bonheur** baisse surtout **aux deux extrêmes** (zones orangées) : très vite après les premières minutes, puis au-delà d'environ 4 h 50 par jour. Entre les deux, il change peu.
- Le temps passé explique **71 %** des écarts de stress, mais seulement **16 %** des écarts de bonheur.
""")
    conclusion_produit("il faut **suivre le stress et le bonheur séparément** : un utilisateur peut être très stressé et très heureux à la fois. Le lien principal d'Instagram est avec **le stress**.")
    st.caption("Source : [le modèle « dual continua » de Keyes (Frontiers in Psychology, 2022)](https://www.frontiersin.org/articles/10.3389/fpsyg.2022.885278/full) — la santé mentale positive et la détresse sont deux dimensions distinctes.")
    retenir("le stress lié à l'usage s'accompagne d'une baisse de bonheur, mais **beaucoup plus faible et concentrée aux extrêmes**. Stress et bonheur sont deux indicateurs différents.")


def page_segmentation():
    st.title("6 · La segmentation")
    st.markdown("**Deux informations suffisent** : le **segment de temps passé** (S1 à S6) et le **groupe d'âge**. Toutes deux sont connues pour **tous** les utilisateurs, et aucune n'est une donnée de santé.")

    st.header("Pourquoi cette méthode ?")
    st.markdown("""
La consigne propose deux voies : **prédire un indicateur de bien-être** à partir de l'usage, ou **regrouper automatiquement** les utilisateurs (*clustering*). Nous avons choisi la première, sous une forme simple : des **segments par paliers** de temps passé, croisés avec l'âge.
- **Un regroupement automatique retrouverait surtout le temps passé** : les compteurs d'activité en sont presque des copies (partie 2.2), et les habitudes d'utilisation n'ajoutent rien à temps égal (partie 4).
- **Ses groupes sont difficiles à expliquer** et peuvent changer d'une exécution à l'autre.
- **Nos segments sont construits pour séparer le stress et le bonheur**, lisibles (« S4 Soutenu, 55–65 ans »), applicables à tous et sans donnée de santé.
""")

    st.header("La carte des segments et le simulateur")
    st.markdown("Entrez l'âge et le temps quotidien d'un **utilisateur fictif** : l'application lui attribue son segment et l'encadre sur la carte.")
    col_age, col_minutes = st.columns(2)
    age = col_age.slider("Âge", min_value=13, max_value=65, value=16)
    minutes = col_minutes.slider("Temps passé sur Instagram par jour (minutes)", min_value=0, max_value=540, value=250, step=5)
    groupe = pd.cut([age], BORNES_GROUPES_AGE, right=False, labels=GROUPES_AGE)[0]
    segment = pd.cut([minutes], BORNES_SEGMENTS, right=False, labels=SEGMENTS)[0]
    ligne = R["segments"].loc[(groupe, segment)]
    c1, c2, c3 = st.columns(3)
    c1.metric("Segment", f"{segment.split(' ')[0]} · {groupe}", help=segment)
    c2.metric("Part en stress élevé dans ce segment", f"{fr(ligne['part_stress_eleve'], 0)} %")
    c3.metric("Utilisateurs dans ce segment", fr(ligne["n"], 0))
    if age < 18:
        st.warning("Utilisateur mineur : seules des protections activées par défaut sont envisageables (rappel de temps, mode sommeil), sans profilage publicitaire.")
    cases = R["segments"].reset_index()
    cases["court"] = segment_vers_court(cases["segment"])
    cases["etiquette"] = cases["part_stress_eleve"].map(lambda v: f"{fr(v, 0)} %")
    cases["stress_txt"] = cases["stress"].map(fr)
    cases["n_txt"] = cases["n"].map(lambda v: fr(v, 0))
    montrer(carte_chaleur(cases, "court", "groupe_age", "part_stress_eleve", "etiquette", COURTS, GROUPES_AGE, [0, 100], "Stress élevé (%)", 55,
                          [alt.Tooltip("groupe_age:N", title="Âge"), alt.Tooltip("segment:N", title="Segment"),
                           alt.Tooltip("etiquette:N", title="En stress élevé"), alt.Tooltip("stress_txt:N", title="Stress moyen"),
                           alt.Tooltip("n_txt:N", title="Utilisateurs")],
                          titre("Carte des segments : part des utilisateurs en stress élevé",
                                "24 segments construits uniquement à partir du temps passé et de l'âge · cadre orange : l'utilisateur simulé"),
                          "Segment de temps passé (S1 : moins de 20 min · S6 : plus de 290 min)",
                          surligner={"court": segment.split(" ")[0], "groupe_age": groupe}))
    chiffres(R["segments"].rename_axis(["âge", "segment"]))
    st.markdown("""
- Les segments vont de **0 %** à **95 %** d'utilisateurs en stress élevé.
- Dans un même segment de temps, l'âge change fortement le résultat : en S4 (188 à 240 min), **17 %** de stress élevé chez les 13–17 ans contre **51 %** chez les 55–65 ans.
""")
    retenir("une segmentation **simple** (temps passé × âge), **applicable à tous les utilisateurs** et **sans donnée de santé**, qui apporte plus qu'un simple classement par temps passé.")

    st.header("Nos critères d'une bonne segmentation")
    st.markdown("Personne ne nous a dit ce qu'est une bonne segmentation : nous fixons nos propres critères, tous **vérifiables sur les données**.")
    st.table(R["criteres"])
    retenir("les six critères sont atteints : la segmentation est discriminante, utile au-delà du temps passé, applicable à tous, stable, sans risque d'isoler quelqu'un et sans donnée de santé.")

    st.header("Quatre profils de bien-être selon le segment")
    st.markdown("On croise le stress (élevé à partir de 27) et le bonheur (élevé à partir de 7).")
    parts = R["profils"].reset_index().melt(id_vars="segment", var_name="profil", value_name="part")
    parts["court"] = segment_vers_court(parts["segment"])
    parts["ordre"] = parts["profil"].map({p: i for i, p in enumerate(PROFILS)})
    parts = parts.sort_values(["court", "ordre"])
    parts["fin"] = parts.groupby("court")["part"].cumsum()
    parts["milieu"] = parts["fin"] - parts["part"] / 2
    parts["etiquette"] = parts["part"].map(lambda v: f"{fr(v, 0)} %")
    parts["etiquette_detail"] = parts["part"].map(lambda v: f"{fr(v)} %")
    base = alt.Chart(parts).encode(x=alt.X("court:N", sort=COURTS, title="Segment de temps passé", axis=alt.Axis(labelAngle=0)))
    empile = base.mark_bar(size=46, stroke=SURFACE, strokeWidth=1.5).encode(
        y=alt.Y("part:Q", stack="zero", title="Part des utilisateurs", scale=alt.Scale(domain=[0, 100]), axis=AXE_POURCENT),
        color=alt.Color("profil:N", scale=alt.Scale(domain=PROFILS, range=RAMPE_4), title=None, legend=alt.Legend(columns=2)),
        order=alt.Order("ordre:Q", sort="ascending"),
        tooltip=[alt.Tooltip("segment:N", title="Segment"), alt.Tooltip("profil:N", title="Profil"), alt.Tooltip("etiquette_detail:N", title="Part")])
    etiquettes = base.mark_text(fontSize=12).encode(
        y="milieu:Q", text="etiquette:N",
        color=alt.condition(f"datum.profil == '{PROFILS[0]}'", alt.value(INK), alt.value("white"))).transform_filter("datum.part >= 12")
    montrer((empile + etiquettes).properties(title=titre("Plus le temps passé augmente, plus le bien-être se dégrade",
                                                         "Répartition des quatre profils de bien-être par segment · survolez les barres"), height=400))
    chiffres(R["profils"].rename_axis(index="segment", columns="profil"))
    st.markdown("""
- En S1, près de **quatre utilisateurs sur cinq** sont sereins et heureux.
- En S6, près des **trois quarts** sont stressés et peu heureux.
- Entre les deux, on passe d'abord par « serein mais peu heureux », puis par « stressé mais heureux ».
""")
    conclusion_produit("ces profils décrivent **le parcours du bien-être selon la dose d'usage**. Ils restent une lecture des résultats agrégés : **on ne les attribue pas à un utilisateur**, puisqu'ils reposent sur des données de santé du panel.")
    retenir("plus la dose d'usage augmente, plus les utilisateurs glissent d'un profil serein et heureux vers un profil stressé et peu heureux.")


def page_protection():
    st.title("7 · Protection des données")
    st.markdown("La consigne nous demande de prendre position, pour les utilisateurs de l'Union européenne et du Royaume-Uni, y compris les moins de 18 ans, sur deux questions.")
    st.header("Sur quelles variables les segments peuvent-ils reposer pour du ciblage ?")
    st.markdown("""
**Uniquement le temps passé par jour et l'âge.**
- Ce sont des données qu'Instagram détient **pour tous ses utilisateurs**, et ce ne sont **pas des données de santé**.
- **Les variables de santé et de bien-être sont exclues** (stress, bonheur, sommeil, IMC, tension, tabac, alcool, alimentation, sport) : ce sont des données sensibles au sens de l'article 9 du RGPD ([CNIL](https://www.cnil.fr/fr/definition/donnee-sensible)), données seulement pour l'étude bien-être.
- **Les autres variables de profil sont exclues aussi** (genre, revenu, emploi, couple, enfants, pays) : elles n'apportent rien, et le RGPD demande de ne traiter que les données nécessaires.
""")
    st.header("Placer un utilisateur dans un segment peut-il révéler quelque chose sur sa santé ?")
    groupe_max, segment_max = R["segment_max"]
    nb, total, part = R["revelateurs"]
    c1, c2 = st.columns(2)
    c1.metric("Segment le plus révélateur", f"{segment_max.split(' ')[0]} · {groupe_max}",
              delta=f"{fr(R['part_max'], 0)} % en stress élevé", delta_color="off")
    c2.metric("Segments à 80 % de stress élevé ou plus", f"{nb} sur {total}", delta=f"{fr(part, 0)} % des utilisateurs", delta_color="off")
    st.markdown("""
**Oui.** Même construits sans donnée de santé, certains segments laissent deviner un état de stress avec une forte probabilité. Une donnée qui révèle indirectement un état de santé doit être traitée comme une donnée de santé. D'où trois conditions :
- **nommer les segments par l'usage** (« S6 Très intensif, 55–65 ans »), jamais par le stress attendu ;
- **ne stocker aucun score de stress** par utilisateur ;
- **réserver les segments aux outils de protection** (rappels de temps, mode sommeil), sans publicité.
""")
    st.header("Les mineurs")
    st.markdown("""
- **Royaume-Uni :** le code de conception adapté à l'âge de l'ICO demande que **le profilage des enfants soit désactivé par défaut**, sauf raison impérieuse dans leur intérêt ([résumé par RPC](https://www.rpclegal.com/snapshots/data-protection/ico-age-appropriate-design-code-for-information-society-services/)).
- **Union européenne :** le DSA (article 28) **interdit les publicités fondées sur le profilage** d'un utilisateur dont la plateforme sait qu'il est mineur ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2022/2065/oj)).
""")
    st.header("Les mesures que nous appliquons et recommandons")
    st.markdown("""
- **Seuil de 100 utilisateurs :** aucune ligne individuelle ni aucun groupe de moins de 100 personnes n'est affiché.
- **Données brutes jamais publiées :** le dossier `data/` est exclu du dépôt du projet par le fichier `.gitignore` ; seule la copie qui sert à l'application en ligne se trouve dans un dépôt privé.
- **Une section « Limites et protection des données »** dans le notebook, l'application et le README.
- **Interdiction écrite** d'utiliser les segments pour la publicité ou de les transmettre aux annonceurs.
- **Informer les utilisateurs** du classement en segments, dans la politique de confidentialité.
- **Inscrire le traitement au registre des traitements**, avec sa finalité, les données utilisées et la durée de conservation.
""")
    st.markdown("**Vérification de la règle des 100 utilisateurs**")
    tableau(R["tailles"], 0)


def page_limites():
    st.title("8 · Limites")
    st.markdown("Ce que nos données **ne permettent pas d'affirmer**, et les points à garder en tête avant d'appliquer ces résultats à de vrais utilisateurs.")
    st.header("Pas de cause à effet")
    st.markdown("Tous nos liens sont des **corrélations**. On ne peut pas dire qu'Instagram *cause* le stress : les personnes stressées pourraient aussi passer plus de temps sur l'application. Seules des expériences, où l'on fait varier le temps passé, peuvent tester une cause.")
    st.header("Un panel de volontaires")
    st.markdown("Le stress et le bonheur ne sont mesurés que chez les **volontaires** de l'étude bien-être. Ils ne ressemblent pas forcément à l'ensemble des utilisateurs.")
    st.header("Une réplique synthétique")
    st.markdown(f"""
- **Le lien entre temps passé et stress est très fort** : 71 % des écarts expliqués, contre 0,4 % au maximum dans les études réelles ([Orben & Przybylski, 2019](https://www.oii.ox.ac.uk/technology-use-explains-at-most-0-4-of-adolescent-wellbeing/)).
- **Des effets connus sont absents** : le sommeil et le nombre de pas n'ont aucun lien ici, alors que nos sources les associent au bien-être (partie 1).
- **Les deux versions du fichier (« usage » et « users ») sont presque identiques**, et le nettoyage de l'une n'est pas documenté (partie 0).
- **{fr(R['part_signalees'], 0)} % des lignes ont au moins une incohérence métier** : elles sont signalées, et les résultats ne changent pas sans elles (partie 0).
- **Un lien caché, très probablement artificiel, entre stress et bonheur** :
""")
    c1, c2 = st.columns(2)
    c1.metric("Corrélation stress ↔ bonheur, sur tous les utilisateurs", fr(R["corr_globale"], 2))
    c2.metric("Corrélation stress ↔ bonheur, à temps passé égal", fr(R["corr_temps_egal"], 2))
    cache = R["lien_cache"].reset_index()
    cache["etiquette"] = cache["stress_moyen"].map(fr)
    cache["n_txt"] = cache["n"].map(lambda v: fr(v, 0))
    montrer(barres_simples(cache, "niveau_bonheur", "stress_moyen", "etiquette",
                           titre("À temps égal, les plus heureux sont aussi les plus stressés",
                                 "Stress moyen selon le bonheur, chez les utilisateurs du segment S3 (88 à 188 min par jour)"),
                           "Bonheur déclaré (1–10)", "Stress moyen (0–40)", ["1–2", "3–4", "5–6", "7–8", "9–10"], [0, 25],
                           [alt.Tooltip("niveau_bonheur:N", title="Bonheur"), alt.Tooltip("etiquette:N", title="Stress moyen"),
                            alt.Tooltip("n_txt:N", title="Utilisateurs")], couleur=MUTED))
    st.markdown("""
- Sur l'ensemble des utilisateurs, stress et bonheur **ne sont pas liés**. Mais **à temps passé égal**, ils sont **fortement liés, dans le même sens**.
- **C'est très probablement un effet de la génération des données** : dans la réalité, on s'attend plutôt à ce que les personnes stressées soient moins heureuses. Ce lien ne sert pas à la segmentation.
""")
    st.header("D'autres points de prudence")
    st.markdown("""
- **Le seuil de stress élevé (27)** est une convention de lecture de l'échelle PSS-10, pas un seuil de diagnostic.
- **Les colonnes « story privée » et « partages » n'existent pas** : l'activité privée n'est mesurée que par les messages (partie 4.3).
""")
    retenir("nos résultats décrivent **des tendances fortes dans une réplique synthétique**. Ils indiquent où regarder, mais doivent être **confirmés sur de vraies données**, et ne permettent jamais de conclure à une cause.")


def page_conclusion():
    st.title("9 · Conclusion et recommandations")
    st.header("Le lien entre l'usage d'Instagram et le bien-être")
    st.markdown("""
- **Le temps passé chaque jour est le facteur central.** Il explique **71 %** des écarts de stress (environ +5,4 points par heure) et **16 %** des écarts de bonheur, qui chute surtout aux deux extrêmes. Les plus heureux passent deux fois moins de temps sur l'application que les moins heureux.
- **L'âge change ce lien.** Les plus jeunes passent plus de temps sur Instagram, mais à temps égal, les plus âgés sont plus stressés (+1,2 point par tranche de 10 ans).
- **Les habitudes d'utilisation n'ajoutent rien au temps passé** : intensité des actions, création ou consommation de contenu, activité privée ou publique, connexions « réflexe » ou « immersion ». Toutes leurs différences disparaissent à temps égal.
- **Le sommeil, l'activité physique et le pays ne sont pas liés** à l'usage dans notre panel.
- **Stress et bonheur sont deux indicateurs distincts**, à suivre séparément.
""")
    st.header("Une segmentation utilisable par les équipes produit")
    st.markdown("""
- **Six segments de temps passé (S1 à S6) croisés avec quatre groupes d'âge** : deux informations connues pour tous les utilisateurs, sans donnée de santé.
- La carte des segments donne directement **les groupes à accompagner en priorité**, et un nouvel utilisateur peut y être placé (simulateur de la partie 6).
- **Les limites** (partie 8) : des corrélations et non des causes, un panel de volontaires, et une réplique synthétique.
""")
    st.header("Recommandations")
    st.markdown("""
1. **Un rappel de temps quotidien cumulé, avec un seuil selon l'âge.** Dès le segment S3 (88 à 188 min par jour), 15 % des 55–65 ans sont en stress élevé, contre 2 % des 13–17 ans, qui ne dépassent 15 % qu'en S4. Nous recommandons un rappel **à l'entrée de S3 (environ 1 h 30 par jour) pour les 55–65 ans** et **à l'entrée de S4 (environ 3 h) pour les autres**, **activé par défaut pour les mineurs**. Le rappel doit compter le temps **de toute la journée**, pas celui d'une seule session (partie 4.4).
2. **Faire du temps quotidien passé l'indicateur de suivi numéro un**, par segment, dans les tableaux de bord produit, plutôt que les compteurs d'activité ou le score d'engagement, qui n'apportent rien de plus. Dans les études bien-être, **suivre le stress et le bonheur séparément**.
3. **Réserver les segments aux outils de protection** (rappels, mode sommeil) : jamais de publicité, des segments nommés par l'usage et non par le stress, et une analyse d'impact sur la protection des données avant tout déploiement.
""")
    st.success("**En une phrase :** plus on passe de temps sur Instagram, plus on est stressé, et ce lien est plus fort chez les plus âgés ; une segmentation simple par temps passé et âge permet aux équipes produit de cibler leurs outils de protection, sans utiliser de données de santé.")


def page_sources():
    st.title("Sources")
    st.markdown("""
**Définitions**
- OMS : [constitution de l'Organisation mondiale de la santé](https://www.who.int/fr/about/governance/constitution)
- Santé publique France : [« On a toutes et tous une santé mentale » (sante.fr)](https://www.sante.fr/toutes-et-tous-une-sante-mentale)
- World Happiness Report : [questions fréquentes, échelle de Cantril](https://www.worldhappiness.report/faq/)
- Échelle PSS-10 : [guide de cotation (NovoPsych)](https://novopsych.com.au/wp-content/uploads/2022/02/pss-10-report-PDF.pdf)

**Temps passé, âge et bien-être**
- Riehm et al., 2019, *JAMA Psychiatry* : [présentation par Johns Hopkins](https://hub.jhu.edu/2019/09/11/social-media-teen-mental-health/)
- Liu et al., 2022, méta-analyse dose–effet : [texte intégral (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9103874/)
- Orben & Przybylski, 2019, *Nature Human Behaviour* : [Oxford Internet Institute](https://www.oii.ox.ac.uk/technology-use-explains-at-most-0-4-of-adolescent-wellbeing/)
- Assemblée nationale, question écrite citant le rapport « Enfants et écrans » (2024) : [PDF](https://www.assemblee-nationale.fr/dyn/16/questions/QANR5L16QE18298.pdf)
- Valkenburg, van Driel & Beyens, 2022, *New Media & Society* : [article](https://journals.sagepub.com/doi/10.1177/14614448211065425)
- Modèle de Keyes : [Frontiers in Psychology, 2022](https://www.frontiersin.org/articles/10.3389/fpsyg.2022.885278/full)

**Mode de vie**
- info.gouv.fr, 2025 : [le sommeil et la santé mentale](https://www.info.gouv.fr/actualite/sante-mentale-pourquoi-le-sommeil-joue-un-role-cle)
- Ameli : [activité physique et bien-être](https://www.ameli.fr/assure/sante/themes/activite-physique-sante/sport-et-activite-physique-un-atout-pour-le-bien-etre)

**Protection des données**
- [CNIL, données sensibles](https://www.cnil.fr/fr/definition/donnee-sensible) · [DSA (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2022/2065/oj) · [code de l'ICO (résumé par RPC)](https://www.rpclegal.com/snapshots/data-protection/ico-age-appropriate-design-code-for-information-society-services/)
""")


PAGES = {
    "Introduction": page_introduction,
    "0 · Nettoyage et données": page_donnees,
    "1 · Hypothèses non concluantes": page_hypotheses,
    "2 · Temps passé": page_temps,
    "3 · Âge": page_age,
    "4 · Habitudes d'utilisation": page_habitudes,
    "5 · Stress et bonheur": page_stress_bonheur,
    "6 · Segmentation": page_segmentation,
    "7 · Protection des données": page_protection,
    "8 · Limites": page_limites,
    "9 · Conclusion et recommandations": page_conclusion,
    "Sources": page_sources,
}

with st.sidebar:
    st.markdown("### Rush 4 · Instagram et bien-être")
    choix_page = st.radio("Parties", list(PAGES), label_visibility="collapsed")
    st.divider()
    st.caption(f"{fr(R['n'], 0)} utilisateurs synthétiques · résultats agrégés uniquement, aucun groupe de moins de {MIN_N} utilisateurs.")

PAGES[choix_page]()
