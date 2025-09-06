import sqlite3
import json
from datetime import datetime, timedelta
from config import Config
import logging
import random
logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.setup_sqlite()
        logger.info("Using SQLite for memory storage")
    
    def setup_sqlite(self):
        """Setup SQLite database for all memory storage"""
        self.conn = sqlite3.connect(Config.SQLITE_DB, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Create tables with proper schema
        tables = [
            '''CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                preferences TEXT,
                personality_traits TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS conversation_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                memory_text TEXT,
                memory_type TEXT,
                emotional_context TEXT,
                importance INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS memory_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                summary_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS recent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                memory_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )'''
        ]
        
        for table in tables:
            cursor.execute(table)
        
        # Create indexes for better performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_user_memories ON conversation_memories(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_recent ON recent_memories(user_id, created_at)',
            'CREATE INDEX IF NOT EXISTS idx_user_summaries ON memory_summaries(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_memory_cleanup ON conversation_memories(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_memory_importance ON conversation_memories(importance)',
            'CREATE INDEX IF NOT EXISTS idx_user_profile_updated ON user_profiles(updated_at)'
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        self.conn.commit()
    
    def cleanup_old_memories(self):
        """Clean up old memories to maintain performance but keep important ones"""
        try:
            cursor = self.conn.cursor()
            # Keep important memories longer
            cutoff_date_important = (datetime.now() - timedelta(days=Config.LONG_TERM_MEMORY_DAYS * 2)).strftime('%Y-%m-%d %H:%M:%S')
            cutoff_date_normal = (datetime.now() - timedelta(days=Config.LONG_TERM_MEMORY_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Delete old normal importance memories
            cursor.execute(
                "DELETE FROM conversation_memories WHERE created_at < ? AND importance < 2",
                (cutoff_date_normal,)
            )
            
            # Delete old important memories (keep these longer)
            cursor.execute(
                "DELETE FROM conversation_memories WHERE created_at < ? AND importance >= 2",
                (cutoff_date_important,)
            )
            
            # Clean up recent memories
            cursor.execute(
                "DELETE FROM recent_memories WHERE created_at < ?",
                (cutoff_date_normal,)
            )
            
            self.conn.commit()
            logger.info("Cleaned up old memories")
        except Exception as e:
            logger.error(f"Error cleaning up memories: {e}")
    
    def get_user_profile(self, user_id):
        """Retrieve user profile from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, preferences, personality_traits, updated_at FROM user_profiles WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    "name": result["name"],
                    "preferences": json.loads(result["preferences"]) if result["preferences"] else {},
                    "personality_traits": json.loads(result["personality_traits"]) if result["personality_traits"] else {},
                    "last_updated": result["updated_at"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id, updates):
        """Update or create user profile with enhanced preference handling"""
        try:
            cursor = self.conn.cursor()
            
            # Check if user exists and get current profile
            cursor.execute("SELECT preferences, personality_traits FROM user_profiles WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            # Merge preferences if they exist
            current_prefs = {}
            current_traits = {}
            
            if existing:
                if existing["preferences"]:
                    try:
                        current_prefs = json.loads(existing["preferences"])
                    except json.JSONDecodeError:
                        current_prefs = {}
                if existing["personality_traits"]:
                    try:
                        current_traits = json.loads(existing["personality_traits"])
                    except json.JSONDecodeError:
                        current_traits = {}
            
            # Update preferences with new values
            if "preferences" in updates:
                for key, value in updates["preferences"].items():
                    if key in current_prefs and isinstance(current_prefs[key], list) and isinstance(value, list):
                        # Merge lists, avoiding duplicates
                        current_prefs[key] = list(set(current_prefs[key] + value))
                    else:
                        current_prefs[key] = value
            
            # Update personality traits
            if "personality_traits" in updates:
                for key, value in updates["personality_traits"].items():
                    current_traits[key] = value
            
            set_clauses = []
            params = []
            
            if "name" in updates:
                set_clauses.append("name = ?")
                params.append(updates["name"])
            
            if current_prefs:
                set_clauses.append("preferences = ?")
                params.append(json.dumps(current_prefs))
            
            if current_traits:
                set_clauses.append("personality_traits = ?")
                params.append(json.dumps(current_traits))
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            if existing:
                query = f"UPDATE user_profiles SET {', '.join(set_clauses)} WHERE user_id = ?"
                cursor.execute(query, params)
            else:
                cursor.execute(
                    "INSERT INTO user_profiles (user_id, name, preferences, personality_traits) VALUES (?, ?, ?, ?)",
                    (
                        user_id,
                        updates.get("name", ""),
                        json.dumps(current_prefs),
                        json.dumps(current_traits)
                    )
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    def store_memory(self, user_id, memory_text, memory_type, emotional_context, importance=1):
        """Store a new memory for the user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_memories (user_id, memory_text, memory_type, emotional_context, importance) VALUES (?, ?, ?, ?, ?)",
                (user_id, memory_text, memory_type, json.dumps(emotional_context), importance)
            )
            
            # Store in recent memories with batch cleanup
            memory_data = {
                "text": memory_text,
                "type": memory_type,
                "emotional_context": emotional_context,
                "timestamp": datetime.now().isoformat()
            }
            cursor.execute(
                "INSERT INTO recent_memories (user_id, memory_data) VALUES (?, ?)",
                (user_id, json.dumps(memory_data))
            )
            
            # Batch cleanup every 10 inserts
            if random.random() < 0.1:  # 10% chance to cleanup
                cursor.execute(
                    "DELETE FROM recent_memories WHERE id NOT IN ("
                    "SELECT id FROM recent_memories "
                    "WHERE user_id = ? "
                    "ORDER BY created_at DESC "
                    "LIMIT 100"  # Increased limit for better context
                    ") AND user_id = ?",
                    (user_id, user_id)
                )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def get_recent_memories(self, user_id, limit=10):
        """Get recent memories from SQLite"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT memory_data FROM recent_memories WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            results = cursor.fetchall()
            
            memories = []
            for result in results:
                try:
                    memories.append(json.loads(result["memory_data"]))
                except json.JSONDecodeError:
                    continue
            
            return memories
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            return []
    
    def get_important_memories(self, user_id, limit=5):
        """Get important memories from SQLite"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT memory_text, memory_type, emotional_context FROM conversation_memories WHERE user_id = ? AND importance >= 2 ORDER BY importance DESC, created_at DESC LIMIT ?",
                (user_id, limit)
            )
            results = cursor.fetchall()
            
            memories = []
            for result in results:
                try:
                    memories.append({
                        "text": result["memory_text"],
                        "type": result["memory_type"],
                        "emotional_context": json.loads(result["emotional_context"]) if result["emotional_context"] else {}
                    })
                except json.JSONDecodeError:
                    continue
            
            return memories
        except Exception as e:
            logger.error(f"Error getting important memories: {e}")
            return []
    
    def create_memory_summary(self, user_id, summary_text):
        """Create a summary of recent memories"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memory_summaries (user_id, summary_text) VALUES (?, ?)",
                (user_id, summary_text)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating memory summary: {e}")
            return False
    
    def get_memory_summaries(self, user_id, limit=3):
        """Get memory summaries for a user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT summary_text, created_at FROM memory_summaries WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            results = cursor.fetchall()
            
            return [{"text": result["summary_text"], "created_at": result["created_at"]} for result in results]
        except Exception as e:
            logger.error(f"Error getting memory summaries: {e}")
            return []
    
    def get_conversation_history(self, user_id, days=7):
        """Get conversation history for a specific time period"""
        try:
            cursor = self.conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                "SELECT memory_text, created_at FROM conversation_memories WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC",
                (user_id, cutoff_date)
            )
            results = cursor.fetchall()
            
            return [{"text": result["memory_text"], "timestamp": result["created_at"]} for result in results]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []