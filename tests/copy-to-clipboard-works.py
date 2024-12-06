import functools

import streamlit as st
import streamlit.components.v1 as stcomponents
from streamlit_float import float_css_helper, float_init

float_init()

# st.markdown(
#     f"""
#         <style>
#         .element-container:has(iframe[height="0"]) {{
#           display: none;
#         }}
#         </style>
#     """,
#     unsafe_allow_html=True,
# )

# stcomponents.v1.html("Booh", height=0)
# stcomponents.html("Bah", height=30)


# def copy_to_clipboard(input_key: str):
#     js = (
#         """<script>
#     function copyFunction() {
#         try {
#             // Get text from parent window
#             const parentDoc = window.parent.document;
#             const stInput = parentDoc.querySelector('.st-key-"""
#         + f"""{input_key}"""
#         + """ input');

#             const textToCopy = stInput ? stInput.value : '';
#             console.log("textToCopy:", textToCopy);

#             window.parent.navigator.clipboard.writeText(textToCopy);


#             console.log('Text copied successfully');
#         } catch (err) {
#             console.error('Copy failed:', err);
#         }
#     }
#     copyFunction();
#     </script>
#     """
#     )
#     stcomponents.html(js, height=0)


def copy_to_clipboard(input_key: str):
    js = f"""
    <script>
    function copyFunction() {{
        try {{
            const parentDoc = window.parent.document;
            const stInput = parentDoc.querySelector('.st-key-{input_key} input');
            
            if (!stInput) {{
                console.error('Input element not found');
                return;
            }}

            const textToCopy = stInput.value;
            console.log("textToCopy:", textToCopy);

            // Try using the parent window's clipboard API first
            if (window.parent.navigator.clipboard) {{
                window.parent.navigator.clipboard.writeText(textToCopy)
                    .then(() => {{
                        console.log('Text copied successfully');
                    }})
                    .catch((err) => {{
                        console.error('Clipboard API failed:', err);
                        fallbackCopy(textToCopy, parentDoc);
                    }});
            }} else {{
                fallbackCopy(textToCopy, parentDoc);
            }}
        }} catch (err) {{
            console.error('Copy failed:', err);
        }}
    }}

    function fallbackCopy(text, parentDoc) {{
        try {{
            const textarea = parentDoc.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            
            parentDoc.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {{
                parentDoc.execCommand('copy');
                console.log('Text copied using fallback method');
            }} catch (execErr) {{
                console.error('execCommand failed:', execErr);
            }}
            
            parentDoc.body.removeChild(textarea);
        }} catch (err) {{
            console.error('Fallback copy failed:', err);
            
            // Last resort fallback
            try {{
                const tempInput = parentDoc.createElement('input');
                tempInput.value = text;
                tempInput.style.position = 'fixed';
                tempInput.style.opacity = '0';
                
                parentDoc.body.appendChild(tempInput);
                tempInput.select();
                tempInput.setSelectionRange(0, 99999);
                
                parentDoc.execCommand('copy');
                parentDoc.body.removeChild(tempInput);
                console.log('Text copied using last resort method');
            }} catch (finalErr) {{
                console.error('All copy methods failed:', finalErr);
            }}
        }}
    }}

    // For the clipboard API not working on subsequent loads,
    // try to reinitialize it each time
    function initAndCopy() {{
        if (window.parent.navigator.clipboard) {{
            // Force clipboard permission check
            window.parent.navigator.permissions.query({{name: 'clipboard-write'}})
                .then(result => {{
                    console.log('Clipboard permission:', result.state);
                    copyFunction();
                }})
                .catch(() => {{
                    copyFunction();
                }});
        }} else {{
            copyFunction();
        }}
    }}

    initAndCopy();
    </script>
    """
    stcomponents.html(js, height=0, width=0)


input_key = "text_to_copy"
# Wrap both containers in a parent container
parent_container = st.container()
with parent_container:
    # Create main container for text input with a unique key
    main_container = st.container()
    with main_container:
        text_input = st.text_input(
            "Text to copy:", value="Hello, Streamlit!", key=input_key
        )

    # Create button container and float it
    button_container = st.container()
    with button_container:
        st.button(
            "📋",
            key="copy_button",
            on_click=functools.partial(copy_to_clipboard, input_key),
        )

    # Float the button container relative to main_container
    button_css = float_css_helper(
        position="relative",
        top="-3.5rem",  # Move up relative to its normal position
        left="calc(100% + .5rem)",  # Position from the right edge
        width="3rem",
        z_index="1000",
        margin="0",
    )
    button_container.float(button_css)
