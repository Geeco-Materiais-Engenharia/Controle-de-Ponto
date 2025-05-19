import pandas as pd
from datetime import datetime, timedelta
import locale
from typing import List, Dict
from utils.utils import converter_data_iso_para_ddmmaaaa, obter_dia_semana, converter_milisegundos_para_hhmm, minutes_to_str, str_to_minutes
import re

# Define o locale para datas em português do Brasil (Windows)
try:
    locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")
except locale.Error:
    # Para Linux/macOS ou fallback caso o locale não esteja disponível
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

def format_punches_as_dataframe(punches: List[Dict], holidays: List) -> pd.DataFrame:
    """
    Converts a list of punch records into a formatted pandas DataFrame.

    Args:
        punches (List[Dict]): A list of punch records returned from the Tangerino API.

    Returns:
        pd.DataFrame: A DataFrame containing formatted punch data for further analysis or export.

    Notes:
        - Assumes each record contains keys like 'employee', 'punchTime', etc.
        - This function should parse and format timestamps, extract names, and structure data appropriately.
    """
    rows = []
    date_emp_id = {}
    for p in punches:
        if f"{p["employee"]["id"]} - {p["date"]}" in date_emp_id:
            date_emp_id[f"{p["employee"]["id"]} - {p["date"]}"].append(p)
        else:
            date_emp_id[f"{p["employee"]["id"]} - {p["date"]}"] = [p]

    for chave in date_emp_id:
        p = date_emp_id[chave]
        rows.append({
        "ID colaborador": p[0]["employee"]["id"],
        "Colaborador": p[0]["employee"]["name"],
        "Data": converter_data_iso_para_ddmmaaaa(p[0]["date"]),
        "Dia da Semana": obter_dia_semana(p[0]["date"]),
        "Pontos": (
            "COMPENSAÇÃO FERIADO"
            if p[0].get("adjust") and p[0].get("adjustmentReason", {}).get("description") == "COMPENSAÇÃO FERIADO"
            else " | ".join(
                f'{datetime.fromtimestamp(punch["dateIn"] / 1000).strftime("%H:%M") if punch["dateIn"] is not None else ""} - {datetime.fromtimestamp(punch["dateOut"] / 1000).strftime("%H:%M") if punch["dateOut"] is not None else ""}'
                for punch in reversed(p)
            )
        ),

        # "Pontos": " | ".join(f'{datetime.fromtimestamp(punch["dateIn"] / 1000).strftime("%H:%M")} - {punch["dateOut"]}' for punch in p),
        "Ajustado": "Sim" if p[0]["adjust"] else "",
        "Trabalhadas": (
            "" if p[0].get("adjust") and p[0].get("adjustmentReason", {}).get("description") == "COMPENSAÇÃO FERIADO"
            else "Menos de 4 pontos batidos"
            if any(punch.get("dateIn") is None or punch.get("dateOut") is None for punch in p) or len(p) < 2 and obter_dia_semana(p[0]["date"]) not in ["sábado", "domingo"]
            else converter_milisegundos_para_hhmm(
                sum(
                    punch["dateOut"] - punch["dateIn"]
                    for punch in p
                    if punch.get("dateIn") is not None and punch.get("dateOut") is not None
                )
            )
        ),

        "Abono Previstas": "" if obter_dia_semana(p[0]["date"]) in ['sábado', 'domingo'] or p[0]["date"] in holidays else "08:48",
        "Saldo": "",
        })
        
        rows[-1]["Saldo"] = "Menos de 4 pontos batidos" if rows[-1]["Trabalhadas"] == "Menos de 4 pontos batidos" else minutes_to_str(
            str_to_minutes(rows[-1].get("Trabalhadas", "")) - str_to_minutes(rows[-1].get("Abono Previstas", ""))
        )
        
    return pd.DataFrame(rows)

def calcular_intervalo(pontos_str: str) -> str:
    """
    Calcula o intervalo entre o primeiro par de batidas e o segundo (se existirem).
    Exemplo de entrada: "05:55 - 11:40 | 12:42 - 16:41"
    """
    try:
        turnos = re.split(r' - |\s*\|\s*', pontos_str)

        if len(turnos) < 4:
            return ""  # Menos de dois períodos = não dá pra calcular intervalo

        if turnos[1] == turnos[2] and len(turnos) > 4:
            primeira_saida = turnos[3]
            segunda_entrada = turnos[4]
        else:
            primeira_saida = turnos[1]
            segunda_entrada = turnos[2]

        fmt = "%H:%M"
        t1 = datetime.strptime(primeira_saida.strip(), fmt)
        t2 = datetime.strptime(segunda_entrada.strip(), fmt)

        intervalo = t2 - t1
        if intervalo.total_seconds() < 0:
            intervalo += timedelta(days=1)  # Trata casos em que a hora vira meia-noite

        return f"{intervalo.seconds // 3600:02d}:{(intervalo.seconds % 3600) // 60:02d}"
    except Exception:
        return ""
    
