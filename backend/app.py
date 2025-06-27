from flask import Flask
from flask_cors import CORS
from ai.endpoint import llm_blueprint

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(llm_blueprint)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)