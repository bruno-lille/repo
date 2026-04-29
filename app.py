# -*- coding: utf-8 -*-

import os
import base64
import requests
import urllib.parse
import unicodedata
import re

ENV = os.getenv("ENV", "DEV")

def get_github_token():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN manquant")
    return token

GITHUB_TOKEN = get_github_token()

from flask import Flask, request, redirect

# 🔥 CRÉATION APP (OBLIGATOIRE)
app = Flask(__name__)

nav_buttons = """
<div class="card">
    <div class="btn-row">
        <a class="btn retour" href="javascript:history.back()">⬅️ Retour</a>
        <a class="btn new" href="/">❌ Annuler</a>
    </div>
</div>
"""

APP_VERSION = "V1-dev"
APP_BUILD = "2026-04-29_10-32-16"
APP_NOTE = "dev en cours"






# 🔧 Chemin base de données (UNIQUE)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "films.db")

# 🔄 Cache mémoire
DATA = None

def reset_cache():
    global DATA
    DATA = None
    

     
#------------FONCTION SQL------------

def search_films_sql(query, exact_mode=False):
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    q = query.lower()

    if exact_mode:
        cursor.execute(
            "SELECT * FROM films WHERE LOWER(titre) = ?",
            (q,)
        )
    else:
        cursor.execute("SELECT * FROM films")

    results = cursor.fetchall()
    conn.close()

    return results



# 🔁 RESTORE DB DEPUIS GITHUB (VERSION SAFE)
def get_latest_backup(files, headers):

    latest_file = None
    latest_date = None

    for f in files:

        try:
            url = f["git_url"]
            r = requests.get(url, headers=headers, timeout=5)

            if r.status_code != 200:
                continue

            data = r.json()

            # 🔐 sécurisation accès date
            date = data.get("committer", {}).get("date")

            if not date:
                continue

            if not latest_date or date > latest_date:
                latest_date = date
                latest_file = f

        except Exception as e:
            print("⚠️ erreur fichier backup :", e)
            continue

    return latest_file


def restore_db():

    try:
        token = GITHUB_TOKEN
        repo = "bruno-lille/repo"

        if not token or not repo:
            print("❌ Variables GitHub manquantes")
            return

        headers = {
            "Authorization": f"token {token}"
        }

        # 📥 récupérer les backups
        url = f"https://api.github.com/repos/{repo}/contents/backups"
        r = requests.get(url, headers=headers, timeout=5)

        if r.status_code != 200:
            print("❌ Impossible de récupérer les backups")
            return

        files = r.json()

        # 🔥 garder uniquement les .db
        db_files = [f for f in files if f["name"].endswith(".db")]

        if not db_files:
            print("❌ Aucun backup .db trouvé")
            return

        latest = sorted(db_files, key=lambda x: x["name"], reverse=True)[0]

        download_url = latest["download_url"]

        r = requests.get(download_url, timeout=5)

        if r.status_code != 200:
            print("❌ Erreur téléchargement DB")
            return

        # 💾 écriture directe (PAS de vérification locale)
        with open(DB_PATH, "wb") as f:
            f.write(r.content)

        print(f"✅ DB restaurée : {latest['name']}")

    except Exception as e:
        print("❌ ERREUR RESTORE :", e)

def init_app():
    if ENV == "PROD":
        print("🌐 Mode PROD → vérification DB")

        if not os.path.exists(DB_PATH):
            print("📥 DB absente → restauration GitHub")
            restore_db()
        else:
            print("✅ DB déjà présente → OK")

    else:
        print("🧪 Mode DEV → pas de restore")




TMDB_API_KEY = os.getenv("TMDB_API_KEY")




COL = {
    "EMPLACEMENT": 1,
    "TYPE": 3,
    "DISC_ID": 5,   # ✅ colonne E
    "TITRE": 6,
    "ALLOCINE": 7,
    "TMDB_ID": 13,
    "JAQUETTE": 14,
    "ANNEE": 15,
    "GENRES": 16,
    "RESUME": 17,
    "CASTING": 18,
    "ORDRE": 11
}

