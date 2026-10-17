# Rush 4 — Segmentation des utilisateurs d'Instagram : usage et bien-être

Bootcamp Data · Epitech

## Objectif

Étudier les relations entre l'utilisation d'Instagram et le bien-être des utilisateurs, à partir d'une réplique synthétique de 200 000 personnes, et livrer une segmentation qui :

- repose sur l'usage de l'application ;
- explique le lien entre l'usage et le bien-être (stress et bonheur) ;
- est utilisable par les équipes produit ;
- est défendue devant un jury.

## Livrables

| Fichier | Contenu |
|---|---|
| `notebook_Instagram_final.ipynb` | Le notebook complet : choix des données, exploration, variables construites, segmentation, évaluation selon nos critères, limites et protection des données. Il s'exécute de bout en bout et produit des résultats identiques à chaque exécution. |
| `notebook_Instagram_final.py` | La même analyse en application Streamlit interactive, avec un simulateur qui place un nouvel utilisateur dans son segment. |

**Application en ligne :** [notebookinstagramfinal.streamlit.app](https://notebookinstagramfinal.streamlit.app)

## Résultats clés

- **Le temps passé chaque jour est le facteur central** : il explique 71 % des écarts de stress (environ +5,4 points par heure, sur une échelle de 0 à 40) et 16 % des écarts de bonheur, qui chute surtout aux deux extrêmes.
- **L'âge change ce lien** : les plus jeunes passent plus de temps sur Instagram, mais à temps égal, les plus âgés sont plus stressés (+1,2 point par tranche de 10 ans).
- **Les habitudes d'utilisation vont dans le même sens** : les moins heureux et les plus stressés ont un usage plus intensif (plus d'actions, plus de publications, une activité plus publique, des connexions plus fréquentes) et passent plus de temps sur l'application.
- **Le sommeil, l'activité physique et le pays ne sont pas liés** à l'usage dans le panel.
- **Segmentation retenue** : 6 segments de temps passé (S1 à S6) croisés avec 4 groupes d'âge, soit 24 segments construits sans aucune donnée de santé.

## Structure du dépôt

```
.
├── notebook_Instagram_final.ipynb   notebook complet (livrable principal)
├── notebook_Instagram_final.py      application Streamlit
├── requirements.txt                 bibliothèques nécessaires
├── .streamlit/config.toml           thème de l'application
└── data/                            extraits CSV (non versionnés, à ajouter)
```

## Installation

Le projet nécessite Python 3.9 ou plus.

```bash
pip install -r requirements.txt
```

## Données

Les extraits ne sont pas versionnés (dossier `data/` exclu par `.gitignore`). Avant de lancer le projet, placez les deux fichiers fournis dans un dossier `data/` à la racine du dépôt :

```
data/instagram_usage_lifestyleSafe.csv
data/instagram_users_lifestyleSafe.csv
```

## Lancement

Notebook :

```bash
jupyter notebook notebook_Instagram_final.ipynb
```

Application Streamlit :

```bash
python3 -m streamlit run notebook_Instagram_final.py
```

L'application s'ouvre dans le navigateur à l'adresse `http://localhost:8501`.

## Méthode en bref

1. **Nettoyage** : aucune valeur manquante ni doublon ; 26 % des lignes ont au moins une incohérence métier, signalée (`flag_*`) et non supprimée, sans effet sur les résultats.
2. **Choix du fichier** : les deux versions de la réplique ont 52 colonnes sur 58 identiques, dont toutes celles utilisées dans l'analyse.
3. **Analyse « à temps égal »** : chaque habitude est comparée entre utilisateurs qui passent le même temps sur Instagram, pour savoir si elle apporte quelque chose en plus du temps passé.
4. **Segmentation par paliers** plutôt qu'un regroupement automatique, car les variables d'usage sont presque toutes des copies du temps passé.
5. **Évaluation** selon six critères vérifiés sur les données : discrimination, apport au-delà du temps seul, applicabilité à tout utilisateur, stabilité, absence de petits groupes, absence de données de santé.

## Équipe et répartition du travail

| Membre | Responsabilités |
|---|---|
| Jordy | Travail commun |
| Manon D. | Travail commun · oral |
| Manon R. | Travail commun · application Streamlit |
| Mina | Travail commun · présentation finale |
| Tom | Travail commun |

**Travail commun** (toute l'équipe) : nettoyage et choix des données, exploration et tests des hypothèses, analyse du lien entre l'usage et le bien-être, segmentation et critères d'évaluation, protection des données et limites, rédaction du notebook.

## Protection des données et limites

- Aucune ligne individuelle ni aucun groupe de moins de 100 utilisateurs n'est affiché.
- Les segments reposent uniquement sur le temps passé et l'âge ; les variables de santé (article 9 du RGPD) sont exclues.
- Un segment peut laisser deviner un niveau de stress : les segments sont réservés aux outils de protection (rappels de temps, mode sommeil), sans publicité, avec des règles renforcées pour les mineurs (DSA, article 28 ; code de l'ICO au Royaume-Uni).
- Les résultats sont des corrélations, mesurées sur un panel de volontaires et sur une réplique synthétique : ils ne permettent pas de conclure à une cause et doivent être confirmés sur de vraies données.

Le détail se trouve dans les parties 7 (Protection des données) et 8 (Limites) du notebook.
