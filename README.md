# Human-Like Conversational Chatbot

A sophisticated chatbot system with emotional intelligence, long-term memory, and contextual awareness built using Ollama and Flask.

## Features

- 🤖 **Human-like Conversations**: Natural, emotionally engaging responses
- 💾 **Long-term Memory**: Remembers user preferences and past conversations
- 🎭 **Emotional Intelligence**: Adapts tone based on conversational context
- 📊 **Context Awareness**: Maintains conversation context across sessions
- 🚀 **Fast & Responsive**: Optimized for real-time interactions
- 🧠 **Personalization**: Learns from interactions to provide tailored responses

## Architecture

The chatbot uses a multi-layered architecture:

1. **Web Layer**: Flask web server with Socket.IO for real-time communication
2. **AI Layer**: Ollama integration for LLM responses
3. **Memory Layer**: Redis for short-term memory + SQLite for long-term storage
4. **Emotion Engine**: Analyzes and responds to emotional content
5. **Memory Manager**: Handles context building and summarization

## Setup Instructions

### Prerequisites

- Python 3.8+
- Ollama (latest version)
- Redis server

### Installation

1. **Install Ollama**:
   ```bash
   # Follow instructions at https://ollama.ai/
   # Pull the required model
   ollama pull llama3.2
   ```
