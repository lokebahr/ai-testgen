from db import db
from datetime import datetime
from enum import Enum
import uuid
import hashlib

class TestStatus(Enum):
    UNTESTED = "untested"
    COMPLETED = "completed"
    FAILED = "failed"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    git_repo = db.Column(db.String(500), nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    mode = db.Column(db.String(20), nullable=False, default='single')  # 'single' or 'git'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to files
    files = db.relationship('File', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'git_repo': self.git_repo,
            'branch': self.branch,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'files': [file.to_dict() for file in self.files]
        }

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_content = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash of file content
    test_status = db.Column(db.Enum(TestStatus), default=TestStatus.UNTESTED, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for path within a project
    __table_args__ = (db.UniqueConstraint('project_id', 'path', name='unique_project_file_path'),)
    
    def calculate_content_hash(self):
        """Calculate SHA-256 hash of file content"""
        if self.file_content is None:
            return None
        return hashlib.sha256(self.file_content.encode('utf-8')).hexdigest()
    
    def update_content(self, new_content):
        """Update file content and recalculate hash"""
        self.file_content = new_content
        self.content_hash = self.calculate_content_hash()
    
    def content_changed(self, new_content):
        """Check if the new content is different from current content"""
        new_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest() if new_content else None
        return self.content_hash != new_hash
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'path': self.path,
            'title': self.title,
            'file_content': self.file_content,
            'content_hash': self.content_hash,
            'test_status': self.test_status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_status_color(self):
        """Return color class for the test status"""
        status_colors = {
            TestStatus.COMPLETED: 'text-green-600 bg-green-50',
            TestStatus.FAILED: 'text-red-600 bg-red-50',
            TestStatus.UNTESTED: 'text-yellow-600 bg-yellow-50'
        }
        return status_colors.get(self.test_status, 'text-gray-600 bg-gray-50')
