# -*- coding: utf-8 -*-
from flask import Flask, request, send_file
import zipfile
import datetime
import os

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
        <form action="/import_excel" method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <button>📥 Import films.xlsx</button>
        </form>
    </div>

    <div style="margin:20px;">
        <a href="/deploy">🚀 Déployer sur Render</a>
    </div>
    """


# ----------- EXPORT ZIP -----------
@app.route("/export_zip")
def export_zip():

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_name = f"backup_{now}.zip"

    with zipfile.ZipFile(zip_name, 'w') as z:
        if os.path.exists("films.xlsx"):
            z.write("films.xlsx")
        if os.path.exists("app.py"):
            z.write("app.py")

    return send_file(zip_name, as_attachment=True)


# ----------- IMPORT EXCEL -----------
@app.route("/import_excel", methods=["POST"])
def import_excel():

    file = request.files.get("file")

    if not file:
        return "❌ Aucun fichier"

    file.save("films.xlsx")

    return "<h2>✅ Import réussi</h2><a href='/'>Retour</a>"


# ----------- DEPLOY GITHUB -----------
@app.route("/deploy")
def deploy():

    os.system("git add .")
    os.system('git commit -m "auto deploy" || echo "no change"')
    os.system("git push")

    return "<h2>🚀 Déploiement lancé !</h2><a href='/'>Retour</a>"


if __name__ == "__main__":
    app.run(port=5001)