import json
import re
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, database):
        self.db = database
        self.conversation_buffers = {}
        # Enhanced user info patterns with more variations
        self.user_info_patterns = {
            'name': [
                re.compile(r'(?:my name is|i am called|you can call me|i\'m|call me|name\'s)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
                re.compile(r'(?:i am|it\'s|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE),
                re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', re.IGNORECASE)
            ],
            'likes': [
                re.compile(r'(?:i like|i love|i enjoy|i\'m into|i really like|i adore)\s+([^.!?]+)', re.IGNORECASE),
                re.compile(r'(?:my favorite|my fav|i prefer)\s+(?:thing|activity|hobby|sport|food|color|movie|book|music|band|artist)\s+is\s+([^.!?]+)', re.IGNORECASE)
            ],
            'dislikes': [
                re.compile(r'(?:i hate|i dislike|i don\'t like|i can\'t stand)\s+([^.!?]+)', re.IGNORECASE)
            ],
            'profession': [
                re.compile(r'(?:i work as|i am a|i\'m a|my job is|i do)\s+([^.!?]+)', re.IGNORECASE),
                re.compile(r'(?:i work in|i\'m in)\s+the\s+([^.!?]+)\s+(?:industry|field)', re.IGNORECASE)
            ],
            'location': [
                re.compile(r'(?:i live in|i\'m from|from|based in|located in)\s+([^.!?]+)', re.IGNORECASE)
            ],
            'relationships': [
                re.compile(r'(?:my (?:wife|husband|partner|boyfriend|girlfriend|friend|mom|dad|parent|sister|brother|family)\'s name is|(?:wife|husband|partner|boyfriend|girlfriend|friend|mom|dad|parent|sister|brother) is called)\s+([A-Z][a-z]+)', re.IGNORECASE)
            ]
        }
    
    def get_conversation_context(self, user_id, max_exchanges=5):
        """Get optimized conversation context"""
        try:
            recent_memories = self.db.get_recent_memories(user_id, max_exchanges)
            important_memories = self.db.get_important_memories(user_id, 3)  # Increased for better recall
            memory_summaries = self.db.get_memory_summaries(user_id, 2)      # Increased for better context
            user_profile = self.db.get_user_profile(user_id) or {}
            
            return {
                "user_profile": user_profile,
                "recent_conversation": recent_memories,
                "important_memories": important_memories,
                "memory_summaries": memory_summaries
            }
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {"user_profile": {}, "recent_conversation": [], "important_memories": [], "memory_summaries": []}
    
    def format_context_for_prompt(self, context, user_profile=None):
        """Format context efficiently with enhanced user details"""
        prompt_parts = []
        
        # Use provided user_profile or from context
        profile = user_profile or context.get("user_profile", {})
        
        # Add user profile information if available
        if profile:
            if profile.get("name"):
                prompt_parts.append(f"User's name: {profile['name']}")
            
            if profile.get("preferences"):
                prefs = profile["preferences"]
                if prefs.get("likes"):
                    prompt_parts.append(f"User likes: {', '.join(prefs['likes'][:3])}")
                if prefs.get("dislikes"):
                    prompt_parts.append(f"User dislikes: {', '.join(prefs['dislikes'][:2])}")
                
                # Add other known preferences
                for key, value in prefs.items():
                    if key not in ["likes", "dislikes"] and value:
                        if isinstance(value, list):
                            prompt_parts.append(f"User's {key}: {', '.join(value[:2])}")
                        else:
                            prompt_parts.append(f"User's {key}: {value}")
        
        if context.get("memory_summaries"):
            for summary in context["memory_summaries"][:2]:  # Up to 2 summaries
                prompt_parts.append(f"Previous conversation summary: {summary['text']}")
        
        if context.get("important_memories"):
            prompt_parts.append("Important memories from past conversations:")
            for memory in context["important_memories"][:3]:  # Up to 3 important memories
                prompt_parts.append(f"- {memory['text'][:120]}...")
        
        if context.get("recent_conversation"):
            prompt_parts.append("Recent conversation:")
            for memory in context["recent_conversation"][:3]:  # Up to 3 recent exchanges
                if isinstance(memory, dict):
                    prompt_parts.append(f"User: {memory.get('user_input', '')[:60]}")
                    prompt_parts.append(f"Assistant: {memory.get('bot_response', '')[:60]}")
        
        return "\n".join(prompt_parts)[:1000]  # Increased context length for better memory
    
    def update_conversation_buffer(self, user_id, user_input, bot_response, emotional_context):
        """Update conversation buffer efficiently"""
        if user_id not in self.conversation_buffers:
            self.conversation_buffers[user_id] = []
        
        memory_data = {
            "user_input": user_input,
            "bot_response": bot_response,
            "emotional_context": emotional_context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_buffers[user_id].append(memory_data)
        
        # Store in database with higher importance for personal information
        memory_text = f"User: {user_input[:100]}... | Bot: {bot_response[:100]}..."
        
        # Check if this contains personal information for higher importance
        importance = 1
        if self._contains_personal_info(user_input):
            importance = 3  # High importance for personal info
        
        self.db.store_memory(
            user_id, 
            memory_text, 
            "conversation_exchange", 
            emotional_context,
            importance=importance
        )
        
        # Check for summarization more frequently for active conversations
        if len(self.conversation_buffers[user_id]) >= Config.MEMORY_SUMMARY_THRESHOLD:
            self._create_conversation_summary(user_id)
    
    def _contains_personal_info(self, text):
        """Check if text contains personal information"""
        text_lower = text.lower()
        personal_keywords = [
            'name', 'live', 'from', 'work', 'job', 'like', 'love', 'hate', 
            'dislike', 'favorite', 'family', 'friend', 'pet', 'hobby', 'born',
            'grew up', 'grow up', 'childhood', 'school', 'college', 'university'
        ]
        return any(keyword in text_lower for keyword in personal_keywords)
    
    def _create_conversation_summary(self, user_id):
        """Create detailed conversation summary for long-term memory"""
        if user_id not in self.conversation_buffers or not self.conversation_buffers[user_id]:
            return
        
        # Extract key topics and emotions from conversation
        topics = set()
        emotions = []
        
        for exchange in self.conversation_buffers[user_id]:
            # Simple topic extraction (in a real implementation, use NLP)
            user_input = exchange['user_input'].lower()
            if 'movie' in user_input or 'film' in user_input:
                topics.add('movies')
            if 'music' in user_input or 'song' in user_input:
                topics.add('music')
            if 'book' in user_input or 'read' in user_input:
                topics.add('reading')
            if 'sport' in user_input or 'game' in user_input:
                topics.add('sports')
            if 'work' in user_input or 'job' in user_input:
                topics.add('work')
            if 'travel' in user_input or 'vacation' in user_input:
                topics.add('travel')
            
            # Collect emotions
            if 'emotional_context' in exchange:
                emotions.append(exchange['emotional_context'].get('tone', 'neutral'))
        
        # Determine dominant emotion
        emotion_count = {}
        for emotion in emotions:
            emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
        dominant_emotion = max(emotion_count.items(), key=lambda x: x[1])[0] if emotion_count else 'neutral'
        
        # Create summary
        topic_str = ", ".join(list(topics)[:3]) if topics else "various topics"
        summary = f"Conversation about {topic_str}. Overall tone was {dominant_emotion}. {len(self.conversation_buffers[user_id])} exchanges."
        
        self.db.create_memory_summary(user_id, summary)
        self.conversation_buffers[user_id] = []  # Clear buffer
    
    def extract_user_info(self, user_id, user_input, response):
        """Enhanced user info extraction using multiple regex patterns"""
        user_profile = self.db.get_user_profile(user_id) or {
            "preferences": {}, 
            "personality_traits": {}
        }
        updated = False
        
        # Ensure preferences has the right structure
        if "likes" not in user_profile["preferences"]:
            user_profile["preferences"]["likes"] = []
        if "dislikes" not in user_profile["preferences"]:
            user_profile["preferences"]["dislikes"] = []
        
        # Name detection with multiple patterns
        for pattern in self.user_info_patterns['name']:
            match = pattern.search(user_input)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1 and name.lower() not in ["i", "me", "you"]:
                    user_profile["name"] = name.title()
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User's name is {name}", 
                        "personal_info", 
                        {"dominant_emotion": "neutral", "importance": "high"},
                        importance=3
                    )
                    break
        
        # Preferences detection - Likes
        for pattern in self.user_info_patterns['likes']:
            match = pattern.search(user_input)
            if match:
                like_item = match.group(1).strip()
                if like_item and like_item not in user_profile["preferences"]["likes"]:
                    user_profile["preferences"]["likes"].append(like_item)
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User likes {like_item}", 
                        "preference", 
                        {"dominant_emotion": "positive", "importance": "medium"},
                        importance=2
                    )
        
        # Preferences detection - Dislikes
        for pattern in self.user_info_patterns['dislikes']:
            match = pattern.search(user_input)
            if match:
                dislike_item = match.group(1).strip()
                if dislike_item and dislike_item not in user_profile["preferences"]["dislikes"]:
                    user_profile["preferences"]["dislikes"].append(dislike_item)
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User dislikes {dislike_item}", 
                        "preference", 
                        {"dominant_emotion": "negative", "importance": "medium"},
                        importance=2
                    )
        
        # Profession detection
        for pattern in self.user_info_patterns['profession']:
            match = pattern.search(user_input)
            if match:
                profession = match.group(1).strip()
                if profession:
                    user_profile["preferences"]["profession"] = profession
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User works as {profession}", 
                        "personal_info", 
                        {"dominant_emotion": "neutral", "importance": "high"},
                        importance=3
                    )
        
        # Location detection
        for pattern in self.user_info_patterns['location']:
            match = pattern.search(user_input)
            if match:
                location = match.group(1).strip()
                if location:
                    user_profile["preferences"]["location"] = location
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User is from {location}", 
                        "personal_info", 
                        {"dominant_emotion": "neutral", "importance": "medium"},
                        importance=2
                    )
        
        # Relationship detection
        for pattern in self.user_info_patterns['relationships']:
            match = pattern.search(user_input)
            if match:
                relation_name = match.group(1).strip()
                if relation_name:
                    # Extract relationship type from pattern
                    rel_type = "unknown"
                    for rel in ['wife', 'husband', 'partner', 'boyfriend', 'girlfriend', 'friend', 'mom', 'dad', 'parent', 'sister', 'brother']:
                        if rel in pattern.pattern:
                            rel_type = rel
                            break
                    
                    if "relationships" not in user_profile["preferences"]:
                        user_profile["preferences"]["relationships"] = {}
                    
                    user_profile["preferences"]["relationships"][rel_type] = relation_name
                    updated = True
                    # Store as important memory
                    self.db.store_memory(
                        user_id, 
                        f"User's {rel_type} is {relation_name}", 
                        "personal_info", 
                        {"dominant_emotion": "neutral", "importance": "medium"},
                        importance=2
                    )
        
        if updated:
            self.db.update_user_profile(user_id, user_profile)
        
        return updated