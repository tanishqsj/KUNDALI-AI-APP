import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import io
sys.path.append(os.getcwd())

# Mock faster_whisper before importing app.ai.transcriber
sys.modules["faster_whisper"] = MagicMock()
from app.ai.transcriber import Transcriber

class TestTranscriber(unittest.TestCase):
    def setUp(self):
        # Reset the singleton for testing
        Transcriber._instance = None
        
    @patch("app.ai.transcriber.WhisperModel")
    def test_transcribe(self, mock_whisper_model):
        # Mock the WhisperModel instance and its transcribe method
        mock_model_instance = MagicMock()
        mock_whisper_model.return_value = mock_model_instance
        
        # Mock segments generator
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock(language="en", language_probability=0.99))
        
        # Initialize transcriber
        transcriber = Transcriber()
        
        # Test transcription
        audio_bytes = b"fake audio data"
        text = transcriber.transcribe(audio_bytes)
        
        self.assertEqual(text, "Hello world")
        mock_model_instance.transcribe.assert_called_once()
        
        # Verify args passed to transcribe
        call_args = mock_model_instance.transcribe.call_args
        # First arg is file-like object
        self.assertIsInstance(call_args[0][0], io.BytesIO)

if __name__ == "__main__":
    unittest.main()
