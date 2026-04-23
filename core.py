import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            cls._instance.cursor = cls._instance.conn.cursor()
        return cls._instance
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            logger.error(f"Database error: {e}, query: {query}")
            self.conn.rollback()
            raise
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict]:
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = ()) -> List[Dict]:
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table: str, data: Dict) -> int:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(query, tuple(data.values()))
        return self.cursor.lastrowid
    
    def update(self, table: str, data: Dict, where: str, params: tuple) -> int:
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        self.execute(query, tuple(data.values()) + params)
        return self.cursor.rowcount
    
    def delete(self, table: str, where: str, params: tuple) -> int:
        query = f"DELETE FROM {table} WHERE {where}"
        self.execute(query, params)
        return self.cursor.rowcount
    
    def close(self):
        self.conn.close()

db = Database()