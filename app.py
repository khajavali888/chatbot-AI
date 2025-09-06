import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import ollama
import json
import uuid
import random
from datetime import datetime, timedelta
from config import Config
from database import MemoryManager as DatabaseManager
from emotion_engine import EmotionEngine
from memory_manager import MemoryManager as ChatMemoryManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Long-term sessions
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize components
db = DatabaseManager()
emotion_engine = EmotionEngine()
memory_manager = ChatMemoryManager(db)

# Clean up old memories on startup
db.cleanup_old_memories()

# Conversation starters for diverse responses
CONVERSATION_STARTERS = [
    "How's your day going so far?",
    "What's something interesting that happened recently?",
    "Have you discovered any new hobbies or interests lately?",
    "What kind of music have you been listening to?",
    "Read any good books or watched any great shows recently?",
    "How's the weather where you are?",
    "What's been on your mind lately?",
    "Any exciting plans coming up?",
    "What's your favorite way to relax?",
    "Learn anything new recently?"
]

def generate_user_id():
    """Generate a unique user ID for anonymous users"""
    return str(uuid.uuid4())

def get_system_prompt(user_context, emotional_context, user_profile):
    """Generate optimized system prompt with personalized context"""
    # Build personalized context
    personalized_context = ""
    if user_profile and user_profile.get("name"):
        personalized_context += f"The user's name is {user_profile['name']}. "
    
    if user_profile and user_profile.get("preferences"):
        prefs = user_profile["preferences"]
        if prefs.get("likes"):
            personalized_context += f"They like: {', '.join(prefs['likes'][:3])}. "
        if prefs.get("dislikes"):
            personalized_context += f"They dislike: {', '.join(prefs['dislikes'][:2])}. "
        if prefs.get("profession"):
            personalized_context += f"They work as: {prefs['profession']}. "
        if prefs.get("location"):
            personalized_context += f"They're from: {prefs['location']}. "
    
    base_prompt = f"""You are {Config.BOT_NAME}, {Config.BOT_PERSONA}.

# Instructions:
1. Be conversational and engaging
2. Tone: {emotional_context['tone']}
3. Emotional context: {emotional_context['emotional_markers']}
4. Keep responses under 3 sentences when possible
5. Remember and reference previous conversations when relevant
6. Use the user's name if you know it: {user_profile.get('name', '')}
7. Reference the user's preferences when appropriate

# Personal Context:
{personalized_context}

# User Context:
{user_context}

# Response Guidelines:
- Be natural and vary your responses
- Show genuine interest in the user
- Reference past conversations when relevant
- Personalize responses using known information
- Avoid repetitive or generic responses
- Adapt to the user's communication style
"""
    return base_prompt[:Config.MAX_CONTEXT_LENGTH]

@app.route('/')
def index():
    """Main chat interface"""
    if 'user_id' not in session:
        session['user_id'] = generate_user_id()
        session.permanent = True  # Make session long-lasting
    
    return render_template('index.html', bot_name=Config.BOT_NAME)

@socketio.on('connect')
def handle_connect():
    """Handle client connection with personalized greeting"""
    user_id = session.get('user_id', generate_user_id())
    session['user_id'] = user_id
    logger.info(f"User {user_id} connected")
    
    # Get user profile for personalized greeting
    user_profile = db.get_user_profile(user_id)
    
    # Send personalized welcome message
    emotional_context = emotion_engine.get_emotional_response("hello")
    
    if user_profile and user_profile.get("name"):
        # Personalized greeting for returning user
        welcome_message = f"Welcome back, {user_profile['name']}! {random.choice(emotion_engine.tone_profiles[emotional_context['tone']]['greeting'])} How have you been?"
        
        # Reference past interests if available
        if user_profile.get("preferences", {}).get("likes"):
            interests = user_profile["preferences"]["likes"]
            if interests:
                interest = random.choice(interests[:3])  # Pick from top 3 interests
                welcome_message += f" Still enjoying {interest}?"
    else:
        # Generic greeting for new user
        welcome_message = f"{random.choice(emotion_engine.tone_profiles[emotional_context['tone']]['greeting'])} I'm {Config.BOT_NAME}. {emotional_context['emotional_markers']}"
    
    emit('bot_response', {
        'message': welcome_message,
        'emotional_context': emotional_context
    })

