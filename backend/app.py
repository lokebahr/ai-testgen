from flask import Flask, request, jsonify
from flask_cors import CORS
from llm_utils import generate_test_ideas

app = Flask(__name__)
CORS(app) #this is to connect fronten

@app.route("/generate-ideas", methods =["POST"])
def generate_ideas():
    data = request.get_json()
    code = data.get("code", "")
    language = data.get("language", "python")
    framework = data.get("framework", "pytest")

    if not code:
        return jsonify({"error": "kod måste skicaks in"}), 400

    test_ideas = generate_test_ideas(code, language, framework)
    return jsonify({"test_ideas": test_ideas})

if __name__ == "__main__":
    app.run(debug=True)