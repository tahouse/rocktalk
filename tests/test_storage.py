import os
import random
from datetime import datetime, timedelta
from typing import Dict, List

from models.interfaces import ChatMessage, ChatSession, LLMConfig, LLMParameters
from storage.sqlite_storage import SQLiteChatStorage
from utils.datetime_utils import format_datetime, parse_datetime_string


class TestDataGenerator:
    def __init__(self, reference_date: datetime = datetime(2024, 10, 22)):
        """
        Initialize the generator with a reference date (default: Oct 22, 2024)
        All dates will be relative to this reference date
        """
        self.reference_date = reference_date
        self.default_config = LLMConfig(
            bedrock_model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            parameters=LLMParameters(
                temperature=0.7, max_output_tokens=4096, top_p=0.9
            ),
        )
        self.sample_conversations = {
            "tech_support": [
                ("user", "How do I fix my printer?"),
                (
                    "assistant",
                    "Let's try some basic troubleshooting. Is it connected and powered on?",
                ),
                ("user", "Yes, but it's not printing"),
                (
                    "assistant",
                    "Try turning it off and on, then check if there are any error messages.",
                ),
            ],
            "python_help": [
                ("user", "Can you help me with Python lists?"),
                (
                    "assistant",
                    "Sure! Lists are ordered collections in Python. What would you like to know?",
                ),
                ("user", "How do I add items?"),
                (
                    "assistant",
                    "You can use .append() to add single items or .extend() for multiple items.",
                ),
            ],
            "casual_chat": [
                ("user", "How's your day going?"),
                ("assistant", "I'm functioning well! How can I help you today?"),
                ("user", "Just wanted to chat"),
                (
                    "assistant",
                    "That's nice! I'm always happy to engage in conversation.",
                ),
            ],
            "book_recommendation": [
                ("user", "Can you recommend a good sci-fi book?"),
                ("assistant", "Have you read 'Project Hail Mary' by Andy Weir?"),
                ("user", "No, what's it about?"),
                (
                    "assistant",
                    "It's about a lone astronaut who wakes up in space with amnesia. It's full of science and problem-solving.",
                ),
            ],
        }

    def generate_date_points(self) -> List[Dict]:
        """
        Generate a list of dates with their descriptions
        Returns dates formatted according to our standard format
        """
        ref_date = self.reference_date
        return [
            {
                "date": format_datetime(ref_date - timedelta(days=3)),
                "desc": "Recent - Few days ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(weeks=2)),
                "desc": "Recent - Couple weeks ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=45)),
                "desc": "Month and a half ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=90)),
                "desc": "Three months ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=180)),
                "desc": "Six months ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=270)),
                "desc": "Nine months ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=365)),
                "desc": "One year ago",
            },
            {
                "date": format_datetime(ref_date - timedelta(days=456)),
                "desc": "15 months ago",
            },
        ]

    def create_test_database(self, db_path: str = "test_chat_database.db"):
        """
        Create a test database with sample conversations using standardized datetime format
        """
        if os.path.exists(db_path):
            os.remove(db_path)

        storage = SQLiteChatStorage(db_path)
        dates = self.generate_date_points()

        for date_info in dates:
            base_datetime = parse_datetime_string(date_info["date"])
            date_str = date_info["date"]
            desc = date_info["desc"]

            # Create 1-2 sessions per date point
            for session_num in range(random.randint(1, 2)):
                conv_type = random.choice(list(self.sample_conversations.keys()))
                conversation = self.sample_conversations[conv_type]

                # Create session with formatted timestamp
                session = ChatSession(
                    title=f"Chat {date_str[:10]}- {conv_type}",
                    created_at=base_datetime,
                    last_active=base_datetime,
                    config=self.default_config,
                )
                storage.store_session(session)

                # Add messages with timestamps spaced a few minutes apart
                message_time = base_datetime
                for idx, (role, content) in enumerate(conversation):
                    message = ChatMessage(
                        session_id=session.session_id,
                        role=role,
                        content=content,
                        index=idx,
                        created_at=message_time,
                    )
                    storage.save_message(message)
                    message_time += timedelta(minutes=random.randint(1, 5))

        return storage


def create_sample_database(
    reference_date: datetime | None = None, db_path: str = "test_chat_database.db"
) -> SQLiteChatStorage:
    """
    Convenience function to create a sample database
    """
    if reference_date is None:
        reference_date = datetime(2024, 12, 4)  # Default reference date

    generator = TestDataGenerator(reference_date)
    return generator.create_test_database(db_path)


if __name__ == "__main__":
    import logging
    import traceback

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting test database creation...")
        storage = create_sample_database(db_path="chat_database.db")
        logger.info("Default test database created successfully!")

    except Exception as e:
        logger.error("Error creating test database: %s", str(e))
        logger.error("Full stack trace:")
        logger.error(traceback.format_exc())
        raise