def get_adjusts(df_punches: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas calculadas como Intervalo, Horas Extras Disponíveis e Horas Faltantes ao DataFrame de batidas.
    
    Args:
        df_punches (pd.DataFrame): DataFrame retornado pela função format_punches_as_dataframe.

    Returns:
        pd.DataFrame: DataFrame com novas colunas calculadas.
    """
    df = df_punches.copy()
    df["Intervalo"] = df["Pontos"].apply(calcular_intervalo)
    
    # Converte saldo e abono previstos para minutos
    df["Saldo_min"] = df["Saldo"].apply(lambda x: str_to_minutes(x) if isinstance(x, str) and x is not "Menos de 4 pontos batidos" else 0)
    df["Abono_min"] = df["Abono Previstas"].apply(lambda x: str_to_minutes(x) if isinstance(x, str) else 0)
    
    LIMITE_EXTRA = 117  # 1:57 em minutos

    # Cria coluna de horas extras disponíveis
    df["Hrs Extras Excedentes"] = df.apply(
        lambda row: minutes_to_str(row["Saldo_min"] - LIMITE_EXTRA) 
        if row["Abono_min"] > 0 and row["Saldo_min"] > LIMITE_EXTRA else "", 
        axis=1
    )

    # Cria coluna de horas faltantes para atingir 1:57
    df["Hrs Extras Disponíveis"] = df.apply(
        lambda row: minutes_to_str(LIMITE_EXTRA - row["Saldo_min"]) 
        if row["Abono_min"] > 0 and row["Saldo_min"] < LIMITE_EXTRA and row["Saldo"] is not "Menos de 4 pontos batidos" and row["Pontos"] is not "COMPENSAÇÃO FERIADO" and not row["Saldo"].startswith("-") else "", 
        axis=1
    )

    # Remove colunas temporárias
    df.drop(columns=["Saldo_min", "Abono_min"], inplace=True)
    
    return df

def adjusted_punches(punches: List[Dict]) -> pd.DataFrame:
    """
    Ajusta os pontos de acordo com as regras de compensação e retorna um DataFrame formatado.

    Args:
        punches (List[Dict]): Lista de pontos retornados pela API do Tangerino.
        holidays (List): Lista de feriados.

    Returns:
        pd.DataFrame: DataFrame contendo os dados ajustados dos pontos.
    """
    df = punches.copy()

    # Formata os pontos como DataFrame
    def str_to_minutes(time_str):
        if not time_str or time_str in ["", None]:
            return 0
        # negative = time_str.startswith("-")
        h, m = map(int, time_str.strip("+").split(":"))
        minutes = h * 60 + m
        return minutes
    
    def minutes_to_str(minutes):
        sign = "-" if minutes < 0 else ""
        minutes = abs(minutes)
        return f"{sign}{minutes // 60:02}:{minutes % 60:02}"
    
    def somar_minutos_hora_str(hora_str, minutos):
        total_minutes = str_to_minutes(hora_str) + minutos
        return minutes_to_str(total_minutes)
    
    total_minutes = df["Hrs Extras Excedentes"].apply(str_to_minutes).sum()

    for idx, row in df.iterrows():
        # Ajustando tempo de intervalo para ser no mínimo 1:00
        if str_to_minutes(row["Intervalo"]) < 60:
            # Ajustando o intervalo para 1:00
            pontos = row["Pontos"]
            blocos = pontos.split(" | ")
            minutes_to_reduce = 60 - str_to_minutes(row["Intervalo"])

            if len(blocos) > 1:
                entrada_saida = blocos[0].split(" - ")
                if len(entrada_saida) == 2:
                    nova_entrada = somar_minutos_hora_str(entrada_saida[0], -minutes_to_reduce)
                    nova_saida = somar_minutos_hora_str(entrada_saida[-1], -minutes_to_reduce)
                    nova_bloco = f"{nova_entrada} - {nova_saida}"
                    blocos[0] = nova_bloco
                    df.at[idx, "Pontos"] = " | ".join(blocos)

                    df.at[idx, "Intervalo"] = "01:00"
                    df.at[idx, "Ajustado"] = "AJUSTAR"

        # Ajustando horas extras excedentes
        extra = row["Hrs Extras Disponíveis"]

        if extra and total_minutes > 0:
            minutos_extra = str_to_minutes(extra)
            minutos_para_somar = minutos_extra if total_minutes >= minutos_extra else total_minutes
            total_minutes -= minutos_para_somar

            # Manipulando a coluna Pontos
            pontos = row["Pontos"]
            blocos = pontos.split(" | ")

            if len(blocos) > 1:
                entrada_saida = blocos[-1].split(" - ")
                if len(entrada_saida) == 2:
                    # Ajustando o ponto de saída para receber as horas extras excedentes
                    nova_saida = somar_minutos_hora_str(entrada_saida[-1], minutos_para_somar)
                    nova_bloco = f"{entrada_saida[0]} - {nova_saida}"
                    blocos[1] = nova_bloco
                    df.at[idx, "Pontos"] = " | ".join(blocos)

                    # Ajustando as horas extras disponíveis
                    if total_minutes < minutos_extra:
                        df.at[idx, "Hrs Extras Disponíveis"] = minutes_to_str(minutos_extra - minutos_para_somar)
                    else:
                        df.at[idx, "Hrs Extras Disponíveis"] = ""

                    df.at[idx, "Ajustado"] = "AJUSTAR"

        # Ajustando ponto de saída com horas extras excedentes
        if df.at[idx, "Hrs Extras Excedentes"] != "":
            pontos = row["Pontos"]
            blocos = pontos.split(" | ")
            if len(blocos) > 1:
                entrada_saida = blocos[-1].split(" - ")
                if len(entrada_saida) == 2:
                    nova_saida = somar_minutos_hora_str(entrada_saida[-1], -str_to_minutes(df.at[idx, "Hrs Extras Excedentes"]))
                    nova_bloco = f"{entrada_saida[0]} - {nova_saida}"
                    blocos[1] = nova_bloco
                    df.at[idx, "Pontos"] = " | ".join(blocos)

                    df.at[idx, "Ajustado"] = "AJUSTAR"
                    df.at[idx, "Hrs Extras Excedentes"] = ""

    return df