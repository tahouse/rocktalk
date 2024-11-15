from datetime import datetime
from typing import List, Protocol

from models.interfaces import ChatMessage, ChatSession


class StorageInterface(Protocol):
    """Protocol defining the interface for chat storage implementations"""

    def store_session(self, session: ChatSession) -> None:
        """Store a new chat session"""
        ...

    def save_message(self, message: ChatMessage) -> None:
        """Save a message to a chat session"""
        ...

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session"""
        ...

    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by content or title"""
        ...

    def get_active_sessions_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[ChatSession]:
        """Get sessions that have messages within the date range"""
        ...

    def get_session_info(self, session_id: str) -> ChatSession:
        """Get detailed information about a specific session"""
        ...

    def delete_message(self, session_id: str, index: int) -> None:
        """Delete a specific message by its index.

        Args:
            session_id: ID of the session containing the message
            index: Index of the message to delete
        """
        ...
        # TODO, not ideal to delete message based on datetime, lets use an index instead. Requires modifying the ChatMessage type to hold this index

    def delete_messages_from_index(self, session_id: str, from_index: int) -> None:
        """Delete all messages with index >= from_index for the given session."""
        ...

    def delete_session(self, session_id: str) -> None:
        """Delete a session and its messages"""
        ...

    def delete_all_sessions(self) -> None:
        """Delete all chat sessions and their messages"""
        ...

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get most recently active sessions"""
        ...

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename a chat session"""
        ...
