import asyncio
import edge_tts
from typing import AsyncGenerator

class TTSService:
    """
    Service to convert text to speech using Microsoft Edge TTS (Free).
    """

    VOICE_MAP = {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural",
        "mr": "mr-IN-AarohiNeural"
    }

    def __init__(self, language: str = "en"):
        self.voice = self.VOICE_MAP.get(language, "en-IN-NeerjaNeural")

    async def generate_audio(self, text: str) -> tuple[bytes, list]:
        """
        Generate audio and word timings.
        Returns: (audio_bytes, timings_list)
        """
        communicate = edge_tts.Communicate(text, self.voice)
        audio_data = b""
        timings = []
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                # chunk dict keys: "offset", "duration", "text"
                # offset is in 100ns units (ticks). Divide by 10,000,000 to get seconds.
                # duration is same.
                start_sec = chunk["offset"] / 10_000_000
                duration_sec = chunk["duration"] / 10_000_000
                timings.append({
                    "word": chunk["text"],
                    "start": start_sec,
                    "end": start_sec + duration_sec
                })
                
        return audio_data, timings

    async def stream_audio_from_text_stream(
        self, 
        text_stream: AsyncGenerator[str, None]
    ) -> AsyncGenerator[bytes, None]:
        """
        Consumes a text stream, buffers it into sentences, 
        and yields audio bytes for each sentence.
        
        This mimics 'streaming TTS' by processing sentence-by-sentence.
        """
        buffer = ""
        # Simple sentence delimiters
        delimiters = {".", "?", "!", ":", ";", "\n"}

        async for text_chunk in text_stream:
            buffer += text_chunk
            
            # Check if we have a complete sentence
            # We look for the last delimiter
            last_delim_pos = -1
            for i, char in enumerate(buffer):
                if char in delimiters:
                    last_delim_pos = i
            
            # If we found a delimiter, process everything up to it
            if last_delim_pos != -1:
                sentence = buffer[:last_delim_pos+1].strip()
                remainder = buffer[last_delim_pos+1:]
                
                if sentence:
                    # Generate audio for this sentence
                    audio_bytes = await self.generate_audio(sentence)
                    yield audio_bytes
                
                buffer = remainder

        # Process any remaining text in buffer
        if buffer.strip():
             audio_bytes = await self.generate_audio(buffer.strip())
             yield audio_bytes
