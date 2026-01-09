#!/usr/bin/env python3
"""
Simple test script to verify the database setup and basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app
from db import db

def test_database_setup():
    """Test that the database can be created and basic operations work"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test importing models
            from db.models import Project, File, TestStatus
            print("✓ Models imported successfully")
            
            # Test creating a simple project
            project = Project(
                title="Test Project",
                mode="single",
                git_repo=None,
                branch=None
            )
            db.session.add(project)
            db.session.commit()
            print("✓ Test project created successfully")
            
            # Test creating a file
            file = File(
                project_id=project.id,
                path="test.py",
                title="test.py",
                file_content="print('hello world')",
                test_status=TestStatus.UNTESTED
            )
            db.session.add(file)
            db.session.commit()
            print("✓ Test file created successfully")
            
            # Test querying
            projects = Project.query.all()
            files = File.query.all()
            print(f"✓ Found {len(projects)} projects and {len(files)} files")
            
            # Test project serialization
            project_dict = project.to_dict()
            print(f"✓ Project serialization works: {project_dict['title']}")
            
            # Clean up
            db.session.delete(file)
            db.session.delete(project)
            db.session.commit()
            print("✓ Cleanup successful")
            
            print("\n🎉 All database tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
