import hmac
import os
import time
from typing import Optional

import dotenv
import streamlit as st
from models.interfaces import ChatSession, ChatTemplate, LLMConfig, LLMParameters
from models.storage_interface import StorageInterface
from services.bedrock import BedrockService
from utils.log import logger

# Load environment variables
dotenv.load_dotenv()

# Check for deployment environment
DEPLOYED = os.getenv("DEPLOYED", "true").lower() == "true"


def get_password() -> Optional[str]:
    """
    Get password from environment variables or Streamlit secrets
    Returns None if no password is configured, with appropriate warnings
    """
    password = None
    if DEPLOYED:
        password = st.secrets.get("password")
        if not password:
            st.warning("⚠️ No password configured in Streamlit secrets")
    else:
        password = os.getenv("APP_PASSWORD")
        if not password:
            st.warning("⚠️ No APP_PASSWORD set in environment variables")
    return password


def check_password() -> bool:
    """Returns `True` if the user had the correct password."""
    password = get_password()
    if not password:
        st.error("Password not configured")
        st.stop()

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


class SettingsManager:

    @staticmethod
    def initialize_temp_config(base_config: Optional[LLMConfig] = None):
        """Initialize temporary configuration state"""
        if (
            "temp_llm_config" not in st.session_state
            or st.session_state.temp_llm_config is None
        ):
            if base_config:
                st.session_state.temp_llm_config = base_config.model_copy(deep=True)
            else:
                st.session_state.temp_llm_config = st.session_state.llm.get_config()

    @staticmethod
    def apply_settings(set_as_default: bool = False) -> bool:
        """
        Apply current temporary settings
        Returns True if successful
        """
        try:
            st.session_state.llm.update_config(st.session_state.temp_llm_config)

            if set_as_default:
                LLMConfig.set_default(st.session_state.temp_llm_config)

            SettingsManager.clear_cached_settings_vars()
            return True
        except Exception as e:
            st.error(f"Error applying settings: {str(e)}")
            return False

    # in settings.py, add the dialog rendering method:

    @staticmethod
    def render_settings_dialog():
        """Render the settings dialog"""
        tab1, tab2 = st.tabs(["Model Settings", "Import/Export"])

        with tab1:
            if st.session_state.current_session_id is None:
                # Initialize temp config if needed
                SettingsManager.initialize_temp_config()

                # Render controls
                SettingsManager.render_model_selector()
                st.subheader("Parameters")
                SettingsManager.render_parameter_controls()

                # Save settings
                set_as_default = st.checkbox(
                    "Set as default configuration",
                    help="These settings will be used for new sessions",
                )

                if st.button("Apply Settings", type="primary"):
                    if SettingsManager.apply_settings(set_as_default):
                        st.success("Settings applied successfully!")
                        st.rerun()
            else:
                st.info(
                    "⚠️ Model settings can only be changed when no session is active"
                )

    @staticmethod
    def render_settings_controls(session: Optional[ChatSession] = None):
        """Render complete settings UI with proper state management"""
        # Initialize temp config if needed
        SettingsManager.initialize_temp_config(session.config if session else None)

        # Render controls
        SettingsManager.render_model_selector()
        st.subheader("Parameters")
        SettingsManager.render_parameter_controls(session=session)

        # Save settings
        set_as_default = st.checkbox(
            "Set as default configuration",
            help="These settings will be used for new sessions",
        )

        if st.button("Apply Settings", type="primary"):
            if SettingsManager.apply_settings(set_as_default):
                st.success("Settings applied successfully!")
                st.rerun()

    @staticmethod
    def clear_cached_settings_vars():
        """Clear cached settings variables"""
        vars_to_clear = [
            "temp_llm_config",
            "temp_llm_preset",
            "llm_preset",
            "providers_reorder",
            "current_provider",
            "model_providers",
            "ordered_providers",
        ]
        for var in vars_to_clear:
            if var in st.session_state:
                del st.session_state[var]

    @staticmethod
    def update_config(config: LLMConfig):
        """Update the current temp LLM configuration"""
        st.session_state.temp_llm_config = config.model_copy(deep=True)

    @staticmethod
    def render_config_summary(config: LLMConfig) -> None:
        """Display read-only summary of a config"""
        st.markdown(f"**Model:** {config.bedrock_model_id}")
        st.markdown(f"**Temperature:** {config.parameters.temperature}")
        if config.system:
            st.markdown(f"**System Prompt:** {config.system}")

    @staticmethod
    def render_model_selector() -> None:
        """Render model selection UI"""
        if "available_models" not in st.session_state:
            try:
                st.session_state.available_models = (
                    BedrockService.get_compatible_models()
                )
            except Exception as e:
                st.error(f"Error getting compatible models: {e}")
                st.session_state.available_models = []

        if not st.session_state.available_models:
            return

        current_model = next(
            (
                m
                for m in st.session_state.available_models
                if m.bedrock_model_id
                == st.session_state.temp_llm_config.bedrock_model_id
            ),
            None,
        )

        with st.expander("Change Model", expanded=False):
            if (
                "model_providers" not in st.session_state
                or st.session_state.model_providers is None
            ):
                providers = {}
                for model in st.session_state.available_models:
                    provider = model.provider_name or "Other"
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(model)
                st.session_state.model_providers = providers

            if (
                "current_provider" not in st.session_state
                or st.session_state.current_provider is None
            ):
                st.session_state.current_provider = (
                    current_model.provider_name if current_model else None
                )

            if (
                "ordered_providers" not in st.session_state
                or st.session_state.ordered_providers is None
            ):
                st.session_state.ordered_providers = sorted(
                    st.session_state.model_providers.keys(),
                    key=lambda x: x != st.session_state.current_provider,
                )

            provider_tabs = st.tabs(st.session_state.ordered_providers)
            for tab, provider in zip(provider_tabs, st.session_state.ordered_providers):
                with tab:
                    for model in st.session_state.model_providers[provider]:
                        st.divider()
                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.markdown(f"**{model.bedrock_model_id}**")
                            if model.model_name:
                                st.markdown(f"*{model.model_name}*")
                        with col2:
                            st.button(
                                "Select",
                                key=f"select_{model.bedrock_model_id}",
                                type=(
                                    "primary"
                                    if (
                                        model.bedrock_model_id
                                        == st.session_state.temp_llm_config.bedrock_model_id
                                    )
                                    else "secondary"
                                ),
                                on_click=lambda p=provider, m=model.bedrock_model_id: SettingsManager._set_model(
                                    p, m
                                ),
                            )

    @staticmethod
    def _set_model(provider: str, model_id: str):
        """Internal method to set the model configuration"""
        st.session_state.temp_llm_config.bedrock_model_id = model_id
        if st.session_state.temp_llm_config.parameters.max_output_tokens:
            st.session_state.temp_llm_config.parameters.max_output_tokens = min(
                st.session_state.temp_llm_config.parameters.max_output_tokens,
                BedrockService.get_max_output_tokens(model_id),
            )
        st.session_state.current_provider = provider

    @staticmethod
    def render_parameter_controls(session: Optional[ChatSession] = None) -> None:
        """Render parameter controls (temperature, tokens, etc)"""
        config: LLMConfig = st.session_state.temp_llm_config

        # System Prompt
        if not session:
            new_system = st.text_area(
                "System Prompt",
                value=config.system or "",
                help="Optional system prompt to provide context or instructions for the model",
            )
            st.session_state.temp_llm_config.system = new_system.strip() or None
        else:
            st.markdown(
                f"*System prompt is not editable in existing session*\n\n"
                f"**System message:** {st.session_state.temp_llm_config.system}"
            )

        # Temperature
        use_temp = st.checkbox(
            "Use Temperature", value=config.parameters.temperature is not None
        )
        if use_temp:
            new_temp = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=float(config.parameters.temperature),
                step=0.1,
                help="Higher values make the output more random, lower values more deterministic",
            )
            st.session_state.temp_llm_config.parameters.temperature = new_temp

        # Max Tokens
        use_max_tokens = st.checkbox(
            "Use Max Tokens", value=config.parameters.max_output_tokens is not None
        )
        if use_max_tokens:
            max_tokens = BedrockService.get_max_output_tokens(config.bedrock_model_id)
            new_max_tokens = st.number_input(
                "Max Output Tokens",
                min_value=1,
                max_value=max_tokens,
                value=config.parameters.max_output_tokens or max_tokens,
                help="Maximum number of tokens in the response",
            )
            st.session_state.temp_llm_config.parameters.max_output_tokens = (
                new_max_tokens
            )

        # Top P
        use_top_p = st.checkbox("Use Top P", value=config.parameters.top_p is not None)
        if use_top_p:
            new_top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=config.parameters.top_p or 1.0,
                step=0.01,
                help="The percentage of most-likely candidates that the model considers",
            )
            st.session_state.temp_llm_config.parameters.top_p = new_top_p

        # Top K (Anthropic only)
        if "anthropic" in config.bedrock_model_id.lower():
            use_top_k = st.checkbox(
                "Use Top K", value=config.parameters.top_k is not None
            )
            if use_top_k:
                new_top_k = st.number_input(
                    "Top K",
                    min_value=1,
                    max_value=500,
                    value=config.parameters.top_k or 250,
                    help="Number of most-likely candidates (Anthropic models only)",
                )
                st.session_state.temp_llm_config.parameters.top_k = new_top_k

        # Stop Sequences
        new_stop_sequences = st.text_input(
            "Stop Sequences",
            value=", ".join(config.stop_sequences),
            help="Comma-separated list of sequences that will cause the model to stop",
        ).split(",")
        st.session_state.temp_llm_config.stop_sequences = [
            seq.strip() for seq in new_stop_sequences if seq.strip()
        ]
