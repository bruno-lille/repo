import sqlite3

conn = sqlite3.connect("films.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disc_id TEXT,
    emplacement TEXT,
    type TEXT,
    titre TEXT,
    allocine TEXT,
    tmdb_id TEXT,
    jaquette TEXT,
    annee TEXT,
    genres TEXT,
    resume TEXT,
    casting TEXT,
    ordre INTEGER
)
""")

conn.commit()
conn.close()

print("✅ Base créée")