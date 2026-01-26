import io
import logging
from threading import Lock
from typing import Optional

from faster_whisper import WhisperModel
from app.config import settings

logger = logging.getLogger(__name__)

class Transcriber:
    """
    Singleton class for local Whisper transcription.
    """
    _instance: Optional["Transcriber"] = None
    _lock: Lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Transcriber, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the Whisper model.
        """
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE} on {settings.WHISPER_DEVICE}")
        try:
            self.model = WhisperModel(
                settings.WHISPER_MODEL_SIZE,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise e

    def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio bytes using the local model.
        Blocking call - should be run in an executor.
        """
        try:
            # faster-whisper accepts a file-like object or path
            audio_file = io.BytesIO(audio_bytes)
            
            segments, info = self.model.transcribe(
                audio_file,
                language=language if language != "auto" else None,
                beam_size=5
            )
            
            # segments is a generator, so we must iterate to get the text
            text_segments = [segment.text for segment in segments]
            full_text = " ".join(text_segments).strip()
            
            logger.info(f"Transcription complete. Language: {info.language}, Probability: {info.language_probability}")
            return full_text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise e
