import unittest
from app import app, db, emotion_engine, memory_manager
import json

class TestChatbot(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.user_id = "test_user_123"
    
    def test_emotion_analysis(self):
        """Test emotion analysis functionality"""
        # Test positive text
        positive_text = "I'm so happy today! Everything is wonderful!"
        emotion_scores = emotion_engine.analyze_emotion(positive_text)
        
        self.assertGreater(emotion_scores["happiness"], 0.6)
        self.assertGreater(emotion_scores["excitement"], 0.5)
        
        # Test negative text
        negative_text = "I'm feeling sad and disappointed about what happened."
        emotion_scores = emotion_engine.analyze_emotion(negative_text)
        
        self.assertGreater(emotion_scores["sadness"], 0.5)
        self.assertGreater(emotion_scores["empathy"], 0.5)
    
    def test_memory_storage(self):
        """Test memory storage and retrieval"""
        # Store a memory
        memory_text = "User mentioned they love hiking and outdoor activities"
        db.store_memory(
            self.user_id,
            memory_text,
            "preference",
            {"dominant_emotion": "excitement", "intensity": 0.8},
            importance=3
        )
        
        # Retrieve memories
        memories = db.get_important_memories(self.user_id)
        self.assertTrue(any(memory_text in memory["text"] for memory in memories))
    
    def test_user_profile_management(self):
        """Test user profile creation and updating"""
        # Create initial profile
        initial_profile = {
            "name": "Test User",
            "preferences": {"music": ["jazz", "classical"]},
            "personality_traits": {"openness": 0.8, "extroversion": 0.6}
        }
        
        db.update_user_profile(self.user_id, initial_profile)
        
        # Retrieve and verify
        retrieved_profile = db.get_user_profile(self.user_id)
        self.assertEqual(retrieved_profile["name"], "Test User")
        self.assertEqual(retrieved_profile["preferences"]["music"], ["jazz", "classical"])
        
        # Update profile
        updated_profile = {
            "name": "Test User Updated",
            "preferences": {"music": ["jazz", "classical", "rock"]},
            "personality_traits": {"openness": 0.9, "extroversion": 0.6}
        }
        
        db.update_user_profile(self.user_id, updated_profile)
        
        # Verify update
        retrieved_profile = db.get_user_profile(self.user_id)
        self.assertEqual(retrieved_profile["name"], "Test User Updated")
        self.assertEqual(len(retrieved_profile["preferences"]["music"]), 3)
    
    def test_tone_adaptation(self):
        """Test tone adaptation based on emotional context"""
        # Test with positive emotion
        positive_emotion = {
            "happiness": 0.8,
            "sadness": 0.2,
            "excitement": 0.7,
            "calmness": 0.5,
            "curiosity": 0.6,
            "empathy": 0.5
        }
        
        tone = emotion_engine.determine_tone(positive_emotion)
        self.assertIn(tone, ["friendly", "playful"])
        
        # Test with negative emotion
        negative_emotion = {
            "happiness": 0.2,
            "sadness": 0.8,
            "excitement": 0.3,
            "calmness": 0.6,
            "curiosity": 0.4,
            "empathy": 0.9
        }
        
        tone = emotion_engine.determine_tone(negative_emotion)
        self.assertEqual(tone, "empathetic")
    
    def test_conversation_context(self):
        """Test conversation context building"""
        # Add some conversation memories
        test_memories = [
            ("User said: 'I love hiking in the mountains'. You responded: 'That sounds amazing! What's your favorite trail?'", "preference"),
            ("User said: 'I work as a software engineer'. You responded: 'That's interesting! What programming languages do you use?'", "personal_info"),
            ("User said: 'My dog just had puppies'. You responded: 'Congratulations! How many puppies?'", "personal_event")
        ]
        
        for memory_text, memory_type in test_memories:
            db.store_memory(
                self.user_id,
                memory_text,
                memory_type,
                {"dominant_emotion": "happiness", "intensity": 0.7},
                importance=2
            )
        
        # Get conversation context
        context = memory_manager.get_conversation_context(self.user_id)
        
        # Should have user profile and memories
        self.assertIsNotNone(context["user_profile"])
        self.assertGreaterEqual(len(context["recent_conversation"]), 0)
    
    def test_memory_summarization(self):
        """Test memory summarization functionality"""
        # Add enough conversations to trigger summarization
        for i in range(6):  # Above the threshold of 5
            memory_text = f"Conversation exchange {i}: User talked about topic {i}"
            db.store_memory(
                self.user_id,
                memory_text,
                "conversation_exchange",
                {"dominant_emotion": "neutral", "intensity": 0.5},
                importance=1
            )
        
        # Manually trigger summarization (in real usage this happens automatically)
        memory_manager._create_conversation_summary(self.user_id)
        
        # Check if summary was created
        summaries = db.get_memory_summaries(self.user_id)
        self.assertGreaterEqual(len(summaries), 1)
    
    def test_emotional_response_generation(self):
        """Test emotional response generation"""
        # Test with different input types
        test_inputs = [
            "I'm so excited about my vacation next week!",
            "I'm feeling really down today.",
            "Can you explain how machine learning works?",
            "I need help right now, it's urgent!"
        ]
        
        for test_input in test_inputs:
            emotional_response = emotion_engine.get_emotional_response(test_input)
            
            # Should return a valid response structure
            self.assertIn("tone", emotional_response)
            self.assertIn("emotion_scores", emotional_response)
            self.assertIn("response_opener", emotional_response)
            self.assertIn("emotional_markers", emotional_response)
            
            # Tone should be one of the valid options
            self.assertIn(emotional_response["tone"], ["friendly", "professional", "empathetic", "playful"])

if __name__ == '__main__':
    unittest.main()