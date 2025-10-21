from typing import Dict, List, Optional
import uuid
from datetime import datetime

class Session:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.search_history = []
        self.last_query = None
        self.created_at = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()

    def add_search(self, query: str, source: str, product_count: int):
        """Add a search to history"""
        self.search_history.append({
            "query": query,
            "source": source,
            "product_count": product_count,
            "timestamp": datetime.now().isoformat()
        })
        self.last_query = query
        self.last_active = datetime.now().isoformat()

    def get_recent_searches(self, limit: int = 5) -> List[Dict]:
        """Get most recent searches"""
        return sorted(
            self.search_history,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]

    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "search_history": self.search_history,
            "last_query": self.last_query,
            "created_at": self.created_at,
            "last_active": self.last_active
        }

class SessionHandler:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def reset_session(self, session_id: Optional[str] = None) -> Session:
        """Reset or create a new session"""
        # If no session_id provided, generate a new one
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create new session
        session = Session(session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            session.last_active = datetime.now().isoformat()
        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        return self.reset_session(session_id)

    def add_search_to_session(self, session_id: str, query: str, source: str, product_count: int):
        """Add search to session history"""
        session = self.get_or_create_session(session_id)
        session.add_search(query, source, product_count)

    def get_recent_searches(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get recent searches for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get_recent_searches(limit)

    def clean_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up inactive sessions older than specified hours"""
        now = datetime.now()
        inactive_sessions = []
        
        for session_id, session in self.sessions.items():
            last_active = datetime.fromisoformat(session.last_active)
            hours_inactive = (now - last_active).total_seconds() / 3600
            
            if hours_inactive >= max_age_hours:
                inactive_sessions.append(session_id)
                
        for session_id in inactive_sessions:
            del self.sessions[session_id]
            
        return len(inactive_sessions)