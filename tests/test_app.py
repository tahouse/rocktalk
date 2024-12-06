import base64
from io import BytesIO

import streamlit as st
from PIL import Image
from streamlit_chat_prompt import prompt

if "counter" not in st.session_state:
    st.session_state.counter = 0
st.session_state.counter += 1
print(
    "-------------------------------------------------------------------------------------"
)
print(f"rerun {st.session_state.counter}")

if val := prompt("foo", key="foo"):
    # time.sleep(1)
    # st.rerun()
    # st.session_state.foo = None
    st.write(val.message)
    for image_data in val.images:
        # Decode the base64 image data
        image_bytes = base64.b64decode(image_data.data)
        # Create a PIL Image object
        image = Image.open(BytesIO(image_bytes))
        # Display the image using Streamlit
        st.image(image, caption=f"Image ({image_data.type};{image_data.format})")
val
# Radio button
st.radio("Choose an option", ["1", "2", "3"])

# # Slider
# st.slider("Select a value", 0, 100, 50)

# # Text input
# user_input = st.text_input("Enter some text", "Default text")

# Expander
# with st.expander("Click to expand"):
#     st.write("This is expanded content!")
# if val := st.chat_input():
#     pass
# val
# print(st.session_state)
