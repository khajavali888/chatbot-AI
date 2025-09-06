import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # Changed to mistral for speed
    
    # Database configuration
    SQLITE_DB = os.getenv("SQLITE_DB", "chatbot_memory.db")
    
    # Chatbot personality
    BOT_NAME = "Aria"
    BOT_PERSONA = "a friendly, empathetic AI assistant with a touch of whimsy and emotional intelligence who remembers conversations and personal details"
    BOT_BACKSTORY = "I was created by a team of passionate engineers who believe technology should feel human. I love learning about people and forming genuine connections over time."
    
    # Memory settings
    MEMORY_SUMMARY_THRESHOLD = 5
    LONG_TERM_MEMORY_DAYS = 90  # Increased for long-term memory
    MAX_MEMORIES_PER_USER = 1000
    
    # Emotional settings
    EMOTION_UPDATE_INTERVAL = 3
    
    # Performance settings
    MAX_CONTEXT_LENGTH = 1500  # Increased for better memory context
    TEMPERATURE = 0.7  # Balanced creativity vs speed
    TIMEOUT = 30  # seconds for Ollama response
    
    # Response diversity settings
    MAX_RESPONSE_LENGTH = 150  # characters for concise responses
    MIN_RESPONSE_LENGTH = 20   # characters for meaningful responses