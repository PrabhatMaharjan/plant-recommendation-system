"""
run.py - Flask Application Entry Point
Database Manager: Prabhat Maharjan (0371462)
Group 13 - Indoor Plant Recommendation System

Local:  python run.py
Render: gunicorn run:app  (handled automatically by Procfile)
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
