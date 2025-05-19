# components/main_dashboard.py
import streamlit as st
from datetime import datetime
from utils.transformToDataframe import format_punches_as_dataframe, get_adjusts, adjusted_punches

def show_date_selector():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Data Inicial", value=datetime.today())
    with col2:
        end_date = st.date_input("Data Final", value=datetime.today())
    return start_date, end_date

def show_employee_selector(colaboradores):
    nomes_para_ids = {c['name']: c['id'] for c in colaboradores}
    selected = st.selectbox("Colaborador", options=list(nomes_para_ids.keys()))
    return nomes_para_ids[selected]

def display_dataframes(punches, holidays, colaborador_id):
    with st.spinner("Processando dados..."):
        df_punches = format_punches_as_dataframe(punches, holidays)
        error_df = get_adjusts(df_punches)
        adjusted_df = adjusted_punches(error_df)
        
        styled_error = error_df.style.applymap(style_error_cells, subset=["Trabalhadas", "Saldo"])
        styled_adjusted = adjusted_df.style.applymap(style_adjusted_cells, subset=["Ajustado"])
        
        st.subheader("Pré Ajustes")
        st.dataframe(styled_error, use_container_width=True)
        
        st.subheader("Pontos Ajustados")
        st.dataframe(styled_adjusted, use_container_width=True)

def style_error_cells(val):
    return 'background-color: red; color: white;' if val == "Menos de 4 pontos batidos" else ''

def style_adjusted_cells(val):
    return 'background-color: #4CAF50; color: white;' if val == "AJUSTADO" else ''