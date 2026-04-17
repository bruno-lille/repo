# -*- coding: utf-8 -*-
from flask import Flask, request, send_file
import zipfile
import datetime
import os
import requests




app = Flask(__name__)

# ----------- PAGE ACCUEIL ADMIN -----------
@app.route("/")
def home():
    return """
    <h1>🛠️ Admin sauvegarde / déploiement</h1>

    <div style="margin:20px;">
        <a href="/export_zip">💾 Sauvegarde complète (ZIP)</a>
    </div>

    
    <div style="margin:20px;">
        <a href="/import_remote">🌐 Import depuis GitHub</a>
    </div>
    
    
    
    <div style="margin:20px;">
        <a href="/push_data">🚀 Déployer Appli</a>
    </div>
    
    """
    


# ----------- EXPORT ZIP -----------
@app.route("/export_zip")
def export_zip():

    dossier_backup = "sauvegardes"

    # 🔥 1. créer dossier si inexistant
    if not os.path.exists(dossier_backup):
        os.makedirs(dossier_backup)

    # 🔥 2. nom du fichier (TOUJOURS en dehors du if)
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"backup_{now}.zip"

    # 🔥 3. chemin complet
    backup_path = os.path.join(dossier_backup, zip_name)

    # 🔥 4. création du zip
    with zipfile.ZipFile(backup_path, 'w') as z:
        if os.path.exists("films.db"):
            z.write("films.db", "films.db")

        if os.path.exists("app.py"):
            z.write("app.py", "app.py")
            
        if os.path.exists("requirements.txt"):
            z.write("requirements.txt", "requirements.txt")

        if os.path.exists("maj.py"):
            z.write("maj.py", "maj.py")

    # 🔥 5. envoi du fichier
    return send_file(backup_path, as_attachment=True)


    
    
#------------IMPORT GITHUB AUTO DERNIER BACKUP---------
@app.route("/import_remote")
def import_remote():

 

    dossier_backup = "sauvegardes"

    if not os.path.exists(dossier_backup):
        os.makedirs(dossier_backup)

    backup_path = "Aucune sauvegarde"

    # 🔥 sauvegarde AVANT import
    if os.path.exists("films.db"):

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_avant_import_{now}.zip"

        backup_path = os.path.join(dossier_backup, backup_name)

        with zipfile.ZipFile(backup_path, 'w') as z:
            z.write("films.db", "films.db")

    # 🔐 CONFIG GITHUB
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")

    if not token or not repo:
        return "<h2>❌ Token ou repo manquant</h2>"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 🔥 1. LISTER LES FICHIERS DANS /backups
    url_list = f"https://api.github.com/repos/{repo}/contents/backups"

    r = requests.get(url_list, headers=headers)

    if r.status_code != 200:
        return f"<h2>❌ Erreur listing backups ({r.status_code})</h2>"

    files = r.json()

    # 🔍 filtrer uniquement les .db
    db_files = [f for f in files if f["name"].endswith(".db")]

    if not db_files:
        return "<h2>❌ Aucun fichier .db trouvé</h2>"

    # 🔥 2. PRENDRE LE PLUS RÉCENT
    latest_file = sorted(db_files, key=lambda x: x["name"], reverse=True)[0]

    path = latest_file["path"]

    # 🔥 3. TÉLÉCHARGER LE FICHIER (version fiable)
    print("FICHIER TROUVÉ:", latest_file)
    download_url = latest_file.get("download_url")

    if not download_url:
        return "<h2>❌ download_url introuvable</h2>"

    r = requests.get(download_url, headers=headers)

    if r.status_code != 200:
        return f"<h2>❌ Erreur téléchargement ({r.status_code})</h2>"

    with open("films.db", "wb") as f:
        f.write(r.content)
        
    chemin_db = os.path.abspath("films.db")
    chemin_backup = os.path.abspath(backup_path) if backup_path != "Aucune sauvegarde" else "Aucune sauvegarde"

    return f"""
    <h2>✅ Import DB OK</h2>

    <p>📦 Backup avant import :</p>
    <p>{chemin_backup}</p>

    <p>📁 Nouveau fichier :</p>
    <p>{chemin_db}</p>

    <p>🔄 Le fichier <b>films.db</b> a remplacé l'ancien dans ton projet <b>DVD Bluray</b></p>

    <p>📥 Source :</p>
    <p>{path}</p>

    <a href='/'>Retour</a>
    """


        
        
#------------Export vers GITHUB---------
@app.route("/push_data")
def push_data():

    import os
    import base64
    import requests

    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")

    if not token or not repo:
        return "<h2>❌ Variables GITHUB_TOKEN ou GITHUB_REPO manquantes</h2>"

    headers = {
        "Authorization": f"token {token}"
    }

    # 👉 fichier à pousser (modifiable via URL)
    file_param = request.args.get("file")

    if file_param:
        files_to_push = [file_param]
    else:
        files_to_push = ["app.py", "films.db", "requirements.txt"]

    result_log = ""

    for file in files_to_push:

        if not os.path.exists(file):
            result_log += f"❌ {file} introuvable<br>"
            continue

        try:
            with open(file, "rb") as f:
                content = base64.b64encode(f.read()).decode()

            url = f"https://api.github.com/repos/{repo}/contents/{file}"

            # 🔍 vérifier si fichier existe déjà
            r = requests.get(url, headers=headers)

            sha = None
            if r.status_code == 200:
                sha = r.json()["sha"]

            data = {
                "message": f"update {file}",
                "content": content,
                "branch": "main"
            }

            if sha:
                data["sha"] = sha

            r = requests.put(url, json=data, headers=headers)

            if r.status_code in [200, 201]:
                result_log += f"✅ {file} envoyé<br>"
            else:
                result_log += f"❌ {file} erreur {r.status_code}<br>"

        except Exception as e:
            result_log += f"❌ {file} erreur {str(e)}<br>"

    return f"""
    <h2>🚀 Push GitHub</h2>
    <p>{result_log}</p>
    <a href='/'>Retour</a>
    """


if __name__ == "__main__":
    app.run(port=5001)