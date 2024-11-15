"""Chat interface module for handling user-AI conversations with support for text and images."""

from datetime import datetime
from typing import Optional

import streamlit as st
import streamlit.components.v1 as stcomponents
from langchain.schema import BaseMessage, HumanMessage
from models.interfaces import ChatMessage, ChatSession, TurnState
from models.llm import LLMInterface
from storage.storage_interface import StorageInterface
from streamlit_chat_prompt import PromptReturn, prompt

MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"


class ChatInterface:
    """Interface for managing chat interactions between users and AI.

    This class handles the display of chat history, processing of user input,
    generation of AI responses, and management of chat sessions.

    Attributes:
        storage (StorageInterface): Interface for persistent storage of chat data.
        llm (LLMInterface): Interface for the language model providing AI responses.
    """

    def __init__(self, storage: StorageInterface, llm: LLMInterface) -> None:
        """Initialize the chat interface.

        Args:
            storage: Storage interface for persisting chat data.
            llm: Language model interface for generating responses.
        """
        self.storage = storage
        self.llm = llm
        if "turn_state" not in st.session_state:
            st.session_state.turn_state = TurnState.HUMAN_TURN
        if "messages" not in st.session_state:
            st.session_state.messages = []  # List[ChatMessage]
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = None  # str
        if "edit_message_value" not in st.session_state:
            st.session_state.edit_message_value = None  # ChatMessage, PromptReturn

    def render(self) -> None:
        """Render the chat interface and handle the current turn state."""
        self._handle_edit_message()
        self._display_chat_history()
        self._handle_chat_input()
        self._generate_ai_response()

    def _scroll_to_bottom(self) -> None:
        """Scrolls to the bottom of the chat interface.

        This method inserts a div element at the bottom of the chat and uses JavaScript
        to scroll to it, ensuring the most recent messages are visible.
        """
        index = st.session_state.scroll_div_index
        st.markdown(f"""<div id="end-of-chat-{index}"></div>""", unsafe_allow_html=True)

        js = (
            """
        <script>
            function scrollToBottom() {
                // Break out of iframe and get the main window
                const mainWindow = window.parent;
                const endMarker = mainWindow.document.getElementById('"""
            + f"""end-of-chat-{index}"""
            + """');
                
                if (endMarker) {
                    endMarker.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'end'
                    });
                } else {
                    // Fallback to scrolling the whole window
                    mainWindow.scrollTo({
                        top: mainWindow.document.documentElement.scrollHeight,
                        behavior: 'smooth'
                    });
                }
            }
            
            // Call immediately and after a short delay to ensure content is loaded
            scrollToBottom();
            setTimeout(scrollToBottom, 100);
        </script>
        """
        )

        stcomponents.html(js, height=0)

    def _scroll_to_bottom_streaming(self) -> None:
        """Automatically scrolls the chat window during streaming responses.

        This method adds a JavaScript script that handles auto-scrolling behavior during
        message streaming. The scrolling continues until the user manually scrolls,
        at which point auto-scrolling is disabled to respect user control.

        The script implements the following features:
            - Detects user scroll events (both wheel and touch)
            - Automatically scrolls to the latest message every 100ms
            - Stops auto-scrolling if user manually scrolls
            - Automatically cleans up after 30 seconds

        The scrolling behavior is implemented using smooth scrolling for better user
        experience and targets the last markdown element in the chat window.
        """
        # Add scroll script with user interaction detection
        js = """
        <script>
            let userHasScrolled = false;
            let scrollInterval;

            // Detect user scroll
            window.parent.addEventListener('wheel', function() {
                userHasScrolled = true;
                if (scrollInterval) {
                    clearInterval(scrollInterval);
                }
            }, { passive: true });

            window.parent.addEventListener('touchmove', function() {
                userHasScrolled = true;
                if (scrollInterval) {
                    clearInterval(scrollInterval);
                }
            }, { passive: true });

            function keepInView() {
                if (!userHasScrolled) {
                    const markdowns = window.parent.document.querySelectorAll('.stMarkdown');
                    if (markdowns.length > 0) {
                        const lastMarkdown = markdowns[markdowns.length - 1];
                        lastMarkdown.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'end' 
                        });
                    }
                }
            }
            
            // Start auto-scroll only if user hasn't manually scrolled
            scrollInterval = setInterval(keepInView, 100);
            
            // Clear interval after 30 seconds as a safety measure
            setTimeout(() => {
                if (scrollInterval) {
                    clearInterval(scrollInterval);
                }
            }, 30000);
        </script>
        """
        stcomponents.html(js, height=0)

    def _display_chat_history(self) -> None:
        """Display the chat history in the Streamlit interface."""

        for message in st.session_state.messages:
            message: ChatMessage
            message.display()

        st.session_state.scroll_div_index = 0
        self._scroll_to_bottom()

    def _handle_edit_message(self) -> None:
        if st.session_state.edit_message_value:
            original_message: ChatMessage = st.session_state.edit_message_value[0]
            prompt_return: PromptReturn = st.session_state.edit_message_value[1]

            # Remove this message and all following messages
            st.session_state.messages = st.session_state.messages[
                : original_message.index
            ]
            st.session_state.storage.delete_messages_from_index(
                session_id=st.session_state.current_session_id,
                from_index=original_message.index,
            )

            new_message = ChatMessage.create_from_prompt(
                user_input=prompt_return,
                session_id=original_message.session_id,
                index=original_message.index,
            )

            # Add edited message
            st.session_state.messages.append(new_message)
            st.session_state.storage.save_message(message=new_message)

            # Set turn state to AI_TURN to generate new response
            st.session_state.turn_state = TurnState.AI_TURN

            st.session_state.edit_message_value = None

    def _handle_chat_input(self) -> None:
        """Handle user input from the chat interface.

        Gets input from the chat prompt and processes it if provided.
        """
        user_input: Optional[PromptReturn] = prompt(
            name="chat_input",
            key="user_input",
            placeholder="Hello!",
            disabled=False,
            max_image_size=5 * 1024 * 1024,
        )

        if st.session_state.turn_state == TurnState.HUMAN_TURN:
            if user_input:
                human_message = ChatMessage.create_from_prompt(
                    user_input=user_input,
                    session_id=st.session_state.current_session_id,
                )

                human_message.display()
                st.session_state.scroll_div_index += 1
                self._scroll_to_bottom()

                # Save to storage if we have a session, otherwise save later after session title is generated
                if st.session_state.current_session_id:
                    self.storage.save_message(message=human_message)

                st.session_state.messages.append(human_message)

                # Set state for AI to respond
                st.session_state.turn_state = TurnState.AI_TURN

    def _convert_messages_to_llm_format(self) -> list[BaseMessage]:
        """Convert stored ChatMessages to LLM format.

        Returns:
            List of BaseMessage objects in LLM format.
        """
        return [msg.convert_to_llm_message() for msg in st.session_state.messages]

    def _generate_ai_response(self) -> None:
        """Generate and display an AI response."""

        if st.session_state.turn_state == TurnState.AI_TURN:

            # Convert messages to LLM format
            llm_messages: list[BaseMessage] = self._convert_messages_to_llm_format()

            # Generate and display AI response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                self._scroll_to_bottom_streaming()
                for chunk in self.llm.stream(input=llm_messages):
                    for item in chunk.content:
                        if isinstance(item, dict) and "text" in item:
                            text = item["text"]
                            full_response += text
                        message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

                # Create ChatMessage
                current_index = len(st.session_state.messages)

                st.session_state.messages.append(
                    ChatMessage(
                        session_id=st.session_state.current_session_id or "",
                        role="assistant",
                        content=full_response,
                        index=current_index,
                    )
                )

                # Create new session if none exists
                if not st.session_state.current_session_id:
                    title: str = self._generate_session_title()
                    new_session: ChatSession = ChatSession.create(
                        title=title,
                        metadata={
                            "model": MODEL
                        },  # TODO use metadata from app settings?
                    )
                    self.storage.store_session(session=new_session)

                    st.session_state.current_session_id = new_session.session_id

                    # Update session_id for all messages and save
                    for msg in st.session_state.messages:
                        msg.session_id = new_session.session_id

                    # save to storage the original human message we didn't save initially
                    self.storage.save_message(message=st.session_state.messages[-2])

                # Save AI message
                self.storage.save_message(message=st.session_state.messages[-1])

                # Update state for next human input
                st.session_state.turn_state = TurnState.HUMAN_TURN
                st.rerun()

    def _generate_session_title(self) -> str:
        """Generate a concise session title using the LLM.

        Returns:
            A concise title for the chat session (2-4 words).

        Note:
            Falls back to timestamp-based title if LLM fails to generate one.
        """

        title_prompt: HumanMessage = HumanMessage(
            content=f"""Summarize this conversation's topic in up to 5 words or about 40 characters. 
            More details are useful, but space is limited to show this summary, so ideally 2-4 words.
            Be direct and concise, no explanations needed. If there are missing messages, do the best you can to keep the summary short."""
        )
        title_response: BaseMessage = self.llm.invoke(
            [*self._convert_messages_to_llm_format(), title_prompt]
        )
        title_content: str | list[str | dict] = title_response.content

        if isinstance(title_content, str):
            title: str = title_content.strip('" \n').strip()
        else:
            print(f"Unexpected generated title response: {title_content}")
            return f"Chat {datetime.now()}"

        # Fallback to timestamp if we get an empty or invalid response
        if not title:
            title = f"Chat {datetime.now()}"

        print(f"New session title: {title}")
        return title
