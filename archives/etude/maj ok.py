import pandas as pd
import requests
import time

MAX_FILMS = 5
API_KEY = "0458b97834e41cd8c1e0f3364d6703d6"

df = pd.read_excel("films.xlsx", sheet_name="Feuil1")

# créer colonnes si elles n'existent pas
cols = ["TMDB_ID", "Jaquette", "Annee", "Genres", "Resume", "Casting"]
for col in cols:
    if col not in df.columns:
        df[col] = ""

def enrich_film(title):
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": API_KEY,
            "query": title,
            "language": "fr-FR"
        }
        r = requests.get(url, params=params).json()

        if not r.get("results"):
            return None

        film = r["results"][0]
        tmdb_id = str(film["id"])

        details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params_details = {
            "api_key": API_KEY,
            "language": "fr-FR",
            "append_to_response": "credits"
        }

        d = requests.get(details_url, params=params_details).json()

        year = str(d.get("release_date", "")[:4])
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


print("🔄 Enrichissement en cours...")

count = 0

for i in range(len(df)):

    titre = str(df.iloc[i, 5]) if not pd.isna(df.iloc[i, 5]) else ""

    if titre.strip() == "":
        continue

    if str(df.at[i, "TMDB_ID"]).strip() != "":
        continue

    if count >= MAX_FILMS:
        break

    print("🎬", titre)

    result = enrich_film(titre)

    if result:
        df.at[i, "TMDB_ID"] = result[0]
        df.at[i, "Jaquette"] = result[1]
        df.at[i, "Annee"] = result[2]
        df.at[i, "Genres"] = result[3]
        df.at[i, "Resume"] = result[4]
        df.at[i, "Casting"] = result[5]

        count += 1
        time.sleep(0.3)

print("✅", count, "films enrichis")

df.to_excel("films.xlsx", index=False)

print("📁 Fichier créé : films.xlsx")