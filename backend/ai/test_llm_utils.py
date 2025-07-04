import pytest
import openai
from unittest.mock import patch, Mock
from dotenv import load_dotenv
from openai.error import OpenAIError, RateLimitError, Timeout
from llm_utils import _call_with_retries, generate_test_plan, generate_tests

def test_call_with_retries_success():
    mock_payload = {'mock_key': 'mock_value'}
    mock_api_response = {'response': 'mock_response'}

    with patch('openai.ChatCompletion.create', return_value=mock_api_response) as mock_create:
        response = _call_with_retries(mock_payload)
        mock_create.assert_called_once_with(**mock_payload)
        assert response == mock_api_response

def test_retries_on_rate_limit_error():
    mock_payload = {'mock_key': 'mock_value'}

    with patch('openai.ChatCompletion.create', side_effect=[RateLimitError, Mock()]) as mock_create:
        _call_with_retries(mock_payload, max_retries=2)
        assert mock_create.call_count == 2

def test_retries_on_timeout():
    mock_payload = {'mock_key': 'mock_value'}
    
    with patch('openai.ChatCompletion.create', side_effect=[Timeout, Mock()]) as mock_create:
        _call_with_retries(mock_payload, max_retries=2)
        assert mock_create.call_count == 2

def test_rate_limit_error_exceeding_max_retries():
    mock_payload = {'mock_key': 'mock_value'}
    
    with patch('openai.ChatCompletion.create', side_effect=RateLimitError):
        with pytest.raises(RateLimitError):
            _call_with_retries(mock_payload, max_retries=2)

def test_timeout_exceeding_max_retries():
    mock_payload = {'mock_key': 'mock_value'}
    
    with patch('openai.ChatCompletion.create', side_effect=Timeout):
        with pytest.raises(Timeout):
            _call_with_retries(mock_payload, max_retries=2)

def test_openaierror_in_call_with_retries():
    mock_payload = {'mock_key': 'mock_value'}
    
    with patch('openai.ChatCompletion.create', side_effect=OpenAIError) as mock_create:
        with pytest.raises(RuntimeError):
            _call_with_retries(mock_payload)

def test_generate_test_plan_uses_o4_mini_model():
    mock_payload = {'mock_key': 'mock_value'}
    mock_code = "def mock_code(): pass"
    mock_language = "Python"
    mock_framework = "pytest"

    with patch('llm_utils._call_with_retries') as mock_call_with_retries:
        generate_test_plan(mock_code, mock_language, mock_framework)
        supplied_payload = mock_call_with_retries.call_args[0][0]
        assert supplied_payload['model'] == 'o4-mini'

def test_generate_tests_uses_gpt_4_model():
    mock_payload = {'mock_key': 'mock_value'}
    mock_code = "def mock_code(): pass"
    mock_test_plan = ["Test 1", "Test 2", "Test 3"]
    mock_filename = "test_file.py"

    with patch('llm_utils._call_with_retries') as mock_call_with_retries:
        generate_tests(mock_code, mock_test_plan, mock_filename)
        supplied_payload = mock_call_with_retries.call_args[0][0]
        assert supplied_payload['model'] == 'gpt-4'