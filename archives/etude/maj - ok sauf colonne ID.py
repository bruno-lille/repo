import pandas as pd
import requests
import time
import re
import unicodedata
from rapidfuzz import fuzz

MAX_FILMS = 20
API_KEY = "0458b97834e41cd8c1e0f3364d6703d6"

df = pd.read_excel("films.xlsx", sheet_name="Feuil1")

cols = ["TMDB_ID", "Jaquette", "Annee", "Genres", "Resume", "Casting"]
for col in cols:
    if col not in df.columns:
        df[col] = ""
    df[col] = df[col].astype(str)

def clean_title(title):
    title = str(title)
    title = re.sub(r"\(.*?\)", "", title)
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

def clean_id(val):
    if pd.isna(val):
        return ""
    val = str(val).strip()
    if val.endswith(".0"):
        val = val[:-2]
    return val

def enrich_film(title):
    try:
        title_clean = clean_title(title)

        results = []

        for lang in ["fr-FR", "en-US"]:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": API_KEY,
                "query": title_clean,
                "language": lang
            }
            r = requests.get(url, params=params).json()
            if r.get("results"):
                results += r["results"][:5]

        if not results:
            return None

        best_film = None
        best_score = 0
        title_norm = normalize(title_clean)

        for f in results:
            candidate = normalize(f.get("title", ""))
            score = fuzz.partial_ratio(title_norm, candidate)
            if score > best_score:
                best_score = score
                best_film = f

        if best_score < 55:
            return None

        film = best_film
        tmdb_id = str(film["id"])

        details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params_details = {
            "api_key": API_KEY,
            "language": "fr-FR",
            "append_to_response": "credits"
        }

        d = requests.get(details_url, params=params_details).json()

        year_raw = d.get("release_date", "")
        year = year_raw[:4] if year_raw else ""

        genres = ", ".join([g["name"] for g in d.get("genres", [])])

        poster = ""
        if d.get("poster_path"):
            poster = f"https://image.tmdb.org/t/p/w300{d['poster_path']}"

        overview = d.get("overview", "")

        cast_list = d.get("credits", {}).get("cast", [])
        cast = ", ".join([actor["name"] for actor in cast_list[:5]])

        return [tmdb_id, poster, year, genres, overview, cast]

    except Exception as e:
        print("Erreur :", title, e)
        return None


print("Enrichissement en cours...")

count = 0

for i in range(len(df)):

    titre = str(df.iloc[i, 5]) if not pd.isna(df.iloc[i, 5]) else ""

    if not is_valid_title(titre):
        continue

    current_id = clean_id(df.at[i, "TMDB_ID"])
    df.at[i, "TMDB_ID"] = current_id

    if current_id != "":
        continue

    if count >= MAX_FILMS:
        break

    print("Film :", titre)

    result = enrich_film(titre)

    if result:
        df.at[i, "TMDB_ID"] = result[0]
        df.at[i, "Jaquette"] = result[1]
        df.at[i, "Annee"] = str(result[2]).replace(".0", "")
        df.at[i, "Genres"] = result[3]
        df.at[i, "Resume"] = result[4]
        df.at[i, "Casting"] = result[5]

        count += 1
        time.sleep(0.25)

print(count, "films enrichis")

df.to_excel("films.xlsx", index=False, sheet_name="Feuil1")

print("Fichier mis à jour : films.xlsx")