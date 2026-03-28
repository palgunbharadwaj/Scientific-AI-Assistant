"""
Database Service — SQLAlchemy with SQLite.
Stores query history, user sessions, and audit metadata.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

# ─── Try SQLAlchemy ──────────────────────────────────────────────────────────
try:
    from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean
    from sqlalchemy.orm import DeclarativeBase, sessionmaker

    engine = create_engine("sqlite:///./scientific_assistant.db", echo=False)

    class Base(DeclarativeBase):
        pass

    class QueryLog(Base):
        __tablename__ = "query_logs"
        id: str = Column(String, primary_key=True)
        username: str = Column(String, nullable=False)
        agent: str = Column(String, nullable=False)
        query: str = Column(Text, nullable=False)
        flagged: bool = Column(Boolean, default=False)
        timestamp = Column(DateTime, default=datetime.utcnow)

        def __init__(self, id: str, username: str, agent: str, query: str, flagged: bool = False, **kwargs):
            self.id = id
            self.username = username
            self.agent = agent
            self.query = query
            self.flagged = flagged

    class AuditLog(Base):
        __tablename__ = "audit_logs"
        id: str = Column(String, primary_key=True)
        event_type: str = Column(String, nullable=False)
        username: str = Column(String, nullable=False)
        details: str = Column(Text, nullable=True)
        timestamp = Column(DateTime, default=datetime.utcnow)

        def __init__(self, id: str, event_type: str, username: str, details: Optional[str] = None, **kwargs):
            self.id = id
            self.event_type = event_type
            self.username = username
            self.details = details

    class User(Base):
        __tablename__ = "users"
        username: str = Column(String, primary_key=True)
        hashed_password: str = Column(String, nullable=False)
        role: str = Column(String, nullable=False)

        def __init__(self, username, hashed_password, role, **kwargs):
            self.username = username
            self.hashed_password = hashed_password
            self.role = role

    class ChatMessage(Base):
        __tablename__ = "chat_history"
        id = Column(String, primary_key=True)
        session_id = Column(String, nullable=False, index=True)
        role = Column(String, nullable=False)  # 'user' or 'model'
        content = Column(Text, nullable=False)
        timestamp = Column(DateTime, default=datetime.utcnow)

        def __init__(self, id, session_id, role, content, **kwargs):
            self.id = id
            self.session_id = session_id
            self.role = role
            self.content = content

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    DB_AVAILABLE = True
    print("[Database] SQLite database initialized.")

except ImportError:
    DB_AVAILABLE = False
    SessionLocal = None
    print("[Database] SQLAlchemy not installed. DB features disabled.")


def get_db_session():
    if not DB_AVAILABLE:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


FAKE_USERS_DB: dict = {}

def get_user_record(username: str) -> Optional[dict]:
    if not DB_AVAILABLE:
        return FAKE_USERS_DB.get(username)
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.username == username).first()
        if u:
            return {"username": u.username, "hashed_password": u.hashed_password, "role": u.role}
        return None
    finally:
        db.close()

def create_user_record(username: str, hashed_password: str, role: str) -> bool:
    if not DB_AVAILABLE:
        if username in FAKE_USERS_DB:
            return False
        FAKE_USERS_DB[username] = {"username": username, "hashed_password": hashed_password, "role": role}
        return True
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == username).first()
        if exists: return False
        db.add(User(username=username, hashed_password=hashed_password, role=role))
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def update_user_password(username: str, new_hashed: str) -> bool:
    if not DB_AVAILABLE:
        if username not in FAKE_USERS_DB:
            return False
        FAKE_USERS_DB[username]["hashed_password"] = new_hashed
        return True
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.username == username).first()
        if not u: return False
        u.hashed_password = new_hashed
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


def log_query_to_db(
    query_id: str,
    username: str,
    agent: str,
    query: str,
    flagged: bool = False,
):
    """Persist a query record to the SQLite database."""
    if not DB_AVAILABLE:
        return
    db = SessionLocal()
    try:
        record = QueryLog(
            id=query_id,
            username=username,
            agent=agent,
            query=query,
            flagged=flagged,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Database] Failed to log query: {e}")
    finally:
        db.close()


def get_chat_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve the last N messages for a given session."""
    if not DB_AVAILABLE:
        return []
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
        # Cap at limit for synthesis
        messages = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in messages]
    finally:
        db.close()

def add_chat_message(session_id: str, role: str, content: str):
    """Save a new message to the chat history."""
    if not DB_AVAILABLE:
        return
    import uuid
    db = SessionLocal()
    try:
        msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(msg)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Database] Failed to add chat message: {e}")
    finally:
        db.close()
