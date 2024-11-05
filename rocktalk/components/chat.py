from datetime import datetime
from typing import List, cast

import streamlit as st
from langchain.schema import AIMessage, HumanMessage
from langchain_core.messages.ai import AIMessageChunk

from models.interfaces import ChatMessage, ChatSession, LLMInterface, StorageInterface


class ChatInterface:
    def __init__(self, storage: StorageInterface, llm: LLMInterface):
        self.storage = storage
        self.llm = llm

    def render(self):
        self._display_chat_history()
        self._handle_chat_input()

    def _display_chat_history(self):
        for message in st.session_state.messages:
            with st.chat_message(message.additional_kwargs["role"]):
                st.markdown(message.content)

    def _handle_chat_input(self):
        if prompt := st.chat_input("Hello!"):
            self._process_user_input(prompt)
            self._generate_ai_response()

    def _process_user_input(self, prompt: str):
        print(f"\nHuman: {prompt}")

        # Display and save user message
        with st.chat_message("user"):
            st.markdown(prompt)

        human_input = HumanMessage(content=prompt, additional_kwargs={"role": "user"})
        st.session_state.messages.append(human_input)

        if st.session_state.current_session_id:
            # Save user message to storage if we have an existing session
            self.storage.save_message(
                ChatMessage(
                    session_id=st.session_state.current_session_id,
                    role="user",
                    content=prompt,
                )
            )

    def _generate_session_title(self, human_message: str, ai_response: str) -> str:
        """Generate a concise session title using the LLM with full conversation context"""
        title_prompt = HumanMessage(
            content=f"""Summarize this conversation's topic in up to 5 words or about 40 characters. More details are useful, but space is limited to show this summary, so ideally 2-4 words.
            Be direct and concise, no explanations needed.
            
            Conversation:
            Human: {human_message}
            Assistant: {ai_response}"""
        )

        title = self.llm.invoke([title_prompt]).content.strip('" \n').strip()

        # Fallback to timestamp if we get an empty or invalid response
        if not title:
            title = f"Chat {datetime.now()}"

        print(f"New session title: {title}")
        return title

    def _generate_ai_response(self):
        print("AI: ")

        # Generate and display AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            for chunk in st.session_state.llm.stream(st.session_state.messages):
                chunk = cast(AIMessageChunk, chunk)
                for item in chunk.content:
                    if isinstance(item, dict) and "text" in item:
                        text = item["text"]
                        full_response += text
                        print(text, end="", flush=True)

                    message_placeholder.markdown(full_response + "▌")

                if chunk.response_metadata:
                    print(chunk.response_metadata)
                if chunk.usage_metadata:
                    print(type(chunk))
                    print(chunk.usage_metadata)

            # Save AI response
            ai_response = AIMessage(
                content=full_response, additional_kwargs={"role": "assistant"}
            )

            # Create new session if none exists
            if not st.session_state.current_session_id:
                # Get the human message that started this conversation
                human_message = st.session_state.messages[-1].content
                title = self._generate_session_title(human_message, full_response)
                new_session = ChatSession.create(
                    title=title,
                    subject=title,
                    metadata={"model": "anthropic.claude-3-sonnet-20240229-v1:0"},
                )
                self.storage.store_session(new_session)

                st.session_state.current_session_id = new_session.session_id
                # Save the initial human message now that we have a session
                self.storage.save_message(
                    ChatMessage(
                        session_id=st.session_state.current_session_id,
                        role="user",
                        content=human_message,
                    )
                )

            st.session_state.messages.append(ai_response)

            # Save to storage
            self.storage.save_message(
                ChatMessage(
                    session_id=st.session_state.current_session_id,
                    role="assistant",
                    content=full_response,
                )
            )

            message_placeholder.markdown(full_response)

            # Update last_update timestamp
            st.session_state.last_update = datetime.now()

            # Now rerun after the complete conversation turn is saved
            st.rerun()
