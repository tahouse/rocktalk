from contextlib import nullcontext

import streamlit as st
from config.settings import SettingsManager
from models.interfaces import ChatExport, LLMConfig


@st.dialog("Settings")
def general_options():
    """Dialog for global application settings and data management"""
    SettingsManager.render_settings_dialog()


# def general_options():
#     """Dialog for global application settings and data management"""
#     tab1, tab2 = st.tabs(["Model Settings", "Import/Export"])

#     with tab1:
#         _render_model_settings()
#     with tab2:
#         _render_import_export()


# def _render_model_settings():
#     """Render global model settings when no session is active"""
#     if st.session_state.current_session_id is None:
#         SettingsManager.render_settings_controls()
#     else:
#         st.info("⚠️ Model settings can only be changed when no session is active")


# def _render_import_export():
#     """Render import/export functionality"""
#     st.markdown("## Import/Export")

#     # Import section
#     _render_import_section()

#     st.divider()

#     # Reset section
#     _render_reset_section()


# def _render_import_section():
#     """Handle conversation import functionality"""
#     with st.form("session_upload", clear_on_submit=True):
#         uploaded_file = st.file_uploader(
#             "Import Conversation",
#             type=["json"],
#             key="conversation_import",
#             help="Upload a previously exported conversation",
#         )

#         if st.form_submit_button("Import"):
#             if uploaded_file is None:
#                 st.error("Please select a file to import")
#                 return

#             try:
#                 _process_import_file(uploaded_file)
#                 st.success("Conversation imported successfully!")
#                 st.rerun()
#             except Exception as e:
#                 st.error(f"Error importing conversation: {str(e)}")
#                 raise e


# def _process_import_file(uploaded_file):
#     """Process the imported conversation file"""
#     import_data = ChatExport.model_validate_json(uploaded_file.getvalue())

#     # Store the imported session
#     st.session_state.storage.store_session(import_data.session)

#     # Store all messages
#     for msg in import_data.messages:
#         st.session_state.storage.save_message(msg)

#     # Update current session
#     st.session_state.current_session_id = import_data.session.session_id
#     uploaded_file.close()


# def _render_reset_section():
#     """Handle application reset functionality"""
#     with st.form("reset_data", clear_on_submit=False):
#         st.warning("⚠️ This will delete ALL sessions and messages!")

#         if st.form_submit_button("Reset All Data"):
#             if _confirm_reset():
#                 _perform_reset()
#                 st.rerun()
#             else:
#                 st.session_state["confirm_reset"] = True
#                 st.warning("Click again to confirm reset")


# def _confirm_reset() -> bool:
#     """Check if reset has been confirmed"""
#     return st.session_state.get("confirm_reset", False)


# def _perform_reset():
#     """Perform the actual reset operation"""
#     st.session_state.storage.delete_all_sessions()
#     st.session_state.current_session_id = None
#     st.session_state.messages = []
#     SettingsManager.clear_cached_settings_vars()
