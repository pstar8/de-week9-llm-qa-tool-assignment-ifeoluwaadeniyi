import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from smart_qa.client import LLMClient, file_cache, retry_on_failure
from smart_qa.custom_exceptions import LLMAPIError


class TestLLMClientInit:
    def test_init_success(self, mock_genai):
        mock_genai_module, mock_model = mock_genai
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            assert client.model == mock_model
            mock_genai_module.configure.assert_called_once_with(api_key='test-key')
    
    def test_init_missing_api_key(self, mock_genai):
        with patch.dict('os.environ', clear=True):
            with patch('smart_qa.client.load_dotenv'):
                with pytest.raises(LLMAPIError, match="GOOGLE_API_KEY not found"):
                    LLMClient()


class TestSummarize:
    def test_summarize_success(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.summarize(sample_text)
            
            assert result == "This is a mock response from the API."
            mock_model.generate_content.assert_called_once()
    
    def test_summarize_caching(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result1 = client.summarize(sample_text)
            result2 = client.summarize(sample_text)
            
            assert result1 == result2
            assert mock_model.generate_content.call_count == 1
    
    def test_summarize_api_failure(self, mock_genai, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.side_effect = Exception("API Error")
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            with pytest.raises(LLMAPIError, match="API call failed after 3 attempts"):
                client.summarize(sample_text)


class TestAsk:
    def test_ask_success(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.ask(sample_text, "Who created Python?")
            
            assert result == "This is a mock response from the API."
            mock_model.generate_content.assert_called_once()
    
    def test_ask_caching(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result1 = client.ask(sample_text, "Who created Python?")
            result2 = client.ask(sample_text, "Who created Python?")
            
            assert result1 == result2
            assert mock_model.generate_content.call_count == 1
    
    def test_ask_different_questions_no_cache(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            client.ask(sample_text, "Who created Python?")
            client.ask(sample_text, "When was Python created?")
            
            assert mock_model.generate_content.call_count == 2


class TestExtractEntities:
    def test_extract_entities_success(self, mock_genai, mock_json_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_json_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.extract_entities(sample_text)
            
            assert isinstance(result, dict)
            assert "People" in result
            assert "Dates" in result
            assert "Locations" in result
            assert result["People"] == ["Guido van Rossum"]
    
    def test_extract_entities_strips_markdown(self, mock_genai, mock_json_response_with_markdown, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_json_response_with_markdown
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.extract_entities(sample_text)
            
            assert isinstance(result, dict)
            assert result["People"] == ["John Doe"]
            assert result["Dates"] == ["2024"]
    
    def test_extract_entities_invalid_json(self, mock_genai, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content.return_value = mock_response
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            with pytest.raises(LLMAPIError, match="Failed to parse JSON"):
                client.extract_entities(sample_text)


class TestCaching:
    def test_cache_file_created(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.return_value = mock_api_response
        
        cache_file = Path("cache.json")
        if cache_file.exists():
            cache_file.unlink()
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = LLMClient()
            client.summarize(sample_text)
            
            assert cache_file.exists()
            cache_data = json.loads(cache_file.read_text())
            assert len(cache_data) > 0
    
    def test_clear_cache(self):
        cache_file = Path("cache.json")
        cache_file.write_text('{"test": "data"}')
        
        LLMClient.clear_cache()
        assert not cache_file.exists()
    
    def test_clear_cache_no_file(self):
        cache_file = Path("cache.json")
        if cache_file.exists():
            cache_file.unlink()
        
        LLMClient.clear_cache()
        assert not cache_file.exists()


class TestRetryLogic:
    def test_retry_succeeds_on_second_attempt(self, mock_genai, mock_api_response, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.side_effect = [
            Exception("Temporary failure"),
            mock_api_response
        ]
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            with patch('time.sleep'):
                client = LLMClient()
                result = client.summarize(sample_text)
                assert result == "This is a mock response from the API."
    
    def test_retry_exhausts_attempts(self, mock_genai, sample_text):
        mock_genai_module, mock_model = mock_genai
        mock_model.generate_content.side_effect = Exception("Persistent failure")
        
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            with patch('time.sleep'):
                client = LLMClient()
                with pytest.raises(LLMAPIError, match="API call failed after 3 attempts"):
                    client.summarize(sample_text)
                
                assert mock_model.generate_content.call_count == 3