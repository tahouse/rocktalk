import base64
from dataclasses import dataclass
from io import BytesIO
from typing import List

import streamlit as st
from PIL import Image
from streamlit_chat_prompt import ImageData, PromptReturn, prompt
from streamlit_float import float_css_helper, float_init

float_init()

st.title("streamlit-chat-prompt")


@dataclass
class ChatMessage:
    role: str
    content: str | PromptReturn


if "messages" not in st.session_state:
    messages: List[ChatMessage] = [
        ChatMessage(role="assistant", content="Hi there! What should we chat about?")
    ]
    st.session_state.messages = messages

# # Add CSS for dynamic sidebar handling and spacing
# st.markdown(
#     """
# <style>
# /* Main content area */
# section[data-testid="stMain"] {
#     padding-bottom: 8rem;  /* Make room for the fixed components */
# }

# /* Sidebar states */
# .sidebar-collapsed .element-container:has(> div[data-testid="chat-wrapper"]) {
#     left: 50%;
#     width: calc(min(800px, 100% - 2rem)) !important;
#     transform: translateX(-50%);
# }

# .sidebar-expanded .element-container:has(> div[data-testid="chat-wrapper"]) {
#     left: calc((100% - 245px) / 2 + 245px);  /* 245px is default sidebar width */
#     width: calc(min(800px, 100% - 245px - 2rem)) !important;
#     transform: translateX(-50%);
# }
# </style>
# """,
#     unsafe_allow_html=True,
# )


@st.dialog("Prompt in dialog")
def dialog(default_input: str | PromptReturn | None = None, key="default_dialog_key"):
    dialog_input = prompt(
        "dialog_prompt",
        key=key,
        placeholder="This is a dialog prompt",
        main_bottom=False,
        default=default_input,
    )
    if dialog_input:
        st.write(dialog_input)


with st.sidebar:
    st.header("Sidebar")

    if st.button("Dialog Prompt", key=f"dialog_prompt_button"):
        dialog()

    if st.button(
        "Dialog Prompt with Default Value", key=f"dialog_prompt_with_default_button"
    ):
        with open("example_images/vangogh.png", "rb") as f:
            image_data = f.read()
            image = Image.open(BytesIO(image_data))
            base64_image = base64.b64encode(image_data).decode("utf-8")
            dialog(
                default_input=PromptReturn(
                    text="This is a test message with an image",
                    images=[
                        ImageData(data=base64_image, type="image/png", format="base64")
                    ],
                ),
                key="dialog_with_default",
            )

for chat_message in st.session_state.messages:
    chat_message: ChatMessage

    with st.chat_message(chat_message.role):
        if isinstance(chat_message.content, PromptReturn):
            st.markdown(chat_message.content.text)
            if chat_message.content.images:
                for image_data in chat_message.content.images:
                    st.divider()
                    st.markdown("Using `st.markdown`")
                    st.markdown(
                        f"![Image example](data:{image_data.type};{image_data.format},{image_data.data})"
                    )

                    # or use PIL
                    st.divider()
                    st.markdown("Using `st.image`")
                    image = Image.open(BytesIO(base64.b64decode(image_data.data)))
                    st.image(image)

        else:
            st.markdown(chat_message.content)

# Create a wrapper container for both prompt and button
wrapper = st.container()
with wrapper:
    # Create main container for prompt
    main_container = st.container()
    with main_container:
        prompt_return: PromptReturn | None = prompt(
            name="foo",
            key="chat_prompt",
            placeholder="Hi there! What should we chat about?",
            main_bottom=False,
        )

        if prompt_return:
            st.session_state.messages.append(
                ChatMessage(role="user", content=prompt_return)
            )
            st.session_state.messages.append(
                ChatMessage(role="assistant", content=f"Echo: {prompt_return.text}")
            )
            st.rerun()

# Create button container
button_container = st.container()
with button_container:
    stop_button = st.button(label="Stop Stream 🛑", use_container_width=True)
    if stop_button:
        print("stopping")

# Float the wrapper container
wrapper.float(
    float_css_helper(
        position="fixed",
        bottom="1rem",
        z_index="1000",
        data_testid="chat-wrapper",  # Add test id for CSS targeting
    )
)
# Position button on right side of viewport
button_container.float(
    float_css_helper(
        position="fixed",  # Fixed to viewport
        bottom="6rem",
        # top="50%",  # Center vertically
        # right="2rem",  # Small margin from right edge
        # margin="0",
        display="flex",
        # padding="60",
        # height="5rem",
        z_index="1001",
        # align_items="center",  # Center items vertically
        # align_items="center",  # Center items vertically
    )
)
# float_box(
#     "",
#     width="100%",
#     height="100%",
#     left="0",
#     top="0",
#     css=float_css_helper(
#         # background=color, backdrop_filter=backdrop_filter, z_index=z_index
#     ),
# )
