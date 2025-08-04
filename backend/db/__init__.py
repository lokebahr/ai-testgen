from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testgen.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    return db
