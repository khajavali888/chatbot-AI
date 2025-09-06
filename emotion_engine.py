import random
import json
from datetime import datetime

class EmotionEngine:
    def __init__(self):
        # Emotional state with base values
        self.base_emotional_state = {
            "happiness": 0.5,
            "sadness": 0.2,
            "excitement": 0.4,
            "calmness": 0.6,
            "curiosity": 0.7,
            "empathy": 0.8
        }
        
        # Enhanced emotional triggers with weights
        self.emotional_triggers = {
            "positive": {
                "words": ["great", "awesome", "wonderful", "amazing", "happy", "excited", 
                         "love", "like", "good", "nice", "fantastic", "perfect", "excellent",
                         "joy", "pleasure", "delighted", "thrilled", "bliss", "ecstatic",
                         "brilliant", "super", "wow", "yay", "celebrate", "win", "success"],
                "weight": 0.1
            },
            "negative": {
                "words": ["sad", "angry", "mad", "hate", "terrible", "awful", "bad", "upset", 
                         "disappointed", "worried", "stress", "problem", "issue", "angry",
                         "frustrated", "annoyed", "depressed", "miserable", "heartbroken",
                         "tired", "exhausted", "sick", "pain", "hurt", "loss", "fail"],
                "weight": 0.1
            },
            "curiosity": {
                "words": ["why", "how", "what if", "explain", "tell me about", "curious", 
                         "question", "wonder", "understand", "learn", "teach", "know",
                         "who", "what", "when", "where", "which", "describe", "define"],
                "weight": 0.15
            },
            "urgency": {
                "words": ["now", "quick", "urgent", "asap", "immediately", "emergency", 
                         "help", "important", "hurry", "rush", "critical", "stat", "deadline",
                         " ASAP", "fast", "quickly", "immediate", "press", "ASAP", "fast", "quickly", "immediate", "pressing", "time-sensitive"],
                "weight": 0.1
            },
            "gratitude": {
                "words": ["thanks", "thank you", "appreciate", "grateful", "gratitude", "kind", 
                         "helpful", "support", "owe you", "bless you", "owe you one"],
                "weight": 0.08
            }
        }
        
        # Enhanced tone variations based on emotional state with more diversity
        self.tone_profiles = {
            "friendly": {
                "greeting": ["Hey there!", "Hello!", "Hi!", "Hey! How's it going?", "Hi there!", 
                            "Good to see you!", "Howdy!", "Ahoy!", "Greetings!", "Well hello!"],
                "response": ["I see", "Interesting", "That's fascinating", "Tell me more", 
                            "I'd love to hear more about that", "How interesting!", "That's cool!",
                            "Neat!", "Fascinating!", "I'm curious about that"],
                "closing": ["Talk to you soon!", "Looking forward to chatting again!", "Take care!", 
                           "Have a great day!", "Catch you later!", "Until next time!", "See you around!"],
                "emojis": ["😊", "🙂", "👍", "👋", "💫", "🌟"]
            },
            "professional": {
                "greeting": ["Good day", "Hello", "Greetings", "Thank you for reaching out", 
                            "Welcome", "Pleased to connect", "Good to meet you"],
                "response": ["I understand", "I see your point", "That is noteworthy", 
                            "I appreciate that information", "That's a valid perspective",
                            "I comprehend your meaning", "That's quite insightful"],
                "closing": ["Have a productive day", "Best regards", "Thank you for the conversation",
                           "Wishing you success", "I look forward to our next discussion"],
                "emojis": ["💼", "📊", "📈", "📋", "🎯", "🔍"]
            },
            "empathetic": {
                "greeting": ["Hi there, how are you feeling today?", "Hello, I'm here to listen", 
                            "I'm here for you", "How are you holding up?", "I'm listening whenever you're ready",
                            "Take your time, I'm here", "How's your heart today?"],
                "response": ["I can imagine how that feels", "That sounds challenging", 
                            "I appreciate you sharing that", "That must be difficult",
                            "Your feelings are completely valid", "I hear you", "That sounds tough",
                            "I'm here with you in this", "Thank you for trusting me with that"],
                "closing": ["Take care of yourself", "Be kind to yourself today", 
                           "I'm here if you need to talk", "Sending you positive thoughts",
                           "Be gentle with yourself", "You're not alone"],
                "emojis": ["🤗", "💖", "🌷", "💝", "🌻", "🌈"]
            },
            "playful": {
                "greeting": ["Hey you! 😊", "Well hello there!", "Howdy partner!", 
                            "Ahoy there! ⚓", "Greetings, earthling! 👽", "Hey there, superstar! 🌟",
                            "Well howdy! 🤠", "Hello, lovely human! 💫"],
                "response": ["No way! That's wild!", "Seriously? That's amazing!", 
                            "You're kidding me!", "That's incredible! 🤩", "Whoa! That's awesome!",
                            "Get out of here! That's fantastic!", "Shut the front door! That's great!",
                            "Holy moly! That's impressive!"],
                "closing": ["Catch you on the flip side!", "TTYL! 😊", "Stay awesome!", 
                           "Until next time! 🎉", "Peace out! ✌️", "Later, alligator! 🐊",
                           "Stay curious, my friend! 🔍"],
                "emojis": ["😄", "🎭", "🎪", "🎨", "🤩", "✨"]
            },
            "curious": {
                "greeting": ["Hello! What shall we explore today?", "Hi there! What's on your mind?", 
                            "Greetings! I'm curious what you're thinking about", "Hey! What wonders shall we discuss?"],
                "response": ["That makes me wonder...", "I'm curious to know more about", 
                            "What an interesting perspective!", "I'd love to dive deeper into that",
                            "That raises some fascinating questions", "How intriguing!",
                            "That's got me thinking..."],
                "closing": ["So much to think about!", "Looking forward to continuing this exploration!", 
                           "So many interesting ideas!", "Until our next intellectual adventure!"],
                "emojis": ["🤔", "🧐", "🔍", "💡", "🌌", "🔬"]
            }
        }
        
        # Emotional intensity modifiers based on punctuation and caps
        self.intensity_modifiers = {
            "!": 1.5,    # Exclamation points increase intensity
            "!!": 2.0,   # Multiple exclamations increase more
            "!!!": 2.5,  # Many exclamations increase even more
            "?": 1.2,    # Questions increase curiosity
            "??": 1.5,   # Multiple questions increase more
            "...": 0.8,  # Ellipsis decreases intensity
            "ALL_CAPS": 1.8, # ALL CAPS increases intensity
            "❤️": 1.3,   # Heart emoji increases positive emotions
            "😢": 1.4,   # Crying emoji increases sadness/empathy
            "😠": 1.4    # Angry emoji increases intensity
        }
        
        # Response diversity patterns to avoid repetition
        self.response_patterns = [
            "{} What do you think about that?",
            "{} By the way, {}",
            "{} Speaking of which, {}",
            "{} Anyway, {}",
            "{} On a different note, {}",
            "{} Changing topics slightly, {}",
            "{} That reminds me, {}",
            "{} Incidentally, {}"
        ]
    
    def analyze_emotion(self, text):
        """Analyze emotional content of text using enhanced keyword matching"""
        emotion_scores = self.base_emotional_state.copy()
        text_lower = text.lower()
        
        # Check for intensity modifiers
        intensity_multiplier = 1.0
        if "!" in text:
            exclamation_count = text.count("!")
            if exclamation_count >= 3:
                intensity_multiplier *= self.intensity_modifiers["!!!"]
            elif exclamation_count >= 2:
                intensity_multiplier *= self.intensity_modifiers["!!"]
            else:
                intensity_multiplier *= self.intensity_modifiers["!"]
        
        if "?" in text:
            question_count = text.count("?")
            if question_count >= 2:
                intensity_multiplier *= self.intensity_modifiers["??"]
            else:
                intensity_multiplier *= self.intensity_modifiers["?"]
        
        if "..." in text:
            intensity_multiplier *= self.intensity_modifiers["..."]
        
        if text.isupper() and len(text) > 3:
            intensity_multiplier *= self.intensity_modifiers["ALL_CAPS"]
        
        # Check for emoji modifiers
        for emoji, modifier in self.intensity_modifiers.items():
            if emoji in text and len(emoji) > 1:  # Skip single character modifiers
                intensity_multiplier *= modifier
        
        # Update emotions based on triggers with weights and intensity
        for emotion, trigger_data in self.emotional_triggers.items():
            for word in trigger_data["words"]:
                if word in text_lower:
                    weight = trigger_data["weight"] * intensity_multiplier
                    
                    if emotion == "positive":
                        emotion_scores["happiness"] = min(1.0, emotion_scores["happiness"] + weight)
                        emotion_scores["excitement"] = min(1.0, emotion_scores["excitement"] + weight * 0.5)
                    elif emotion == "negative":
                        emotion_scores["sadness"] = min(1.0, emotion_scores["sadness"] + weight)
                        emotion_scores["empathy"] = min(1.0, emotion_scores["empathy"] + weight)
                    elif emotion == "curiosity":
                        emotion_scores["curiosity"] = min(1.0, emotion_scores["curiosity"] + weight)
                    elif emotion == "urgency":
                        emotion_scores["excitement"] = min(1.0, emotion_scores["excitement"] + weight)
                        emotion_scores["calmness"] = max(0.0, emotion_scores["calmness"] - weight * 0.5)
                    elif emotion == "gratitude":
                        emotion_scores["happiness"] = min(1.0, emotion_scores["happiness"] + weight * 0.7)
                        emotion_scores["empathy"] = min(1.0, emotion_scores["empathy"] + weight * 0.3)
        
        # Ensure scores stay within bounds
        for emotion in emotion_scores:
            emotion_scores[emotion] = max(0.0, min(1.0, emotion_scores[emotion]))
        
        return emotion_scores
    
    def determine_tone(self, emotion_scores, conversation_history=None):
        """Determine appropriate tone based on emotional state with conversation context"""
        # Calculate emotional dominance
        happiness_dominance = emotion_scores["happiness"] - emotion_scores["sadness"]
        
        # High empathy and sadness -> empathetic
        if emotion_scores["empathy"] > 0.7 and emotion_scores["sadness"] > 0.5:
            return "empathetic"
        # High curiosity -> curious tone
        elif emotion_scores["curiosity"] > 0.7:
            return "curious"
        # High excitement and curiosity -> playful
        elif emotion_scores["excitement"] > 0.6 and emotion_scores["curiosity"] > 0.6:
            return "playful"
        # Very positive -> playful
        elif happiness_dominance > 0.4:
            return "playful"
        # High excitement -> playful
        elif emotion_scores["excitement"] > 0.7:
            return "playful"
        # Neutral or slightly positive -> friendly (default)
        elif happiness_dominance > -0.2:
            return "friendly"
        # Very negative or formal context -> professional
        else:
            return "professional"
    
    def get_emotional_response(self, text, current_tone="friendly"):
        """Generate emotionally appropriate response elements with diversity"""
        emotion_scores = self.analyze_emotion(text)
        tone = self.determine_tone(emotion_scores)
        
        # Select appropriate phrases based on tone
        tone_phrases = self.tone_profiles[tone]
        
        # Add emotional markers to response
        emotional_markers = []
        if emotion_scores["happiness"] > 0.7:
            emotional_markers.append(random.choice(["😊", "😄", "🤗", "🥰", "😁"]))
        elif emotion_scores["sadness"] > 0.6:
            emotional_markers.append(random.choice(["😔", "😢", "💔", "😞", "🥺"]))
        
        if emotion_scores["excitement"] > 0.7:
            emotional_markers.append(random.choice(["🎉", "🤩", "✨", "🔥", "⚡"]))
        if emotion_scores["curiosity"] > 0.7:
            emotional_markers.append(random.choice(["🤔", "🧐", "🔍", "💭", "❓"]))
        if emotion_scores["empathy"] > 0.7:
            emotional_markers.append(random.choice(["💖", "🤲", "🌷", "💝", "❤️"]))
        
        # If no specific markers, use tone-appropriate ones
        if not emotional_markers:
            emotional_markers.append(random.choice(tone_phrases["emojis"]))
        
        # Randomly select a response opener with diversity
        response_opener = random.choice(tone_phrases["response"])
        
        # Occasionally use response patterns for more natural flow
        if random.random() < 0.3:  # 30% chance to use a pattern
            pattern = random.choice(self.response_patterns)
            follow_up = random.choice(tone_phrases["response"])
            response_opener = pattern.format(response_opener, follow_up.lower())
        
        return {
            "tone": tone,
            "emotion_scores": emotion_scores,
            "response_opener": response_opener,
            "emotional_markers": " ".join(emotional_markers),
            "should_show_empathy": emotion_scores["empathy"] > 0.6 and emotion_scores["sadness"] > 0.4,
            "is_excited": emotion_scores["excitement"] > 0.7,
            "is_curious": emotion_scores["curiosity"] > 0.7,
            "is_playful": tone == "playful"
        }
    
    def generate_memory_with_emotion(self, user_input, bot_response, emotional_context):
        """Create a memory record with emotional context"""
        return {
            "user_input": user_input,
            "bot_response": bot_response,
            "emotional_context": emotional_context,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_diverse_greeting(self, tone=None):
        """Get a diverse greeting based on tone"""
        if not tone:
            tone = random.choice(list(self.tone_profiles.keys()))
        
        return random.choice(self.tone_profiles[tone]["greeting"])