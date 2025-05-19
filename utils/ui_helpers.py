# utils/ui_helpers.py
import streamlit as st
from contextlib import contextmanager
import time

@contextmanager
def show_loading_spinner(message="Processando..."):
    """Componente de loading personalizado com contexto"""
    with st.spinner(message):
        # Adiciona delay mínimo para evitar piscar rápido demais
        start_time = time.time()
        yield
        elapsed = time.time() - start_time
        if elapsed < 1:
            time.sleep(1 - elapsed)

def display_error_message(message, icon="🚨"):
    """Exibe mensagens de erro estilizadas"""
    st.markdown(f"""
        <div style="
            padding: 1rem;
            background-color: #ffebee;
            color: #b71c1c;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border: 1px solid #ffcdd2;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        ">
            <span style="font-size: 1.5rem">{icon}</span>
            <span>{message}</span>
        </div>
    """, unsafe_allow_html=True)

def display_success_message(message, icon="✅"):
    """Exibe mensagens de sucesso estilizadas"""
    st.markdown(f"""
        <div style="
            padding: 1rem;
            background-color: #e8f5e9;
            color: #1b5e20;
            border-radius: 0.5rem;
            margin: 1rem 0;
            border: 1px solid #c8e6c9;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        ">
            <span style="font-size: 1.5rem">{icon}</span>
            <span>{message}</span>
        </div>
    """, unsafe_allow_html=True)