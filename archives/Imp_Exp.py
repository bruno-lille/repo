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
        <a href="/deploy">🚀 Déployer sur Render</a>
    </div>
    
    <div style="margin:20px;">
        <a href="/push_data">🚀 Envoyer vers GitHub</a>
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
        if os.path.exists("films.xlsx"):
            z.write("films.xlsx", "films.xlsx")

        if os.path.exists("app.py"):
            z.write("app.py", "app.py")

        if os.path.exists("maj.py"):
            z.write("maj.py", "maj.py")

    # 🔥 5. envoi du fichier
    return send_file(backup_path, as_attachment=True)


    
    
    #------------IMPORT GITHUB---------
@app.route("/import_remote")
def import_remote():

    dossier_backup = "sauvegardes"

    if not os.path.exists(dossier_backup):
        os.makedirs(dossier_backup)

    backup_path = "Aucune sauvegarde"

    if os.path.exists("films.xlsx"):

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_avant_import_{now}.zip"

        backup_path = os.path.join(dossier_backup, backup_name)

        with zipfile.ZipFile(backup_path, 'w') as z:
            z.write("films.xlsx", "films.xlsx")

            if os.path.exists("app.py"):
                z.write("app.py", "app.py")

            if os.path.exists("maj.py"):
                z.write("maj.py", "maj.py")

    # 🔥 3. téléchargement GitHub
    url = "https://raw.githubusercontent.com/bruno-lille/repo/main/films.xlsx"

    r = requests.get(url)

    if r.status_code == 200:
        with open("films.xlsx", "wb") as f:
            f.write(r.content)

        return f"""
        <h2>✅ Import OK</h2>
        <p>📦 Sauvegarde créée :</p>
        <p>{backup_path}</p>
        <a href='/'>Retour</a>
        """

    return "<h2>❌ Erreur téléchargement</h2><a href='/'>Retour</a>"

#-----------Exporter la Solution-------------

@app.route("/deploy")
def deploy():

    import subprocess

    try:
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True, text=True
        )

        result = subprocess.run(
            ["git", "commit", "-m", "update"],
            capture_output=True, text=True
        )

        result = subprocess.run(
            ["git", "push"],
            capture_output=True, text=True
        )

        return f"""
        <h2>🚀 Déploiement OK</h2>
        <pre>{result.stdout}</pre>
        <a href='/'>Retour</a>
        """

    except Exception as e:
        return f"<h2>❌ Erreur</h2><pre>{e}</pre><a href='/'>Retour</a>"
        
        
#------------Export vers GITHUB---------
@app.route("/push_data")
def push_data():

    import subprocess
    import shutil

    git = shutil.which("git")

    if not git:
        return "<h2>❌ Git non trouvé</h2><a href='/'>Retour</a>"

    try:
        # 🔥 ajouter fichiers
        subprocess.run([git, "add", "films.xlsx"])
        subprocess.run([git, "add", "app.py"])

        # 🔥 commit
        subprocess.run([git, "commit", "-m", "update app + data"])

        # 🔥 push
        result = subprocess.run([git, "push"], capture_output=True, text=True)

        return f"""
        <h2>🚀 Push GitHub OK</h2>
        <pre>{result.stdout}</pre>
        <a href='/'>Retour</a>
        """

    except Exception as e:
        return f"<h2>❌ Erreur</h2><pre>{e}</pre><a href='/'>Retour</a>"


if __name__ == "__main__":
    app.run(port=5001)