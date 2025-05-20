# components/main_dashboard.py
import streamlit as st
from datetime import datetime
from utils.transformToDataframe import format_punches_as_dataframe, get_adjusts, adjusted_punches
import pandas as pd

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
        # 1) monta o df inicial e converte a Data para datetime
        df_punches = format_punches_as_dataframe(punches, holidays)
        df_punches["Data"] = pd.to_datetime(df_punches["Data"], format="%d/%m/%Y")
        df_punches = df_punches.sort_values("Data")

        # 2) aplica os cálculos de ajuste
        error_df = get_adjusts(df_punches)
        error_df["Data"] = pd.to_datetime(error_df["Data"], format="%d/%m/%Y")
        error_df = error_df.sort_values("Data")

        adjusted_df = adjusted_punches(error_df)
        adjusted_df["Data"] = pd.to_datetime(adjusted_df["Data"], format="%d/%m/%Y")
        adjusted_df = adjusted_df.sort_values("Data")

        # 3) cria os Stylers mantendo datetime64 mas formatando a exibição
        styled_error = (
            error_df
            .style
            .format({"Data": lambda dt: dt.strftime("%d/%m/%Y")})
            .applymap(style_error_cells, subset=["Trabalhadas", "Saldo"])
        )
        styled_adjusted = (
            adjusted_df
            .style
            .format({"Data": lambda dt: dt.strftime("%d/%m/%Y")})
            .applymap(style_adjusted_cells, subset=["Ajustado"])
        )

        # 4) exibe no Streamlit (ordenável)
        st.subheader("Pré Ajustes")
        st.write(styled_error, use_container_width=True)

        st.subheader("Pontos Ajustados")
        st.write(styled_adjusted, use_container_width=True)
def style_error_cells(val):
    return 'background-color: red; color: white;' if val == "Menos de 4 pontos batidos" else ''

def style_adjusted_cells(val):
    return 'background-color: #4CAF50; color: white;' if val == "AJUSTADO" else ''