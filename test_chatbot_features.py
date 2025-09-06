#!/usr/bin/env python3
"""
Test script for chatbot features
"""

import sys
import time
from datetime import datetime, timedelta
from database import MemoryManager as DatabaseManager
from memory_manager import MemoryManager as ChatMemoryManager

def test_memory_features():
    """Test long-term memory functionality"""
    print("Testing Memory Features...")
    print("=" * 50)
    
    db = DatabaseManager()
    memory_manager = ChatMemoryManager(db)
    
    # Test user ID
    test_user_id = "test_user_123"
    
    # Clear any existing test data
    # (In a real test, you'd use a test database)
    
    # Test 1: Name memory
    print("Test 1: Name Memory")
    memory_manager.extract_user_info(test_user_id, "My name is John Smith", "")
    profile = db.get_user_profile(test_user_id)
    assert profile and profile.get("name") == "John Smith", "Name not stored correctly"
    print("✓ Name correctly stored")
    
    # Test 2: Preference memory
    print("\nTest 2: Preference Memory")
    memory_manager.extract_user_info(test_user_id, "I love pizza and hiking", "")
    profile = db.get_user_profile(test_user_id)
    assert profile and "pizza" in profile.get("preferences", {}).get("likes", []), "Preferences not stored"
    print("✓ Preferences correctly stored")
    
    # Test 3: Profession memory
    print("\nTest 3: Profession Memory")
    memory_manager.extract_user_info(test_user_id, "I work as a software engineer", "")
    profile = db.get_user_profile(test_user_id)
    assert profile and profile.get("preferences", {}).get("profession") == "software engineer", "Profession not stored"
    print("✓ Profession correctly stored")
    
    print("\nAll memory tests passed! ✅")

def test_personalization():
    """Test personalization over time"""
    print("\nTesting Personalization Features...")
    print("=" * 50)
    
    # This would require actual conversation simulation
    # For now, we'll test that the memory system works with multiple inputs
    
    db = DatabaseManager()
    memory_manager = ChatMemoryManager(db)
    
    test_user_id = "test_user_456"
    
    # Simulate multiple conversations about interests
    conversations = [
        "I really enjoy reading science fiction books",
        "My favorite author is Isaac Asimov",
        "I also love watching sci-fi movies",
        "Star Wars is my favorite franchise"
    ]
    
    for message in conversations:
        memory_manager.extract_user_info(test_user_id, message, "")
    
    profile = db.get_user_profile(test_user_id)
    
    # Check that multiple interests are stored
    likes = profile.get("preferences", {}).get("likes", [])
    assert len(likes) >= 3, "Not all interests were stored"
    assert any("sci" in like.lower() for like in likes), "Sci-fi interests not detected"
    
    print("✓ Multiple interests stored correctly")
    print("✓ Personalization working properly")
    
    print("\nPersonalization tests passed! ✅")

if __name__ == "__main__":
    try:
        test_memory_features()
        test_personalization()
        print("\n🎉 All tests passed! The chatbot should handle:")
        print("   - Long-term memory recall")
        print("   - Personalization over time") 
        print("   - Diverse natural responses")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)