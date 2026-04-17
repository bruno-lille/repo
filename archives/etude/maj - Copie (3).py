import pandas as pd
import requests
import time
import re
import unicodedata
from rapidfuzz import fuzz
import tkinter as tk
from tkinter import simpledialog

#-----------nombre de film----------

def demander_nombre_films():
    root = tk.Tk()
    root.withdraw()  # cache la fenêtre principale

    nb = simpledialog.askinteger(
        "Traitement films",
        "Combien de films traiter ?",
        minvalue=1,
        maxvalue=1000
    )

    root.destroy()

    # valeur par défaut si annulation
    if nb is None:
        return 50

    return nb



# ---------------- CONFIG ----------------
MAX_FILMS = demander_nombre_films()
API_KEY = "0458b97834e41cd8c1e0f3364d6703d6"

df = pd.read_excel("films.xlsx", sheet_name="Sheet1")

cols = ["TMDB_ID", "Jaquette", "Annee", "Genres", "Resume", "Casting"]
for col in cols:
    if col not in df.columns:
        df[col] = ""

df = df.astype(str)
for col in ["Jaquette", "Annee", "Genres", "Resume", "Casting"]:
    df[col] = df[col].replace(["nan", "None"], "").fillna("")


# ---------------- OUTILS ----------------

def is_empty(val):
    if val is None:
        return True

    val = str(val).strip().lower()

    return val in ["", "nan", "none"]

def safe_str(val):
    if val is None:
        return ""
    if str(val).lower() == "nan":
        return ""
    return str(val)

def clean_id(val):
    if pd.isna(val):
        return ""
    val = str(val).strip()
    if val.endswith(".0"):
        val = val[:-2]
    return val

def clean_title(title):
    title = str(title)
    title = re.sub(r"\(\d{4}\)", "", title)
    title = re.sub(r"bluray|dvd|4k|uhd", "", title, flags=re.I)
    title = re.sub(r"[^a-zA-Z0-9 ]", " ", title)
    return title.strip()

def normalize(text):
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text

def is_valid_title(title):
    title = title.strip()
    if len(title) < 2:
        return False
    if title.isdigit():
        return False
    return True

# ---------------- API SAFE ----------------

def safe_request(url, params, retries=3):
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, timeout=5)
            return r.json()
        except:
            time.sleep(1)
    return {}

# ---------------- ENRICHISSEMENT PAR ID ----------------

def enrich_from_id(tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params = {
            "api_key": API_KEY,
            "language": "fr-FR",
            "append_to_response": "credits"
        }

        d = safe_request(url, params)

        year = safe_str(d.get("release_date", "")[:4])
        genres = ", ".join([g["name"] for g in d.get("genres", [])])

        poster = ""
        if d.get("poster_path"):
            poster = f"https://image.tmdb.org/t/p/w300{d['poster_path']}"

        overview = d.get("overview", "")
        cast_list = d.get("credits", {}).get("cast", [])
        cast = ", ".join([a["name"] for a in cast_list[:5]])

        return [
            safe_str(tmdb_id),
            safe_str(poster),
            safe_str(year),
            safe_str(genres),
            safe_str(overview),
            safe_str(cast)
        ]

    except:
        return None

# ---------------- RECHERCHE INTELLIGENTE ----------------

def build_variants(title):
    t = clean_title(title)

    variants = [
        t,
        normalize(t),
        t.replace(" ", ""),
        t.split(":")[0],
        t.split("-")[0],
    ]

    # enlever doublons
    return list(set([v.strip() for v in variants if v.strip()]))


def enrich_film(title):
    try:
        title_norm = normalize(title)
        variants = build_variants(title)

        results = []

        for variant in variants:
            for lang in ["fr-FR", "en-US"]:
                url = "https://api.themoviedb.org/3/search/movie"
                params = {
                    "api_key": API_KEY,
                    "query": variant,
                    "language": lang
                }

                data = safe_request(url, params)

                if data.get("results"):
                    results += data["results"][:5]

            if results:
                break

        if not results:
            print(f"[NO RESULT] {title}")
            return None

        best_film = None
        best_score = 0

        for f in results:
            candidate = normalize(f.get("title", ""))
            score = fuzz.token_set_ratio(title_norm, candidate)

            year_excel = re.search(r"\d{4}", title)
            if year_excel and f.get("release_date"):
                if year_excel.group() in f["release_date"]:
                    score += 10

            if score > best_score:
                best_score = score
                best_film = f

        if best_score < 65:
            print(f"[SKIP] {title} → score {best_score}")
            return None

        return enrich_from_id(best_film["id"])

    except Exception as e:
        print("Erreur :", title, e)
        return None

# ---------------- MAIN ----------------

print("Enrichissement en cours...\n")

count = 0

for i in range(len(df)):

    titre = str(df.iloc[i, 5])

    if not is_valid_title(titre):
        continue

    current_id = clean_id(df.at[i, "TMDB_ID"])
    df.at[i, "TMDB_ID"] = current_id

    jaquette_empty = is_empty(df.at[i, "Jaquette"])
    annee_empty = is_empty(df.at[i, "Annee"])
    genres_empty = is_empty(df.at[i, "Genres"])
    resume_empty = is_empty(df.at[i, "Resume"])
    casting_empty = is_empty(df.at[i, "Casting"])

    needs_update = any([
        jaquette_empty,
        annee_empty,
        genres_empty,
        resume_empty,
        casting_empty
    ])
    if current_id != "":
        print(f"[CHECK] {titre} → update={needs_update}")

    # -------- CAS ID --------
    if current_id != "" and needs_update:
        print(f"[{i}/{len(df)}] [ID] {titre}")

        result = enrich_from_id(current_id)

        if result:
            if jaquette_empty: df.at[i, "Jaquette"] = result[1]
            if annee_empty: df.at[i, "Annee"] = str(result[2]).replace(".0", "")
            if genres_empty: df.at[i, "Genres"] = result[3]
            if resume_empty: df.at[i, "Resume"] = result[4]
            if casting_empty: df.at[i, "Casting"] = result[5]

            count += 1
            time.sleep(0.2)

        continue

    # -------- CAS SEARCH --------
    if current_id == "":
        if count >= MAX_FILMS:
            print("\n🛑 Limite atteinte")
            break

        print(f"[{i}/{len(df)}] [SEARCH] {titre}")

        result = enrich_film(titre)

        if result:
            df.at[i, "TMDB_ID"] = result[0]
            df.at[i, "Jaquette"] = result[1]
            df.at[i, "Annee"] = result[2]
            df.at[i, "Genres"] = result[3]
            df.at[i, "Resume"] = result[4]
            df.at[i, "Casting"] = result[5]

            count += 1
            time.sleep(0.25)

print(f"\n✅ {count} films traités")

df.to_excel("films.xlsx", index=False)

print("📁 Fichier mis à jour : films.xlsx")