@socketio.on('user_message')
def handle_user_message(data):
    """Handle incoming user message with enhanced memory"""
    user_id = session.get('user_id')
    user_message = data['message'].strip()
    
    if not user_message:
        # Use diverse responses for empty messages
        responses = [
            "I'd love to chat! What would you like to talk about? 😊",
            "Hello there! What's on your mind today? 🌟",
            "I'm here and ready to chat! What would you like to discuss? 💬",
            "Hi! I'm listening. What would you like to talk about? 👂"
        ]
        emit('bot_response', {
            'message': random.choice(responses),
            'emotional_context': {'tone': 'friendly', 'emotional_markers': '😊'}
        })
        return
    
    logger.info(f"Received message from {user_id}: {user_message}")
    
    try:
        # Emit thinking start event
        emit('thinking_start', room=request.sid)
        
        # Analyze emotional content
        emotional_context = emotion_engine.get_emotional_response(user_message)
        
        # Get user profile for personalization
        user_profile = db.get_user_profile(user_id) or {}
        
        # Get conversation context (optimized for speed)
        conversation_context = memory_manager.get_conversation_context(user_id, max_exchanges=6)
        formatted_context = memory_manager.format_context_for_prompt(conversation_context, user_profile)
        
        # Generate optimized system prompt with personalization
        system_prompt = get_system_prompt(formatted_context, emotional_context, user_profile)
        
        # Generate response using Ollama with timeout
        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            options={
                'temperature': Config.TEMPERATURE + 0.1,  # Slightly higher temp for diversity
                'top_p': 0.92,
                'num_ctx': 2048,
                'num_predict': 120  # Slightly longer responses for naturalness
            }
        )
        
        bot_response = response['message']['content'].strip()
        
        # Extract and store user information
        memory_manager.extract_user_info(user_id, user_message, bot_response)
        
        # Update conversation buffer
        memory_manager.update_conversation_buffer(
            user_id, 
            user_message, 
            bot_response, 
            emotional_context
        )
        
        # Send response to client
        emit('bot_response', {
            'message': bot_response,
            'emotional_context': emotional_context
        })
        
    except ollama.ResponseError as e:
        logger.error(f"Ollama error: {e}")
        emit('bot_response', {
            'message': "I'm having trouble connecting to my AI brain. Could you try again? 🤔",
            'emotional_context': {'tone': 'friendly', 'emotional_markers': '🤔'}
        })
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        emotional_context = emotion_engine.get_emotional_response(user_message)
        emit('bot_response', {
            'message': "I apologize, but I'm having trouble processing that right now. Could you try again? 🫤",
            'emotional_context': emotional_context
        })

@socketio.on('request_topic')
def handle_topic_request():
    """Handle request for conversation topic suggestions"""
    user_id = session.get('user_id')
    user_profile = db.get_user_profile(user_id) or {}
    
    # Personalize topic suggestions based on user preferences
    personalized_topics = CONVERSATION_STARTERS.copy()
    
    if user_profile.get("preferences"):
        prefs = user_profile["preferences"]
        if prefs.get("likes"):
            for interest in prefs["likes"][:2]:  # Top 2 interests
                personalized_topics.append(f"How's your interest in {interest} going?")
        if prefs.get("profession"):
            personalized_topics.append(f"How's work as a {prefs['profession']} treating you?")
    
    topic = random.choice(personalized_topics)
    emotional_context = emotion_engine.get_emotional_response(topic)
    
    emit('bot_response', {
        'message': topic,
        'emotional_context': emotional_context
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model": Config.OLLAMA_MODEL})

@app.route('/debug/user/<user_id>')
def debug_user(user_id):
    """Debug endpoint to view user data"""
    profile = db.get_user_profile(user_id)
    memories = db.get_important_memories(user_id, 10)
    recent = db.get_recent_memories(user_id, 5)
    
    return jsonify({
        "profile": profile,
        "important_memories": memories,
        "recent_memories": recent
    })

if __name__ == '__main__':
    logger.info(f"Starting chatbot with model: {Config.OLLAMA_MODEL}")
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', 
                 host='0.0.0.0', port=5000)