# ----------- CHARGEMENT SQL LIGHT -----------
def load_data():
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM films
    ORDER BY
        CASE WHEN ordre IS NULL THEN 999999 ELSE ordre END ASC,
        annee ASC
    """)
    rows = cursor.fetchall()

    titres, liens = [], []
    col_A, col_C = [], []
    tmdb_ids, jaquettes = [], []
    annees, genres = [], []
    resumes, casting = [], []
    disc_ids, ordres = [], []

    for row in rows:
        disc_ids.append(row[1])
        col_A.append(row[2])
        col_C.append(row[3])
        titres.append(row[4])
        liens.append(row[5])
        tmdb_ids.append(row[6])
        jaquettes.append(row[7])
        annees.append(row[8])
        genres.append(row[9])
        resumes.append(row[10])
        casting.append(row[11])
        ordres.append(row[12])

    conn.close()

    return titres, liens, col_A, col_C, tmdb_ids, jaquettes, annees, genres, resumes, casting, disc_ids, ordres
    
def load_data_cached():
    global DATA

    if DATA is None:
        DATA = load_data()

    return DATA


def short_text(text, max_len=140):
    return text if len(text) <= max_len else text[:max_len] + "..."

      
        
def search_tmdb_multi(query):
    print("TMDB KEY:", TMDB_API_KEY)
    print("QUERY:", query)
    print("QUERY TMDB:", query)
    print("API KEY:", TMDB_API_KEY)
    query = query.strip()

    results = []

    def fetch(lang):
        try:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": lang,
                "region": "FR",
                "include_adult": False
            }

            data = requests.get(url, params=params, timeout=5).json()

            for film in data.get("results", []):
                poster = film.get("poster_path")
                img = f"https://image.tmdb.org/t/p/w300{poster}" if poster else ""

                results.append({
                    "id": film["id"],
                    "title": film["title"],
                    "year": film.get("release_date", "")[:4],
                    "img": img
                })
        except:
            pass

    # 🔥 recherche FR
    fetch("fr-FR")

    # 🔥 fallback anglais
    if len(results) < 5:
        fetch("en-US")

    # 🔥 suppression doublons
    unique = {film["id"]: film for film in results}

    # 🔥 tri par année décroissante
    sorted_results = sorted(
        unique.values(),
        key=lambda x: (x["year"] or "0", x["title"]),
        reverse=True
    )

    return sorted_results[:5]

# ----------- EXTRACTION ID TMDB -----------

    
def extract_tmdb_id(value):

    value = value.strip()

    # cas simple : nombre direct
    if value.isdigit():
        return value

    # cas URL TMDB (robuste)
    match = re.search(r'/movie/(\d+)', value)
    if match:
        return match.group(1)

    return None
    
def generate_disc_id(ws):

    max_id = 0

    for row in ws.iter_rows(min_row=2):

        val = str(row[COL["DISC_ID"] - 1].value or "").strip()

        if val.startswith("DISC-"):
            try:
                num = int(val.replace("DISC-", ""))
                if num > max_id:
                    max_id = num
            except:
                pass

    new_id = max_id + 1

    return f"DISC-{str(new_id).zfill(5)}"
    
def find_row_by_disc_id(ws, disc_id):

    for idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        val = str(row[COL["DISC_ID"] - 1].value or "").strip()

        if val == disc_id:
            return idx

    return None


# ----------- STYLE GLOBAL -----------
def get_style():
    return """
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    
    <script>
    function updateCount() {

        let q = document.getElementById("search").value;

        if (q.length === 0) {
            document.getElementById("count").innerText = "";
            return;
        }

        fetch("/count?q=" + encodeURIComponent(q))
            .then(res => res.text())
            .then(data => {
                document.getElementById("count").innerText =
                    data + " résultats";
            });
    }
    </script>
    
    <script>
    function setTMDB(id) {
        const input = document.getElementById("tmdb_input");

        if (!input) {
            alert("Champ TMDB introuvable");
            return;
        }

        input.value = id;
        input.focus();

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function setTitle(title) {
        const input = document.getElementById("title");

        if (!input) {
            alert("Champ titre introuvable");
            return;
        }

        input.value = title;
        input.focus();
        input.style.background = "#2a9df4";

        setTimeout(() => {
            input.style.background = "";
        }, 300);

        window.scrollTo({ top: 0, behavior: "smooth" });
    }
    </script>
    
    <style>
    body {font-family: Arial; background:#111; color:white; text-align:center; padding:15px;}

    input {
        padding:14px;
        width:85%;
        font-size:16px;
        border-radius:10px;
        border:none;
        text-align:center;
    }

    .card {
        background:#1c1c1c;
        padding:15px;
        border-radius:16px;
        margin:15px auto;
        width:95%;
        max-width:420px;
    }

    img {width:100%; border-radius:12px;}

    .titre a {
        color:#4fc3f7;
        font-size:18px;
        font-weight:bold;
        text-decoration:none;
    }

    .btn-row {
        display:flex;
        gap:8px;
        margin-top:12px;
    }

    .btn {
        flex:1;
        padding:12px;
        border-radius:10px;
        text-decoration:none;
        font-weight:bold;
        font-size:14px;
    }
    
    .btn:hover {
        opacity:0.85;
    }

    .allocine {
        background:#2a9df4;
        color:white;
        font-weight:bold;
    }
    .new {background:#e50914; color:white;}
    .update {
        background:#ffb74d;
        color:black;
    }
    .retour {background:#444; color:white;}
    </style>
    """
#-----------Appli---------------



def normalize(text):
    if not text:
        return ""

    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    text = re.sub(r'[^a-z0-9]', '', text)

    return text
    
def normalize_words(text):
    if not text:
        return []

    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # garder les mots séparés
    words = re.findall(r'\b[a-z0-9]+\b', text)

    return words
       
def safe_int(val, default=0):
    try:
        return int(val)
    except:
        return default

# ----------- HOME -----------
@app.route("/", methods=["GET"])
def home():

    show_suggest = request.args.get("suggest")
    print("SUGGEST =", show_suggest)

    titres, liens, col_A, col_C, tmdb_ids, jaquettes, annees, genres, resumes, casting, disc_ids, ordres = load_data_cached()

    query_raw = request.args.get("q", "").strip()
    mode = request.args.get("mode")

    exact_mode = False

    if query_raw.startswith("(") and query_raw.endswith(")"):
        exact_mode = True
        query = query_raw[1:-1].strip()
    else:
        query = query_raw

    html = get_style()

    # =========================
    # 🔥 PAGE ACCUEIL
    # =========================
    if not query:

        html += f"""
        <div style="
            position:fixed;
            top:8px;
            right:10px;
            font-size:12px;
            color:white;
            background:#222;
            padding:4px 8px;
            border-radius:6px;
            z-index:9999;
        ">
            {APP_VERSION} | {APP_BUILD}
        </div>

        <h1>🎬 Ma vidéothèque</h1>
      

        <form>

            <div id="count" style="font-size:20px; margin-bottom:10px;"></div>

            <input name="q" id="search" placeholder="Tape un film..." onkeyup="updateCount()">

            <div class="card">
                <div class="btn-row">
                    <button class="btn allocine" name="mode" value="fast">🔎 Recherche</button>
                    <button class="btn new" name="mode" value="poster">🎬 Jaquettes</button>
                </div>
            </div>
        </form>
        """

        return html

    # =========================
    # 🔍 RECHERCHE
    # =========================
    rows = search_films_sql(query, exact_mode)
    results = list(rows)

    # 🔥 fallback large si vide
    if not results:
        rows = search_films_sql("", False)
        results = list(rows)

    # 🔥 normalisation
    # 🔥 NORMALISATION
    q_norm = normalize(query)

    # 🔥 découpage AVANT normalisation
    q_words_raw = query.lower().split()

    # 🔥 mots normalisés individuellement
    q_words = [normalize(w) for w in q_words_raw]

    filtered = []

    for row in results:

        titre_norm = normalize(row["titre"])

        # 🔥 MODE EXACT
        if exact_mode:
            if titre_norm == q_norm:
                filtered.append(row)
            continue

        # 🔥 MODE MULTI-MOTS INTELLIGENT
        match = True

        for q in q_words:
            if q not in titre_norm:
                match = False
                break

        if match:
            filtered.append(row)

    results = [r for r in filtered if r["titre"]]

    # =========================
    # 🎯 SI RESULTATS
    # =========================
    if results:

        bloc = f"<h2>🎬 {query} {len(results)} résultat(s)</h2>"
        bloc += nav_buttons

        for row in results:

            poster_html = f'<img src="{row["jaquette"]}">' if row["jaquette"] else ""

            bloc += f"""
            <div class="card">
                {poster_html}

                <div class="titre">
                    <div style="color:#888; font-size:12px; margin-bottom:4px;">
                        🆔 {row["disc_id"]}
                    </div>

                    <a href="https://www.themoviedb.org/movie/{row["tmdb_id"]}" target="_blank">
                        {row["titre"]}
                    </a>
                </div>

                <div style="color:#b0b0b0; font-size:16px; margin-top:6px;">
                    📀 {row["type"]} &nbsp;&nbsp;
                    📁 {row["emplacement"]} &nbsp;&nbsp;
                    📅 {row["annee"]}
                </div>

                <div>{row["genres"]}</div>
                <div>{row["casting"]}</div>

                <div class="btn-row">
                    <a class="btn allocine" href="{row["allocine"]}" target="_blank">Allociné</a>
                    <a class="btn update" href="/suggest_update/{row["disc_id"]}?q={urllib.parse.quote(query_raw)}">🔄 Corriger</a>
                    <a class="btn new" href="/delete/{row["disc_id"]}" onclick="return confirm('Supprimer ce film ?')">
                        🗑 Supprimer
                    </a>
                </div>
            </div>
            """
        query_encoded = urllib.parse.quote(query_raw)

        bloc += f"""
        <div class="card">
            <a class="btn allocine" href="/?q={query_encoded}&mode={mode}&suggest=1">
                🔎 Plus de résultats TMDB
            </a>
        </div>
        """
        
        # 🔥 SUGGESTIONS TMDB
        if show_suggest:
            results_tmdb = search_tmdb_multi(query_raw)

            bloc += "<h2>🎬 Suggestions TMDB</h2>"

            for film in results_tmdb:
                bloc += f"""
                <div class="card">
                    <img src="{film['img'] or 'https://via.placeholder.com/300x450?text=No+Image'}">
                    <div>{film['title']} ({film['year']})</div>

                    <div class="btn-row">
                        <a class="btn new" href="/add/{film['id']}?q={urllib.parse.quote(query_raw)}">
                            ➕ Ajouter
                        </a>
                    </div>
                </div>
                """

        bloc += nav_buttons
        return html + bloc
        
    # 🔥 AUCUN RESULTAT → TMDB DIRECT
    results_tmdb = search_tmdb_multi(query_raw)

    # =========================
    # 🎬 SI TMDB TROUVE
    # =========================
    if results_tmdb:

        bloc = f"<h2>🎬 {query} n'existe pas dans ma liste mais voici les résultats TMDB</h2>"
        bloc += nav_buttons

        for film in results_tmdb:
            bloc += f"""
            <div class="card">
                <img src="{film['img'] or 'https://via.placeholder.com/300x450?text=No+Image'}">
                <div>{film['title']} ({film['year']})</div>

                <div class="btn-row">
                    <a class="btn new" href="/add/{film['id']}?q={urllib.parse.quote(query_raw)}">
                        ➕ Ajouter
                    </a>
                </div>
            </div>
            """

        bloc += nav_buttons
        return html + bloc

    # =========================
    # ❌ SI TMDB VIDE → FORMULAIRE
    # =========================
    query_encoded = urllib.parse.quote(query_raw)

    bloc = f"<h2>❌ {query} introuvable — Ajout manuel</h2>"
    bloc += nav_buttons

    bloc += f"""
    <div class="card">
        <h3>✍️ Ajouter ce film</h3>

        <form method="post" action="/manual_add">

            <input name="title" value="{query.title()}" placeholder="Titre" required><br><br>

            <input name="emplacement" placeholder="📁 Emplacement"><br><br>

            <input name="type" placeholder="📀 Type (DVD/BLURAY)"><br><br>

            <input name="allocine" value="https://www.google.com/search?q={query_encoded}+allocine" placeholder="🔗 Allociné"><br><br>

            <input name="tmdb_input" placeholder="ID ou lien TMDB"><br><br>

            <div class="btn-row">
                <a class="btn allocine" href="https://www.google.com/search?q={query_encoded}+allocine+film" target="_blank">
                    🎬 Chercher Allociné
                </a>

                <a class="btn allocine" href="https://www.themoviedb.org/search?query={query_encoded}" target="_blank">
                    🔎 Chercher TMDB
                </a>
            </div>

            <br>

            <button class="btn new">➕ Ajouter</button>

        </form>
    </div>
    """

    bloc += nav_buttons
    return html + bloc


 

# ----------- PAGE CORRECTION -----------
@app.route("/suggest_update/<disc_id>")
def suggest_update(disc_id):

    import sqlite3
    import urllib.parse

    query = request.args.get("q", "")
    query_encoded = urllib.parse.quote(query)
    results_tmdb = search_tmdb_multi(query)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM films WHERE disc_id = ?", (disc_id,))
    film = cursor.fetchone()
    conn.close()

    if not film:
        return "❌ Film introuvable"

    title = film["titre"] or ""
    emplacement = film["emplacement"] or ""
    type_disc = film["type"] or ""
    allocine = film["allocine"] or ""
    tmdb_id = film["tmdb_id"] or ""
    ordre = film["ordre"] or ""

    html = get_style()

    html += f"""
    <div style="
        position:fixed;
        top:10px;
        right:15px;
        font-size:12px;
        color:#888;
        z-index:999;
    ">
        {APP_VERSION} | {APP_BUILD}
    </div>
    """

    html += f"""
    <h2>🛠 Modification / Mise à jour</h2>

    <div class="card">
        <a class="btn retour" href="/?q={query}">⬅️ Retour</a>
        <a class="btn new" href="/">❌ Annuler</a>
    </div>

    <div class="card">
        <h3>✏️ Modifier complètement</h3>

        <form action="/manual_update/{disc_id}?q={query_encoded}" method="post">

            <input id="title" name="title" value="{title}" placeholder="Titre"><br><br>

            <input name="emplacement" value="{emplacement}" placeholder="📁 Emplacement"><br><br>

            <input name="type" value="{type_disc}" placeholder="📀 Type (DVD/BLURAY)"><br><br>

            <input name="allocine" value="{allocine}" placeholder="🔗 Allociné"><br><br>

            <input name="ordre" value="{ordre}" placeholder="🔢 Ordre" type="number" min="1"><br><br>

            <input id="tmdb_input" name="tmdb_input" value="{tmdb_id}" placeholder="ID ou lien TMDB"><br><br>

            <button type="submit" class="btn update">💾 Mettre à jour</button>

        </form>
    </div>
    """

    for film in results_tmdb:

        title_safe = film["title"].replace("'", "\\'")

        html += f"""
        <div class="card">
            <a href="https://www.themoviedb.org/movie/{film['id']}" target="_blank">
                <img src="{film['img'] or 'https://via.placeholder.com/300x450?text=No+Image'}">
            </a>

            <div class="titre">{film['title']} ({film['year']})</div>

            <div class="btn-row">
                <button type="button" class="btn update"
                    onclick="window.location.href='/confirm_update/{disc_id}/{film['id']}?q={query_encoded}'">
                    ⚡ Remplir automatiquement
                </button>
            </div>
        </div>
        """
        

    return html


# ----------- UPDATE AUTO -----------
@app.route("/confirm_update/<disc_id>/<int:tmdb_id>")
def confirm_update(disc_id, tmdb_id, query=""):

    import sqlite3

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "fr-FR", "append_to_response": "credits"}

    data = requests.get(url, params=params, timeout=5).json()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE films SET
        tmdb_id = ?,
        jaquette = ?,
        annee = ?,
        genres = ?,
        resume = ?,
        casting = ?
    WHERE disc_id = ?
    """, (
        tmdb_id,
        f"https://image.tmdb.org/t/p/w300{data.get('poster_path','')}",
        data.get("release_date", "")[:4],
        ", ".join([g["name"] for g in data.get("genres", [])]),
        data.get("overview", ""),
        ", ".join([c["name"] for c in data.get("credits", {}).get("cast", [])[:5]]),
        disc_id
    ))

    conn.commit()
    conn.close()

    reset_cache()

    query = request.args.get("q", "")
    return redirect(f"/?q={query}")



# ----------- UPDATE MANUEL (ID OU URL) -----------
@app.route("/manual_update/<disc_id>", methods=["POST"])
def manual_update(disc_id):

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔥 vérifie si le film existe
    cursor.execute("SELECT id FROM films WHERE disc_id = ?", (disc_id,))
    film = cursor.fetchone()

    if not film:
        conn.close()
        return "❌ Introuvable"

    # 🔥 mise à jour des champs
    cursor.execute("""
        UPDATE films SET
            titre = ?,
            emplacement = ?,
            type = ?,
            allocine = ?,
            ordre = ?,
            tmdb_id = ?,
            jaquette = ?,
            annee = ?,
            genres = ?,
            resume = ?,
            casting = ?
        WHERE disc_id = ?
    """, (
        request.form.get("title", ""),
        request.form.get("emplacement", ""),
        request.form.get("type", ""),
        request.form.get("allocine", ""),
        int(request.form.get("ordre")) if request.form.get("ordre") else None,
        request.form.get("tmdb_input", ""),
        request.form.get("poster", ""),
        request.form.get("year", ""),
        request.form.get("genres", ""),
        request.form.get("overview", ""),
        request.form.get("cast", ""),
        disc_id
    ))

    conn.commit()
    conn.close()
    reset_cache()

    # 🔥 TMDB optionnel
    raw = request.form.get("tmdb_input", "")
    tmdb_id = extract_tmdb_id(raw) if raw else None

    query = request.args.get("q", "")

    if tmdb_id:
        
        reset_cache()
        return confirm_update(disc_id, int(tmdb_id), query)

    
    return redirect(f"/?q={query}")


# ----------- PAGE AJOUT FILM -----------
@app.route("/add/<int:tmdb_id>")
def add_movie(tmdb_id):

    emplacement = request.args.get("emplacement", "")
    type_disc = request.args.get("type", "")
    allocine = request.args.get("allocine", "")

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR",
        "append_to_response": "credits"
    }

    data = requests.get(url, params=params, timeout=5).json()

    title = data.get("title", "")
    year = data.get("release_date", "")[:4]
    genres = ", ".join([g["name"] for g in data.get("genres", [])])
    overview = data.get("overview", "")
    poster = f"https://image.tmdb.org/t/p/w300{data.get('poster_path','')}"
    cast = ", ".join([c["name"] for c in data.get("credits", {}).get("cast", [])[:5]])
    query_allocine = urllib.parse.quote(f"{title} {year} allocine fichefilm")

    return get_style() + f"""
    <h2>➕ Ajouter ce film</h2>

    <div class="card">
        <img src="{poster}">
        <h3>{title} ({year})</h3>
        <p>{genres}</p>
        <p>{cast}</p>
        <p>{overview}</p>
    </div>

    <div class="card">
        <form method="post" action="/confirm_add">

            <input type="hidden" name="tmdb_id" value="{tmdb_id}">
            <input type="hidden" name="title" value="{title}">
            <input type="hidden" name="year" value="{year}">
            <input type="hidden" name="genres" value="{genres}">
            <input type="hidden" name="overview" value="{overview}">
            <input type="hidden" name="cast" value="{cast}">
            <input type="hidden" name="poster" value="{poster}">
            
            <input name="title" value="{title}" required><br><br>

            <input name="emplacement" value="{emplacement}" placeholder="📁 Emplacement" required><br><br>

            <input name="type" value="{type_disc}" placeholder="📀 Type (DVD/BLURAY)" required><br><br>



            <input name="allocine" 
                  value="https://www.google.com/search?q={query_allocine}">

            <div class="btn-row">
                <a class="btn allocine" 
                   href="https://www.google.com/search?q={query_allocine}" 
                   target="_blank">
                    🎬 Chercher Allociné
                </a>
            </div>
            <br>

            <button class="btn new">✅ Ajouter</button>
        </form>
    </div>

    <div class="card">
        <a class="btn retour" href="/">⬅️ Retour</a>
    </div>
    """
            

# ----------- CONFIRM ADD -----------
@app.route("/confirm_add", methods=["POST"])
def confirm_add():

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔥 générer DISC_ID automatiquement
    cursor.execute("SELECT disc_id FROM films ORDER BY id DESC LIMIT 1")
    last = cursor.fetchone()

    if last and last[0].startswith("DISC-"):
        num = int(last[0].replace("DISC-", ""))
        new_id = f"DISC-{str(num + 1).zfill(5)}"
    else:
        new_id = "DISC-00001"

    cursor.execute("""
    INSERT INTO films (
        disc_id, emplacement, type, titre, allocine,
        tmdb_id, jaquette, annee, genres, resume, casting, ordre
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id,
        request.form.get("emplacement", ""),
        request.form.get("type", ""),
        request.form.get("title", ""),
        request.form.get("allocine", ""),
        request.form.get("tmdb_id", ""),
        request.form.get("poster", ""),
        request.form.get("year", ""),
        request.form.get("genres", ""),
        request.form.get("overview", ""),
        request.form.get("cast", ""),
        None
    ))

    conn.commit()
    conn.close()

    reset_cache()

    return get_style() + """
    <h2>✅ Film ajouté !</h2>

    <div class="card">
        <a class="btn allocine" href="/">🏠 Retour accueil</a>
    </div>
    """
    
# ----------- suppression ligne -----------

@app.route("/delete/<disc_id>")
def delete_movie(disc_id):

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM films WHERE disc_id = ?", (disc_id,))

    conn.commit()
    conn.close()

    reset_cache()

    return """
    <div style="font-size:28px; text-align:center; margin-top:40px;">
        🗑 Film supprimé
    </div>

    <div style="text-align:center; margin-top:20px;">
        <a href="/" style="font-size:20px;">⬅️ Retour</a>
    </div>
    """
#------------COMPTEUR--------------


@app.route("/count")
def count():

    query_raw = request.args.get("q", "").strip()

    if not query_raw:
        return "0"

    # 🔥 gestion mode exact (parenthèses)
    exact_mode = False
    if query_raw.startswith("(") and query_raw.endswith(")"):
        exact_mode = True
        query = query_raw[1:-1].strip()
    else:
        query = query_raw

    # 🔥 récupération des données
    rows = search_films_sql(query, exact_mode)
    results = list(rows)

    # 🔥 fallback large
    if not results:
        rows = search_films_sql("", False)
        results = list(rows)

    # 🔥 NORMALISATION IDENTIQUE À home()
    q_norm = normalize(query)
    q_words = [normalize(w) for w in query.lower().split()]

    filtered = []

    for row in results:

        titre_norm = normalize(row["titre"])

        # 🔥 mode exact
        if exact_mode:
            if titre_norm == q_norm:
                filtered.append(row)
            continue

        # 🔥 multi-mots intelligent
        match = True
        for q in q_words:
            if q not in titre_norm:
                match = False
                break

        if match:
            filtered.append(row)

    return str(len(filtered))
    
    #----------Tout Automatique------------
    

@app.route("/prefill/<disc_id>/<int:tmdb_id>")
def prefill(disc_id, tmdb_id):

    import sqlite3

    # 🔥 récupération TMDB
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR",
        "append_to_response": "credits"
    }

    data = requests.get(url, params=params, timeout=5).json()

    poster_path = data.get("poster_path")
    poster = f"https://image.tmdb.org/t/p/w300{poster_path}" if poster_path else ""

    genres = ", ".join([g["name"] for g in data.get("genres", [])]) if data.get("genres") else ""
    overview = data.get("overview", "")
    cast = ", ".join([c["name"] for c in data.get("credits", {}).get("cast", [])[:5]])

    title = data.get("title", "")
    year = data.get("release_date", "")[:4]

    # 🔥 récupération données existantes (SQLite)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM films WHERE disc_id = ?", (disc_id,))
    film = cursor.fetchone()

    conn.close()

    emplacement = film["emplacement"] if film else ""
    type_disc = film["type"] if film else ""
    allocine = film["allocine"] if film else ""
    ordre = film["ordre"] if film else ""

    return get_style() + f"""
    <h2>✨ Pré-remplissage</h2>

    <div class="card">
        <h3>{title} ({year})</h3>
    </div>

    <div class="card">
        <form action="/manual_update/{disc_id}" method="post">
        
            

            <input name="title" value="{title}" placeholder="Titre"><br><br>

            <input name="emplacement" value="{emplacement}" placeholder="📁 Emplacement"><br><br>

            <input name="type" value="{type_disc}" placeholder="📀 Type (DVD/BLURAY)"><br><br>

            <input name="allocine" value="{allocine}" placeholder="🔗 Allociné"><br><br>

            <input name="ordre" value="{ordre}" placeholder="🔢 Ordre" type="number" min="1"><br><br>

            <input id="tmdb_input" name="tmdb_input" value="{tmdb_id}" placeholder="ID ou lien TMDB">

            <button class="btn new">✅ Valider</button>

            <div class="card">
                <a class="btn retour" href="javascript:history.back()">⬅️ Retour</a>
            </div>

        </form>
    </div>
    """
#-------------SAUVEGARDE VERS GITHUB----------------

@app.route("/backup_db", methods=["GET", "HEAD"])
def backup_db():

    import os
    import base64
    import requests
    import sqlite3
    import shutil
    from datetime import datetime

    print("STEP 1: start backup")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "films.db")
    TMP_PATH = os.path.join(BASE_DIR, "backup_temp.db")

    token = GITHUB_TOKEN
    repo = "bruno-lille/repo"

    headers = {
        "Authorization": f"token {token}"
    }

    if not os.path.exists(DB_PATH):
        return "❌ films.db introuvable"

    print("STEP 2: DB found")

    try:
        # 🔥 1. Sécuriser SQLite
        conn = sqlite3.connect(DB_PATH)
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(FULL);")
        conn.close()

        # 🔥 2. Copier version stable
        shutil.copyfile(DB_PATH, TMP_PATH)
        print("STEP 3: DB copied")

        # 🔥 3. Lire copie
        with open(TMP_PATH, "rb") as f:
            raw = f.read()

        print("STEP 4: DB read OK, size =", len(raw))

        if len(raw) < 1000:
            return "❌ DB invalide"

        content = base64.b64encode(raw).decode()

        # 🔥 4. Upload GitHub
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backups/films_{now}.db"

        url = f"https://api.github.com/repos/{repo}/contents/{filename}"

        data = {
            "message": f"backup {now}",
            "content": content,
            "branch": "main"
        }

        r = requests.put(url, json=data, headers=headers)
        backup_status = r.status_code

        print("STEP 5: upload OK", r.status_code)

        if r.status_code not in [200, 201]:
            return f"❌ Backup erreur {r.status_code}"

        print(f"✅ Backup créé : {filename}")

        # ==================================================
        # 🧠 NETTOYAGE INTELLIGENT
        # ==================================================

        print("STEP 6: listing backups")

        url = f"https://api.github.com/repos/{repo}/contents/backups"
        r = requests.get(url, headers=headers, timeout=5)

        if r.status_code != 200:
            print("⚠️ Impossible de lister les backups")
            return f"Backup OK → {backup_status}"

        files = r.json()
        print("STEP 7: files received =", len(files))

        db_files = [
            f for f in files
            if f["name"].startswith("films_") and f["name"].endswith(".db")
        ]

        print("STEP 8: db_files =", len(db_files))

        if len(db_files) <= 50:
            return f"Backup OK → {backup_status}"

        db_files_sorted = sorted(db_files, key=lambda x: x["name"], reverse=True)

        def extract_date(filename):
            try:
                date_str = filename.replace("films_", "").replace(".db", "")
                return datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            except Exception as e:
                print("❌ DATE ERROR:", filename, e)
                return datetime.min

        recent = []
        weekly = {}
        monthly = {}

        for f in db_files_sorted:

            try:
                date = extract_date(f["name"])
            except Exception as e:
                print("❌ LOOP DATE ERROR:", f["name"], e)
                continue

            if date == datetime.min:
                continue

            if len(recent) < 34:
                recent.append(f)
                continue

            week_key = date.strftime("%Y-%W")
            if week_key not in weekly and len(weekly) < 4:
                weekly[week_key] = f
                continue

            month_key = date.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = f
                continue

        keep = set()

        keep.update(f["name"] for f in recent)
        keep.update(f["name"] for f in weekly.values())
        keep.update(f["name"] for f in monthly.values())

        print("STEP 9: deleting old backups")

        count = 0  # 🔥 AJOUT

        for f in db_files_sorted:
            if f["name"] not in keep:
                
                if count >= 10:  # 🔥 LIMITE
                    break

                delete_data = {
                    "message": f"delete old backup {f['name']}",
                    "sha": f["sha"],
                    "branch": "main"
                }

                try:
                    requests.delete(f["url"], json=delete_data, headers=headers, timeout=5)
                    print("🗑️ OK:", f["name"])
                    count += 1  # 🔥 INCRÉMENT
                except Exception as e:
                    print("❌ DELETE ERROR:", f["name"], e)

        print("STEP FINAL: success")

        return f"Backup OK → {backup_status}"

    except Exception as e:
        print("❌ ERREUR BACKUP :", e)
        return "❌ Backup crash"

    finally:
        if os.path.exists(TMP_PATH):
            os.remove(TMP_PATH)
            
#----------nouvelle route---------

@app.route("/health")
def health():
    return "OK", 200
    
    
@app.before_request
def startup():
    if not hasattr(app, "initialized"):
        init_app()
        app.initialized = True
    
    
#---------Ajout Nanuel fiche vide------------------

@app.route("/manual_add", methods=["POST"])
def manual_add():

    title = request.form.get("title")
    emplacement = request.form.get("emplacement")
    type_disc = request.form.get("type")
    allocine = request.form.get("allocine")
    tmdb_input = request.form.get("tmdb_input", "").strip()

    # 🔥 nettoyage TMDB ID
    import re
    tmdb_id = ""

    if tmdb_input.isdigit():
        tmdb_id = tmdb_input
    elif "themoviedb.org" in tmdb_input:
        match = re.search(r"/movie/(\\d+)", tmdb_input)
        if match:
            tmdb_id = match.group(1)

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 🔥 génération disc_id automatique
    cursor.execute("SELECT MAX(id) FROM films")
    last_id = cursor.fetchone()[0] or 0
    next_id = last_id + 1
    disc_id = f"DISC-{next_id:05d}"

    # 🔥 INSERT COMPLET
    cursor.execute("""
        INSERT INTO films (disc_id, titre, emplacement, type, allocine, tmdb_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (disc_id, title, emplacement, type_disc, allocine, tmdb_id))

    conn.commit()
    conn.close()

    # 🔥 retour à la recherche
    return redirect(f"/?q={title}")
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
