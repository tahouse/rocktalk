import json

import streamlit as st
from streamlit_float import float_css_helper, float_init
from streamlit_js_eval import streamlit_js_eval

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


def copy_input_to_clipboard(input_key: str):
    st.markdown(
        """
        <style>
            .element-container:has(
                iframe[title="streamlit_js_eval.streamlit_js_eval"]
            ) {
                height: 0 !important;
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    streamlit_js_eval(
        js_expressions=f"""
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
    """
    )


def copy_value_to_clipboard(value: str):
    value = json.dumps(value)

    st.markdown(
        """
        <style>
            .element-container:has(
                iframe[title="streamlit_js_eval.streamlit_js_eval"]
            ) {
                height: 0 !important;
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    streamlit_js_eval(
        js_expressions=f"""
        function copyFunction() {{
            try {{
                const parentDoc = window.parent.document;

                const textToCopy = {value};
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
    """
    )
    st.toast(body="Copied to clipboard", icon="📋")


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
        if text_input:
            text_val = f"Wrote: {text_input}"

            st.chat_message("user").container(key="text_val").markdown(text_val)
    # Create button container and float it
    button_container = st.container()
    with button_container:
        # print(st.session_state[input_key])
        if st.button(
            "📋",
            key="copy_button",
            # on_click=functools.partial(copy_input_to_clipboard, input_key),
        ):
            # specific to input types -- not really useful, better if generic key? then what, copy the value?
            copy_input_to_clipboard(input_key)

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
if st.button("Copy Value to Clipboard"):
    value = "Here are 5 good cartoons:\n\n1. Avatar: The Last Airbender\n2. SpongeBob SquarePants\n3. The Simpsons\n4. Adventure Time\n5. Gravity Falls"
    copy_value_to_clipboard(value)
    st.markdown(value)
