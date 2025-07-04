import pytest
from unittest.mock import patch, Mock

from flask import json
from endpoint import llm_blueprint

from pytest import fixture
@pytest.fixture
def client():
    llm_blueprint.config['TESTING'] = True
    with llm_blueprint.test_client() as client:
        yield client

def test_get_test_plan(client):
    response = client.post('/api/testplan', json={'code': 'print("hello")'})
    assert response.status_code == 200
    assert 'plan' in json.loads(response.data.decode())

def test_get_test_plan_with_custom_language_framework(client):
    response = client.post('/api/testplan', json={'code': 'console.log("hello")', 'language': 'javascript', 'framework': 'jest'})
    assert response.status_code == 200
    assert 'plan' in json.loads(response.data.decode())

def test_get_test_plan_without_code(client):
    response = client.post('/api/testplan', json={})
    assert response.status_code == 400
    assert 'error' in json.loads(response.data.decode())

@patch('endpoint.generate_test_plan', side_effect=Exception('Test plan generation error'))
def test_get_test_plan_exception(mock_gen_test_plan, client):
    response = client.post('/api/testplan', json={'code': 'print("hello")'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data.decode())

def test_create_tests(client):
    response = client.post('/api/test_creation', json={'code': 'print("hello")', 'testPlan': 'Test Plan', 'filename': 'test.py'})
    assert response.status_code == 200
    assert 'tests' in json.loads(response.data.decode())

def test_create_tests_without_code(client):
    response = client.post('/api/test_creation', json={'testPlan': 'Test Plan', 'filename': 'test.py'})
    assert response.status_code == 400
    assert 'error' in json.loads(response.data.decode())

def test_create_tests_without_test_plan(client):
    response = client.post('/api/test_creation', json={'code': 'print("hello")', 'filename': 'test.py'})
    assert response.status_code == 400
    assert 'error' in json.loads(response.data.decode())

def test_create_tests_without_filename(client):
    response = client.post('/api/test_creation', json={'code': 'print("hello")', 'testPlan': 'Test Plan'})
    assert response.status_code == 400
    assert 'error' in json.loads(response.data.decode())

@patch('endpoint.generate_tests', side_effect=Exception('Test creation error'))
def test_create_tests_exception(mock_gen_tests, client):
    response = client.post('/api/test_creation', json={'code': 'print("hello")', 'testPlan': 'Test Plan', 'filename': 'test.py'})
    assert response.status_code == 500
    assert 'error' in json.loads(response.data.decode())