from emotion_engine import EmotionEngine

# Test the emotion engine
engine = EmotionEngine()

test_messages = [
    "I'm so happy today! Everything is wonderful!",
    "I'm feeling really sad and disappointed...",
    "Can you explain how this works? I'm curious.",
    "I NEED HELP RIGHT NOW!!! IT'S URGENT!",
    "Hello, how are you doing today?"
]

print("Testing Emotion Engine:")
print("=" * 50)

for message in test_messages:
    analysis = engine.analyze_emotion(message)
    response = engine.get_emotional_response(message)
    
    print(f"Message: {message}")
    print(f"Emotion scores: {analysis}")
    print(f"Recommended tone: {response['tone']}")
    print(f"Response opener: {response['response_opener']}")
    print(f"Emotional markers: {response['emotional_markers']}")
    print("-" * 50)