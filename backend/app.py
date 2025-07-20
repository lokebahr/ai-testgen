from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv


load_dotenv()

from ai.test_platform import test_platform

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register the new test platform blueprint
    app.register_blueprint(test_platform, url_prefix='/api')
    
    # Register legacy endpoints directly to maintain backward compatibility
    from ai.llm_utils import app as legacy_routes
    for rule in legacy_routes.url_map.iter_rules():
        if rule.endpoint != 'static':
            app.add_url_rule(
                f'/legacy{rule.rule}',
                endpoint=f'legacy_{rule.endpoint}',
                view_func=legacy_routes.view_functions[rule.endpoint],
                methods=rule.methods
            )
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)