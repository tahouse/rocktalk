import streamlit as st
from config.settings import SettingsManager
from models.interfaces import ChatTemplate, LLMConfig


@st.dialog("Template Settings")
def template_settings():
    """Dialog for managing chat templates"""
    storage = st.session_state.storage
    templates = storage.get_chat_templates()

    tab1, tab2 = st.tabs(["Templates", "Create New"])

    with tab1:
        _render_existing_templates(templates, storage)

    with tab2:
        _render_new_template_form(storage)


def _render_existing_templates(templates, storage):
    """Render the list of existing templates with actions"""
    for template in templates:
        with st.expander(template.name):
            st.markdown(f"**Description:** {template.description}")
            SettingsManager.render_config_summary(template.config)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Use", key=f"use_{template.template_id}"):
                    SettingsManager.update_config(template.config)
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{template.template_id}"):
                    storage.delete_chat_template(template.template_id)
                    st.rerun()


def _render_new_template_form(storage):
    """Render the form for creating a new template"""
    with st.form("new_template"):
        name = st.text_input("Name", help="Template name")
        description = st.text_area("Description", help="Template description")

        # Initialize temp config if needed
        if (
            "temp_llm_config" not in st.session_state
            or st.session_state.temp_llm_config is None
        ):
            st.session_state.temp_llm_config = LLMConfig.get_default()

        # Model selection
        st.subheader("Model Configuration")
        SettingsManager.render_model_selector(
            st.session_state.temp_llm_config.bedrock_model_id
        )

        # Parameter controls
        st.subheader("Parameters")
        SettingsManager.render_parameter_controls()

        if st.form_submit_button("Create Template"):
            if not name or not description:
                st.error("Please provide both name and description")
                return

            template = ChatTemplate(
                name=name,
                description=description,
                config=st.session_state.temp_llm_config,
            )
            storage.store_chat_template(template)

            # Clear temporary config
            SettingsManager.clear_cached_settings_vars()
            st.rerun()
