from flask import Flask, request
import pandas as pd
from rapidfuzz import process

app = Flask(__name__)

# Charger Excel
try:
    df = pd.read_excel("films.xlsx", sheet_name=0)
    titres = df.iloc[:, 5].fillna("").astype(str).tolist()
    liens = df.iloc[:, 6].fillna("").astype(str).tolist()
except Exception as e:
    titres = []
    liens = []
    erreur = str(e)


@app.route("/", methods=["GET"])
def home():
    query = request.args.get("q")
    page = int(request.args.get("page", 1))

    html = """
    <style>
    body {font-family: Arial; background: #111; color: white; text-align: center; padding: 30px;}
    input {padding: 10px; width: 250px; border-radius: 10px; border: none;}
    button {padding: 10px 20px; border-radius: 10px; border: none; background: #e50914; color: white;}
    .card {background: #222; padding: 15px; border-radius: 12px; margin: 10px auto; width: 320px;}
    a {color: #00c3ff; text-decoration: none;}
    .nav {margin-top: 20px;}
    </style>
    """

    if not titres:
        return html + f"<h2>❌ Erreur Excel :</h2><p>{erreur}</p>"

    if not query:
        return html + """
        <h1>🎬 Ma vidéothèque</h1>
        <form>
            <input name="q" placeholder="Tape un film...">
            <button type="submit">Rechercher</button>
        </form>
        """

    query_clean = query.lower().strip()

    # 1️⃣ MATCH EXACT
    for i, titre in enumerate(titres):
        if query_clean == titre.lower().strip():
            return html + f"""
            <h1>🎬 Résultat exact</h1>
            <div class="card">
                <b>🎬 {titre}</b><br>
                <a href="{liens[i]}" target="_blank">👉 Voir fiche</a>
            </div>
            <br><a href="/">⬅ Retour</a>
            """

    # 2️⃣ CONTIENT LE MOT
    matches = []
    for i, titre in enumerate(titres):
        if query_clean in titre.lower():
            matches.append((titre, liens[i]))

    # Pagination
    if matches:
        par_page = 5
        total = len(matches)
        start = (page - 1) * par_page
        end = start + par_page
        page_items = matches[start:end]

        bloc = f"<h2>{total} résultats trouvés 👇</h2>"

        for titre, lien in page_items:
            bloc += f"""
            <div class="card">
                <b>🎬 {titre}</b><br>
                <a href="{lien}" target="_blank">👉 Voir fiche</a><br><br>
                <button onclick="navigator.clipboard.writeText('{lien}')">
                    📋 Copier le lien
                </button>
            </div>
            """

        # Navigation
        nav = '<div class="nav">'

        if start > 0:
            nav += f'<a href="/?q={query}&page={page-1}">⬅ Précédent</a> '

        if end < total:
            nav += f'<a href="/?q={query}&page={page+1}">Suivant ➡</a>'

        nav += '</div>'

        return html + bloc + nav + '<br><a href="/">⬅ Nouvelle recherche</a>'

    # 3️⃣ FUZZY (fallback)
    titres_clean = [t.lower() for t in titres]
    results = process.extract(query_clean, titres_clean, limit=5)

    bloc = "<h2>Résultats approximatifs 👇</h2>"

    for match_clean, score, index in results:
        titre = titres[index]
        lien = liens[index]

        bloc += f"""
        <div class="card">
            <b>🎬 {titre}</b><br>
            📊 {score}%<br>
            <a href="{lien}" target="_blank">👉 Voir fiche</a>
        </div>
        """

    return html + bloc + '<br><a href="/">⬅ Nouvelle recherche</a>'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)