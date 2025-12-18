"""
Database models for user-based scraping system
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from src.shared.log import logger
import os


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = "data/scraper.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                pushover_api_token TEXT NOT NULL,
                pushover_user_key TEXT NOT NULL,
                filters TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                notify_on_first_scrape INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Results table - stores latest results per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                listing_hash TEXT NOT NULL,
                listing_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, listing_hash)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_results_user_id ON user_results(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_results_hash ON user_results(listing_hash)")
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")


class UserManager:
    """User management operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_or_update_user(
        self,
        user_id: str,
        pushover_api_token: str,
        pushover_user_key: str,
        filters: Dict,
        notify_on_first_scrape: bool = False
    ) -> bool:
        """Create or update a user. If filters changed, clears stored results and sets notify flag."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            filters_json = json.dumps(filters)
            
            # Check if user exists and if filters changed
            cursor.execute("SELECT filters FROM users WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            filters_changed = False
            
            if existing:
                existing_filters = json.loads(existing['filters'])
                # Compare filters (normalize for comparison)
                existing_filters_normalized = json.dumps(existing_filters, sort_keys=True)
                new_filters_normalized = json.dumps(filters, sort_keys=True)
                filters_changed = existing_filters_normalized != new_filters_normalized
            
            cursor.execute("""
                INSERT INTO users (user_id, pushover_api_token, pushover_user_key, filters, notify_on_first_scrape, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    pushover_api_token = excluded.pushover_api_token,
                    pushover_user_key = excluded.pushover_user_key,
                    filters = excluded.filters,
                    notify_on_first_scrape = excluded.notify_on_first_scrape,
                    updated_at = CURRENT_TIMESTAMP,
                    is_active = 1
            """, (user_id, pushover_api_token, pushover_user_key, filters_json, 1 if notify_on_first_scrape else 0))
            
            # If filters changed, clear stored results and set notify flag
            if filters_changed:
                logger.info(f"Filters changed for user {user_id}. Clearing stored results and enabling notification for next scrape.")
                # Clear stored results
                cursor.execute("DELETE FROM user_results WHERE user_id = ?", (user_id,))
                # Set notify_on_first_scrape to True for the next scrape
                cursor.execute("UPDATE users SET notify_on_first_scrape = 1 WHERE user_id = ?", (user_id,))
            
            conn.commit()
            logger.info(f"User {user_id} created/updated")
            return True
        except Exception as e:
            logger.error(f"Error creating/updating user {user_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ? AND is_active = 1", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'user_id': row['user_id'],
                    'pushover_api_token': row['pushover_api_token'],
                    'pushover_user_key': row['pushover_user_key'],
                    'filters': json.loads(row['filters']),
                    'notify_on_first_scrape': bool(row['notify_on_first_scrape']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
        finally:
            conn.close()
    
    def get_all_active_users(self) -> List[Dict]:
        """Get all active users"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE is_active = 1")
            users = []
            for row in cursor.fetchall():
                users.append({
                    'user_id': row['user_id'],
                    'pushover_api_token': row['pushover_api_token'],
                    'pushover_user_key': row['pushover_user_key'],
                    'filters': json.loads(row['filters']),
                    'notify_on_first_scrape': bool(row['notify_on_first_scrape']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            return users
        finally:
            conn.close()
    
    def clear_notify_flag(self, user_id: str) -> bool:
        """Clear the notify_on_first_scrape flag after initial notification"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET notify_on_first_scrape = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Cleared notify flag for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing notify flag for user {user_id}: {e}")
            return False
        finally:
            conn.close()
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"User {user_id} deactivated")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


class ResultManager:
    """Result management operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def save_user_results(self, user_id: str, listings: List[Dict]) -> bool:
        """Save or update results for a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete old results for this user
            cursor.execute("DELETE FROM user_results WHERE user_id = ?", (user_id,))
            
            # Track seen hashes to avoid duplicates within the same batch
            seen_hashes = set()
            inserted_count = 0
            
            # Insert new results (skip duplicates within batch)
            for listing in listings:
                listing_hash = listing.get('HASH', '')
                if not listing_hash:
                    logger.warning(f"Listing missing HASH, skipping: {listing.get('Naziv', 'Unknown')}")
                    continue
                
                # Skip if we've already seen this hash in this batch
                if listing_hash in seen_hashes:
                    logger.debug(f"Skipping duplicate hash in batch: {listing_hash}")
                    continue
                
                seen_hashes.add(listing_hash)
                listing_json = json.dumps(listing)
                
                try:
                    cursor.execute("""
                        INSERT INTO user_results (user_id, listing_hash, listing_data)
                        VALUES (?, ?, ?)
                    """, (user_id, listing_hash, listing_json))
                    inserted_count += 1
                except sqlite3.IntegrityError as e:
                    # Handle UNIQUE constraint (shouldn't happen after DELETE, but just in case)
                    logger.warning(f"Duplicate hash {listing_hash} skipped: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Saved {inserted_count} results for user {user_id} (out of {len(listings)} listings)")
            return True
        except Exception as e:
            logger.error(f"Error saving results for user {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_user_results(self, user_id: str) -> List[Dict]:
        """Get stored results for a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT listing_data FROM user_results WHERE user_id = ?", (user_id,))
            results = []
            for row in cursor.fetchall():
                results.append(json.loads(row['listing_data']))
            return results
        finally:
            conn.close()
    
    def compare_results(self, user_id: str, new_listings: List[Dict]) -> List[Dict]:
        """Compare new listings with stored results and return only new ones"""
        stored_results = self.get_user_results(user_id)
        
        if not stored_results:
            # First scrape - return empty list (no notifications)
            return []
        
        # Create set of stored hashes
        stored_hashes = {listing['HASH'] for listing in stored_results}
        
        # Find new listings
        new_listings_filtered = [
            listing for listing in new_listings
            if listing['HASH'] not in stored_hashes
        ]
        
        return new_listings_filtered

