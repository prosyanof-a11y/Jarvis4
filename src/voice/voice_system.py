"""
Voice System — Speech-to-Text-to-AI-to-Text-to-Speech pipeline.

Pipeline: Speech → Text → AI → Text → Speech

Voice responses must be:
- Short
- Clear
- Natural
- Conversational
"""

import asyncio
import logging
import io
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Speech Recognition
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    logger.warning("SpeechRecognition not installed")

# Text-to-Speech (pyttsx3 — offline)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not installed")

# Text-to-Speech (gTTS — online)
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not installed")


class VoiceSystem:
    """
    Voice pipeline: Speech → Text → AI → Text → Speech
    
    Supports:
    - Google Speech Recognition (STT)
    - pyttsx3 offline TTS
    - gTTS online TTS
    - Microphone input
    - Audio file input
    """

    def __init__(self, language: str = "ru", tts_engine: str = "gtts"):
        self.language = language
        self.tts_engine = tts_engine
        self.recognizer = sr.Recognizer() if STT_AVAILABLE else None
        self._pyttsx_engine = None

        if PYTTSX3_AVAILABLE and tts_engine == "pyttsx3":
            try:
                self._pyttsx_engine = pyttsx3.init()
                self._pyttsx_engine.setProperty("rate", 150)
                voices = self._pyttsx_engine.getProperty("voices")
                # Try to find Russian voice
                for voice in voices:
                    if "ru" in voice.id.lower() or "russian" in voice.name.lower():
                        self._pyttsx_engine.setProperty("voice", voice.id)
                        break
            except Exception as e:
                logger.error(f"pyttsx3 init error: {e}")

    # ─── Speech to Text ────────────────────────────────────────────

    async def listen_microphone(self, timeout: int = 5) -> Optional[str]:
        """Listen to microphone and convert speech to text."""
        if not STT_AVAILABLE:
            logger.error("SpeechRecognition not available")
            return None

        def _listen():
            with sr.Microphone() as source:
                logger.info("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
                return audio

        try:
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(None, _listen)
            text = await self.speech_to_text(audio)
            return text
        except sr.WaitTimeoutError:
            logger.info("Listening timeout")
            return None
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None

    async def speech_to_text(self, audio) -> Optional[str]:
        """Convert audio to text using Google Speech Recognition."""
        if not STT_AVAILABLE:
            return None

        def _recognize():
            return self.recognizer.recognize_google(audio, language=self.language)

        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, _recognize)
            logger.info(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"STT service error: {e}")
            return None

    async def speech_to_text_from_file(self, audio_path: str) -> Optional[str]:
        """Convert audio file to text."""
        if not STT_AVAILABLE:
            return None

        def _recognize_file():
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language=self.language)

        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, _recognize_file)
            return text
        except Exception as e:
            logger.error(f"File STT error: {e}")
            return None

    # ─── Text to Speech ────────────────────────────────────────────

    async def text_to_speech(self, text: str, output_path: str = None) -> Optional[str]:
        """Convert text to speech audio."""
        # Make response short and natural
        text = self._make_conversational(text)

        if self.tts_engine == "gtts" and GTTS_AVAILABLE:
            return await self._tts_gtts(text, output_path)
        elif self.tts_engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            return await self._tts_pyttsx3(text, output_path)
        else:
            logger.error(f"TTS engine '{self.tts_engine}' not available")
            return None

    async def _tts_gtts(self, text: str, output_path: str = None) -> Optional[str]:
        """Google Text-to-Speech (online)."""
        def _generate():
            tts = gTTS(text=text, lang=self.language)
            path = output_path or "workspace/voice_output.mp3"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tts.save(path)
            return path

        try:
            loop = asyncio.get_event_loop()
            path = await loop.run_in_executor(None, _generate)
            logger.info(f"TTS saved to: {path}")
            return path
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return None

    async def _tts_pyttsx3(self, text: str, output_path: str = None) -> Optional[str]:
        """Offline Text-to-Speech."""
        if not self._pyttsx_engine:
            return None

        def _speak():
            if output_path:
                self._pyttsx_engine.save_to_file(text, output_path)
                self._pyttsx_engine.runAndWait()
                return output_path
            else:
                self._pyttsx_engine.say(text)
                self._pyttsx_engine.runAndWait()
                return None

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _speak)
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return None

    # ─── Full Pipeline ─────────────────────────────────────────────

    async def voice_pipeline(self, process_func) -> Optional[str]:
        """
        Full voice pipeline: Speech → Text → Process → Text → Speech
        
        Args:
            process_func: async function that takes text and returns response text
        """
        # Step 1: Listen
        text = await self.listen_microphone()
        if not text:
            return None

        logger.info(f"User said: {text}")

        # Step 2: Process through AI
        response = await process_func(text)
        if not response:
            return None

        logger.info(f"AI response: {response}")

        # Step 3: Speak
        audio_path = await self.text_to_speech(response)
        return audio_path

    def _make_conversational(self, text: str) -> str:
        """Make text short, clear, natural, conversational."""
        # Limit length for voice
        if len(text) > 300:
            sentences = text.split(".")
            short = ". ".join(sentences[:3])
            if short:
                return short + "."
            return text[:300] + "..."
        return text
