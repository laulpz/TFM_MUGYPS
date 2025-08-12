# config.py
import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="MUGYPS",
        page_icon="🧊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Fuerza la regeneración del sidebar
    st.sidebar.empty()
    
    # Añade tu propio header
    st.sidebar.header("MUGYPS")
    
    # CSS para eliminar cualquier rastro del título original
    st.markdown("""
    <style>
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
