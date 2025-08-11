#!/usr/bin/env python3
"""
Migration script to add content_hash column to files table and populate it for existing files.
This should be run once after updating the File model to include content_hash.
"""

import os
import sys
import hashlib

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import create_app
from db import db
from db.models import File
from sqlalchemy import text

def migrate_content_hash():
    """Add content_hash column and populate for existing files"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if content_hash column exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('files')]
            
            if 'content_hash' not in columns:
                print("Adding content_hash column to files table...")
                # Add the content_hash column using raw SQL
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE files ADD COLUMN content_hash VARCHAR(64)'))
                    conn.commit()
                print("Column added successfully.")
            else:
                print("content_hash column already exists.")
            
            # Get all files that don't have a content hash
            files_without_hash = File.query.filter(
                db.or_(File.content_hash.is_(None), File.content_hash == '')
            ).all()
            
            print(f"Found {len(files_without_hash)} files without content hash.")
            
            # Calculate and update content hash for each file
            updated_count = 0
            for file in files_without_hash:
                if file.file_content:
                    file.content_hash = hashlib.sha256(file.file_content.encode('utf-8')).hexdigest()
                    updated_count += 1
                else:
                    file.content_hash = None
            
            # Commit the changes
            db.session.commit()
            
            print(f"Successfully updated content hash for {updated_count} files.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    success = migrate_content_hash()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
