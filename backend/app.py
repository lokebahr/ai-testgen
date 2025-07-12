from flask import Flask
from flask_cors import CORS
from ai.llm_utils import app

def create_app():
    app = Flask(__name__)
    CORS(app)
    return app

if __name__ == "__main__":
    app.run(debug=True)