import pandas as pd
import requests
import time
import re
import unicodedata
from rapidfuzz import fuzz

# ---------------- CONFIG ----------------
MAX_FILMS = 20
API_KEY = "0458b97834e41cd8c1e0f3364d6703d6"

df = pd.read_excel("films.xlsx", sheet_name="Feuil1")

cols = ["TMDB_ID", "Jaquette", "Annee", "Genres", "Resume", "Casting"]
for col in cols:
    if col not in df.columns:
        df[col] = ""

# 🔥 force tout en string (important)
df = df.astype(str)

# ---------------- OUTILS ----------------

def is_empty(val):
    return str(val).strip() == "" or str(val).lower() == "nan"

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

# ---------------- ENRICHISSEMENT PAR TITRE ----------------

def enrich_film(title):
    try:
        title_clean = clean_title(title)
        title_norm = normalize(title_clean)

        results = []

        for lang in ["fr-FR", "en-US"]:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": API_KEY,
                "query": title_clean,
                "language": lang
            }

            data = safe_request(url, params)

            if data.get("results"):
                results += data["results"][:5]

        if not results:
            return None

        best_film = None
        best_score = 0

        for f in results:
            candidate = normalize(f.get("title", ""))
            score = fuzz.token_set_ratio(title_norm, candidate)

            # bonus année
            year_excel = re.search(r"\d{4}", title)
            if year_excel and f.get("release_date"):
                if year_excel.group() in f["release_date"]:
                    score += 10

            if score > best_score:
                best_score = score
                best_film = f

        if best_score < 70:
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

    titre = str(df.iloc[i, 5]) if not pd.isna(df.iloc[i, 5]) else ""

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

    # -------- CAS 1 : ID EXISTE --------
    if current_id != "" and needs_update:

        print(f"[ID] {titre}")

        result = enrich_from_id(current_id)

        if result:
            if jaquette_empty:
                df.at[i, "Jaquette"] = result[1]
            if annee_empty:
                df.at[i, "Annee"] = result[2]
            if genres_empty:
                df.at[i, "Genres"] = result[3]
            if resume_empty:
                df.at[i, "Resume"] = result[4]
            if casting_empty:
                df.at[i, "Casting"] = result[5]

            count += 1
            time.sleep(0.2)

        continue

    # -------- CAS 2 : PAS D’ID --------
    if current_id == "":

        if count >= MAX_FILMS:
            break

        print(f"[SEARCH] {titre}")

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

df.to_excel("films.xlsx", index=False, sheet_name="Feuil1")

print("📁 Fichier mis à jour : films.xlsx")