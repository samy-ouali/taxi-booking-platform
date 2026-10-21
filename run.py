"""
Point d'entrée de l'application Flask.
Lancement :
    python run.py
    # ou
    flask --app run run --debug
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
