# app.py
import streamlit as st
from components.login_components import show_login_form
from components.main_dashboard import show_date_selector, show_employee_selector, display_dataframes
from api.api import get_colaboradores, get_holidays_between
from utils.utils import converter_data_para_ms, fetch_punches_in_chunks
from datetime import datetime

# Configuração inicial da página
st.set_page_config(
    page_title="Controle de Ponto - Tangerino v2",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    }
)

# Esconder elementos padrão do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def main_app():
    st.title("Controle de Ponto")

    token = st.session_state.get("token")
    if not token:
        st.error("Token não encontrado. Faça login novamente.")
        return
    
    start_date, end_date = show_date_selector()
    colaboradores = get_colaboradores(token)
    colaborador_id = show_employee_selector(colaboradores)
    
    if start_date > end_date:
        return st.error("Data Inicial não pode ser maior que Data Final")
    
    start_ms = converter_data_para_ms(datetime.combine(start_date, datetime.min.time()))
    end_ms = converter_data_para_ms(datetime.combine(end_date, datetime.max.time()))
    
    with st.spinner("Buscando dados da API..."):
        punches = fetch_punches_in_chunks(start_ms, end_ms, colaborador_id, token)
        holidays = get_holidays_between(start_ms, end_ms, token)
    
    display_dataframes(punches, holidays, colaborador_id)

if __name__ == "__main__":
    if not st.session_state.get("authenticated"):
        show_login_form()
    else:
        main_app()