from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow_enum import EnumField
from db.models import TestStatus

class ProjectSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    git_repo = fields.Str(allow_none=True)
    branch = fields.Str(allow_none=True)
    mode = fields.Str(required=True, validate=lambda x: x in ['single', 'git'])
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    files = fields.List(fields.Nested('FileSchema', exclude=['project_id']), dump_only=True)

    @validates_schema
    def validate_git_repo(self, data, **kwargs):
        if data.get('mode') == 'git' and not data.get('git_repo'):
            raise ValidationError('git_repo is required when mode is git')

class FileSchema(Schema):
    id = fields.Int(dump_only=True)
    project_id = fields.Str(required=True)
    path = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    title = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    file_content = fields.Str(allow_none=True)
    test_status = EnumField(TestStatus, by_value=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProjectCreateSchema(Schema):
    title = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    git_repo = fields.Str(allow_none=True)
    branch = fields.Str(allow_none=True, load_default=None)
    mode = fields.Str(required=True, validate=lambda x: x in ['single', 'git'])
    file_content = fields.Str(allow_none=True)  # For single file mode
    filename = fields.Str(allow_none=True, load_default='main.py')  # For single file mode

    @validates_schema
    def validate_mode_requirements(self, data, **kwargs):
        if data.get('mode') == 'git':
            if not data.get('git_repo'):
                raise ValidationError('git_repo is required when mode is git')
        elif data.get('mode') == 'single':
            if not data.get('file_content'):
                raise ValidationError('file_content is required when mode is single')

class FileUpdateSchema(Schema):
    test_status = EnumField(TestStatus, by_value=True)
    file_content = fields.Str(allow_none=True)
