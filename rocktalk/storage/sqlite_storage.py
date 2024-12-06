import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

from config.settings import LLMConfig
from models.interfaces import ChatMessage, ChatSession, ChatTemplate
from models.storage_interface import StorageInterface
from utils.datetime_utils import format_datetime, parse_datetime


class SQLiteChatStorage(StorageInterface):
    def __init__(self, db_path: str = "chat_database.db") -> None:
        # Ensure database directory exists
        Path(db_path).parent.mkdir(exist_ok=True, parents=True)
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create a new connection with row factory for dict results"""
        try:
            # Connect to database (creates file if it doesn't exist)
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to database at {self.db_path}: {str(e)}"
            )

    def init_db(self) -> None:
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_active TIMESTAMP NOT NULL,
                    config TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_index INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    UNIQUE(session_id, message_index)  -- Ensure unique indexes per session
                );

                CREATE TABLE IF NOT EXISTS chat_templates (
                        template_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL, 
                        config TEXT NOT NULL
                    );

                -- Indexes for better search performance

                CREATE INDEX IF NOT EXISTS idx_sessions_last_active
                ON sessions(last_active);

                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages(session_id, message_index);

                CREATE INDEX IF NOT EXISTS idx_messages_timestamp
                ON messages(timestamp);

                CREATE INDEX IF NOT EXISTS idx_templates_name 
                ON chat_templates(name);
            """
            )
            self.initialize_preset_templates()

    def store_session(self, session: ChatSession) -> None:

        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                (session_id, title, created_at, last_active, config)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    session.session_id,
                    session.title,
                    format_datetime(session.created_at),
                    format_datetime(session.last_active),
                    session.config.model_dump_json(),
                ),
            )

    def update_session(self, session: ChatSession) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET title = ?, last_active = ?, config = ?
                WHERE session_id = ?
            """,
                (
                    session.title,
                    format_datetime(session.last_active),
                    json.dumps(session.config.model_dump()),
                    session.session_id,
                ),
            )

    def save_message(self, message: ChatMessage) -> None:
        """Save a message to a chat session and update last_active"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages
                (session_id, role, content, message_index, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.session_id,
                    message.role,
                    json.dumps(message.content),
                    message.index,
                    format_datetime(message.created_at),
                ),
            )
            # Update session's last_active timestamp
            conn.execute(
                """
                UPDATE sessions
                SET last_active = ?
                WHERE session_id = ?
            """,
                (format_datetime(message.created_at), message.session_id),
            )

    def delete_messages_from_index(self, session_id: str, from_index: int) -> None:
        """Delete all messages with index >= from_index for the given session."""
        with self.get_connection() as conn:
            conn.execute(
                """
                DELETE FROM messages
                WHERE session_id = ? AND message_index >= ?
                """,
                (session_id, from_index),
            )

    def delete_message(self, session_id: str, index: int) -> None:
        """Delete a specific message by its index from a chat session."""
        with self.get_connection() as conn:
            try:
                # Start a transaction
                conn.execute("BEGIN TRANSACTION")

                # Delete the specific message
                result = conn.execute(
                    """
                    DELETE FROM messages
                    WHERE session_id = ? AND message_index = ?
                    """,
                    (session_id, index),
                )

                # Check if a message was actually deleted
                if result.rowcount == 0:
                    raise ValueError(
                        f"No message found with index {index} in session {session_id}"
                    )

                # Update indexes of subsequent messages
                conn.execute(
                    """
                    UPDATE messages
                    SET message_index = message_index - 1
                    WHERE session_id = ? AND message_index > ?
                    """,
                    (session_id, index),
                )

                # Update session's last_active timestamp
                conn.execute(
                    """
                    UPDATE sessions
                    SET last_active = ?
                    WHERE session_id = ?
                    """,
                    (format_datetime(datetime.now()), session_id),
                )

                # Commit the transaction
                conn.execute("COMMIT")
            except Exception as e:
                # If any error occurs, rollback the transaction
                conn.execute("ROLLBACK")
                raise e

    def _deserialize_message(self, row: sqlite3.Row) -> ChatMessage:
        """Deserialize a message from the database row"""
        return ChatMessage(
            session_id=row["session_id"],
            role=row["role"],
            content=json.loads(row["content"]),
            index=row["message_index"],
            created_at=parse_datetime(row["timestamp"]),
        )

    def _deserialize_session(self, row: sqlite3.Row) -> ChatSession:
        """Deserialize a session from the database row"""
        session_data = dict(row)
        return ChatSession(
            session_id=session_data["session_id"],
            title=session_data["title"],
            created_at=parse_datetime(session_data["created_at"]),
            last_active=parse_datetime(session_data["last_active"]),
            config=LLMConfig.model_validate_json(session_data["config"], strict=True),
        )

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY timestamp
            """,
                (session_id,),
            )
            return [self._deserialize_message(row) for row in cursor.fetchall()]

    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by content or title"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT
                    s.*,
                    MAX(m.timestamp) as last_message,
                    COUNT(m.message_id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                WHERE m.content LIKE ?
                OR s.title LIKE ?
                GROUP BY s.session_id
                ORDER BY MAX(m.timestamp) DESC NULLS LAST
            """,
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            return [self._deserialize_session(row) for row in cursor.fetchall()]

    def get_active_sessions_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[ChatSession]:
        """Get sessions that have messages within the date range"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT
                    s.*,
                    MIN(m.timestamp) as first_message,
                    MAX(m.timestamp) as last_message,
                    COUNT(m.message_id) as message_count
                FROM sessions s
                INNER JOIN messages m ON s.session_id = m.session_id
                WHERE m.timestamp BETWEEN ? AND ?
                GROUP BY s.session_id
                ORDER BY MAX(m.timestamp) DESC
            """,
                (format_datetime(start_date), format_datetime(end_date)),
            )
            return [self._deserialize_session(row) for row in cursor.fetchall()]

    def get_session(self, session_id: str) -> ChatSession:
        """Get a specific chat session"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sessions
                WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._deserialize_session(row)
            else:
                raise ValueError(f"No session found with id {session_id}")

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently active sessions"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT s.*,
                    (SELECT COUNT(*) FROM messages WHERE messages.session_id = s.session_id) as message_count,
                    (SELECT MIN(timestamp) FROM messages WHERE messages.session_id = s.session_id) as first_message,
                    (SELECT MAX(timestamp) FROM messages WHERE messages.session_id = s.session_id) as last_message
                FROM sessions s
                ORDER BY last_active DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [self._deserialize_session(row) for row in cursor.fetchall()]

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a chat session"""
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET title = ?, last_active = ?
                WHERE session_id = ?
            """,
                (new_title, format_datetime(datetime.now()), session_id),
            )

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages"""
        with self.get_connection() as conn:
            try:
                # Start a transaction
                conn.execute("BEGIN TRANSACTION")

                # Delete all messages associated with the session
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

                # Delete the session itself
                result = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?", (session_id,)
                )

                # Check if a session was actually deleted
                if result.rowcount == 0:
                    raise ValueError(f"No session found with id {session_id}")

                # Commit the transaction
                conn.execute("COMMIT")
            except Exception as e:
                # If any error occurs, rollback the transaction
                conn.execute("ROLLBACK")
                raise e  # Re-raise the exception after rollback

    def delete_all_sessions(self) -> None:
        """Delete all chat sessions and their messages"""
        with self.get_connection() as conn:
            try:
                # Start a transaction
                conn.execute("BEGIN TRANSACTION")

                # Delete all messages first (due to foreign key constraint)
                conn.execute("DELETE FROM messages")

                # Delete all sessions
                conn.execute("DELETE FROM sessions")

                # Commit the transaction
                conn.execute("COMMIT")
            except Exception as e:
                # If any error occurs, rollback the transaction
                conn.execute("ROLLBACK")
                raise RuntimeError(f"Failed to delete all sessions: {str(e)}")

    def _deserialize_template(self, row: sqlite3.Row) -> ChatTemplate:
        """Deserialize a template from the database row"""
        return ChatTemplate(
            template_id=row["template_id"],
            name=row["name"],
            description=row["description"],
            config=LLMConfig.model_validate_json(row["config"], strict=True),
        )

    def store_chat_template(self, template: ChatTemplate) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_templates 
                (template_id, name, description, config)
                VALUES (?, ?, ?, ?)
                """,
                (
                    template.template_id,
                    template.name,
                    template.description,
                    template.config.model_dump_json(),
                ),
            )

    def initialize_preset_templates(self) -> None:
        """Initialize default preset templates if they don't exist"""
        presets = super().get_default_templates()

        with self.get_connection() as conn:
            for template in presets:
                # Check if preset already exists
                cursor = conn.execute(
                    "SELECT 1 FROM chat_templates WHERE name = ?",
                    (template.name,),
                )
                if not cursor.fetchone():
                    self.store_chat_template(template)

    def get_chat_template(self, template_id: str) -> ChatTemplate:
        """Get a specific chat template"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM chat_templates 
                WHERE template_id = ?
                """,
                (template_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"No template found with id {template_id}")
            return self._deserialize_template(row)

    def get_chat_templates(self) -> List[ChatTemplate]:
        """Get all chat templates"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM chat_templates 
                ORDER BY name
                """
            )
            return [self._deserialize_template(row) for row in cursor.fetchall()]

    def update_chat_template(self, template: ChatTemplate) -> None:
        """Update an existing chat template"""
        with self.get_connection() as conn:
            result = conn.execute(
                """
                UPDATE chat_templates
                SET name = ?, description = ?, config = ?
                WHERE template_id = ?
                """,
                (
                    template.name,
                    template.description,
                    template.config.model_dump_json(),
                    template.template_id,
                ),
            )
            if result.rowcount == 0:
                raise ValueError(f"No template found with id {template.template_id}")

    def delete_chat_template(self, template_id: str) -> None:
        """Delete a chat template"""
        with self.get_connection() as conn:
            result = conn.execute(
                """
                DELETE FROM chat_templates 
                WHERE template_id = ?
                """,
                (template_id,),
            )
            if result.rowcount == 0:
                raise ValueError(f"No template found with id {template_id}")
