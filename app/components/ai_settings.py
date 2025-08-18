"""AI Provider Settings Component for AlitaOS"""

import streamlit as st
from utils.ai_models import get_ollama_models, is_ollama_available
from typing import List, Dict, Any


def display_ai_settings():
    """Display AI provider and model selection settings."""
    
    # Initialize session state for AI settings
    if "ai_provider" not in st.session_state:
        st.session_state.ai_provider = "openai"
    if "ai_model" not in st.session_state:
        st.session_state.ai_model = "gpt-4o-mini"
    if "show_ai_settings" not in st.session_state:
        st.session_state.show_ai_settings = False
    
    # Settings toggle button with custom styling
    st.markdown("""
    <style>
    /* Fix AI Settings button to be consistently grey */
    .st-emotion-cache-1anq8dj, 
    button[data-testid="baseButton-secondary"],
    .stButton > button {
        background-color: rgb(75, 85, 99) !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        color: white !important;
    }
    .st-emotion-cache-1anq8dj:hover,
    button[data-testid="baseButton-secondary"]:hover,
    .stButton > button:hover {
        background-color: rgb(107, 114, 128) !important;
        border: 1px solid rgba(250, 250, 250, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚙️ AI Settings", use_container_width=True):
            st.session_state.show_ai_settings = not st.session_state.show_ai_settings
    
    # Show settings panel if toggled
    if st.session_state.show_ai_settings:
        with st.container():
            st.markdown("""
            <div class="tool-card">
                <h4 style="margin-top: 0; color: var(--charcoal);">🅰️ AI Provider Settings</h4>
                <style>
                /* Fix radio button and text styling */
                .stRadio > div {
                    color: var(--charcoal) !important;
                }
                .stRadio > div > label {
                    color: var(--charcoal) !important;
                    background-color: transparent !important;
                }
                .stRadio > div > label > div {
                    color: var(--charcoal) !important;
                }
                .stRadio > div > label > div[data-testid="stMarkdownContainer"] p {
                    color: var(--charcoal) !important;
                }
                /* Fix selectbox styling */
                .stSelectbox > div > div {
                    color: white !important;
                }
                .stSelectbox label {
                    color: white !important;
                }
                /* Ensure all text in settings is readable */
                .tool-card * {
                    color: white !important;
                }
                .tool-card strong {
                    color: var(--charcoal) !important;
                    font-weight: bold;
                }
                .tool-card h4 {
                    color: var(--charcoal) !important;
                }
                /* Fix label text to be charcoal for better contrast */
                .tool-card p {
                    color: var(--charcoal) !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Provider selection
            providers = ["openai"]
            provider_labels = ["OpenAI (Cloud)"]
            
            # Check if Ollama is available
            if is_ollama_available():
                providers.append("ollama")
                provider_labels.append("Ollama (Local)")
                ollama_status = "🟢 Connected"
            else:
                ollama_status = "🔴 Not Available"
            
            # Display provider selection
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Provider:**")
                current_provider_idx = 0
                if st.session_state.ai_provider in providers:
                    current_provider_idx = providers.index(st.session_state.ai_provider)
                
                selected_provider_idx = st.radio(
                    "Select AI Provider",
                    range(len(provider_labels)),
                    index=current_provider_idx,
                    format_func=lambda x: provider_labels[x],
                    label_visibility="collapsed"
                )
                
                new_provider = providers[selected_provider_idx]
                if new_provider != st.session_state.ai_provider:
                    st.session_state.ai_provider = new_provider
                    # Reset model selection when provider changes
                    if new_provider == "openai":
                        st.session_state.ai_model = "gpt-4o-mini"
                    else:
                        ollama_models = get_ollama_models()
                        if ollama_models:
                            st.session_state.ai_model = ollama_models[0]
                    st.rerun()
            
            with col2:
                st.write("**Model:**")
                
                if st.session_state.ai_provider == "openai":
                    openai_models = [
                        "gpt-4o",
                        "gpt-4o-mini", 
                        "gpt-4-turbo",
                        "gpt-3.5-turbo"
                    ]
                    
                    current_model_idx = 0
                    if st.session_state.ai_model in openai_models:
                        current_model_idx = openai_models.index(st.session_state.ai_model)
                    
                    selected_model = st.selectbox(
                        "Select Model",
                        openai_models,
                        index=current_model_idx,
                        label_visibility="collapsed"
                    )
                    st.session_state.ai_model = selected_model
                    
                elif st.session_state.ai_provider == "ollama":
                    ollama_models = get_ollama_models()
                    
                    if ollama_models:
                        current_model_idx = 0
                        if st.session_state.ai_model in ollama_models:
                            current_model_idx = ollama_models.index(st.session_state.ai_model)
                        
                        selected_model = st.selectbox(
                            "Select Model",
                            ollama_models,
                            index=current_model_idx,
                            label_visibility="collapsed"
                        )
                        st.session_state.ai_model = selected_model
                    else:
                        st.warning("No Ollama models found. Please install models using `ollama pull <model_name>`")
                        st.session_state.ai_model = "llama2"  # fallback
            
            # Status display
            st.markdown("---")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Status:**")
                if st.session_state.ai_provider == "openai":
                    # Check for API key in environment variables or secrets
                    import os
                    try:
                        api_key_available = (
                            os.environ.get("OPENAI_API_KEY") or 
                            (hasattr(st, 'secrets') and st.secrets.get("OPENAI_API_KEY", None)) or 
                            st.session_state.get("openai_api_key")
                        )
                    except:
                        api_key_available = os.environ.get("OPENAI_API_KEY") or st.session_state.get("openai_api_key")
                    
                    api_key_status = "🟢 Configured" if api_key_available else "🔴 Missing API Key"
                    st.write(f"OpenAI: {api_key_status}")
                else:
                    st.write(f"Ollama: {ollama_status}")
            
            with col2:
                st.write("**Current Selection:**")
                provider_name = "OpenAI" if st.session_state.ai_provider == "openai" else "Ollama"
                st.write(f"{provider_name} - {st.session_state.ai_model}")
            
            # Additional info removed - setup instructions will be in README
            
            st.markdown("</div>", unsafe_allow_html=True)


def get_current_ai_info() -> Dict[str, Any]:
    """Get current AI provider and model information."""
    return {
        "provider": st.session_state.get("ai_provider", "openai"),
        "model": st.session_state.get("ai_model", "gpt-4o-mini"),
        "ollama_available": is_ollama_available(),
        "ollama_models": get_ollama_models() if is_ollama_available() else []
    }
