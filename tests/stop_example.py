import streamlit as st
from streamlit_float import float_css_helper, float_init

float_init()

# Create a wrapper container for both elements
wrapper = st.container()
with wrapper:
    # Create main container for prompt
    main_container = st.container()
    with main_container:
        text_input = st.text_input("Enter text")

    # Create button container
    button_container = st.container()
    with button_container:
        stop_button = st.button("Stop Stream 🛑")

# Add CSS to handle sidebar and theme states
st.markdown(
    """
<style>
/* Main content area */
section[data-testid="stMain"] {
    padding-bottom: 100px;  /* Make room for the fixed component */
}

/* Sidebar states */
.sidebar-collapsed .element-container:has(> div[data-testid="wrapper"]) {
    left: 50%;
    width: calc(min(800px, 100% - 2rem)) !important;
    transform: translateX(-50%);
}

.sidebar-expanded .element-container:has(> div[data-testid="wrapper"]) {
    left: calc((100% - 245px) / 2 + 245px);  /* 245px is default sidebar width */
    width: calc(min(800px, 100% - 245px - 2rem)) !important;
    transform: translateX(-50%);
}
</style>
""",
    unsafe_allow_html=True,
)

# Float the wrapper container
wrapper.float(
    float_css_helper(
        position="fixed",
        bottom="1rem",
        z_index="1000",
        data_testid="wrapper",  # Add test id for CSS targeting
    )
)

# Position button relative to wrapper
button_container.float(
    float_css_helper(
        position="absolute",  # Absolute within the wrapper
        top="-3.5rem",  # Move up relative to wrapper
        right="0",  # Align to right edge of wrapper
        width="10rem",
    )
)

# Add some sidebar content to test
with st.sidebar:
    st.write("Sidebar content")
