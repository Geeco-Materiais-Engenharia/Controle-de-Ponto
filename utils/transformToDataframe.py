import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from utils.utils import converter_data_iso_para_ddmmaaaa, obter_dia_semana, converter_milisegundos_para_hhmm, minutes_to_str, str_to_minutes
import re
from babel.dates import format_date, format_datetime, format_time
from babel import Locale
import pytz

brazil_tz = pytz.timezone('America/Sao_Paulo')

def format_punch_time(ts, locale):
    if ts is None:
        return ""
    
    dt_utc = datetime.utcfromtimestamp(ts / 1000).replace(tzinfo=timezone.utc)
    
    dt_brazil = dt_utc.astimezone(brazil_tz)
    
    return format_time(dt_brazil, format="short", locale=locale)

# Configura o locale para português do Brasil
locale = Locale('pt', 'BR')

def format_punches_as_dataframe(punches: List[Dict], holidays: List) -> pd.DataFrame:
    """
    Converts a list of punch records into a formatted pandas DataFrame.

    Args:
        punches (List[Dict]): A list of punch records returned from the Tangerino API.
        holidays (List): List of holidays dates.

    Returns:
        pd.DataFrame: A DataFrame containing formatted punch data for further analysis or export.

    Notes:
        - Assumes each record contains keys like 'employee', 'punchTime', etc.
        - This function should parse and format timestamps, extract names, and structure data appropriately.
    """
    rows = []
    date_emp_id = {}
    for p in punches:
        if f"{p['employee']['id']} - {p['date']}" in date_emp_id:
            date_emp_id[f"{p['employee']['id']} - {p['date']}"].append(p)
        else:
            date_emp_id[f"{p['employee']['id']} - {p['date']}"] = [p]

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
                    f'{format_punch_time(punch["dateIn"], locale)} - {format_punch_time(punch["dateOut"], locale)}'
                    for punch in reversed(p)
                )
            ),
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
    Calcula o maior intervalo entre as batidas dentro do horário comercial (08:00-17:48).
    Exemplo de entrada: "05:55 - 11:40 | 12:42 - 16:41"

    Args:
        pontos_str (str): String com os pontos no formato "HH:MM - HH:MM | HH:MM - HH:MM"

    Returns:
        str: Intervalo formatado como "HH:MM" ou string vazia se não houver intervalos válidos.
    """
    try:
        if not pontos_str or pontos_str == "COMPENSAÇÃO FERIADO":
            return ""
            
        # Extrai todos os horários da string
        horarios = re.findall(r'(\d{2}:\d{2})', pontos_str)
        if len(horarios) < 2:
            return ""
            
        # Se houver apenas 2 horários (uma entrada e uma saída), não há intervalo
        if len(horarios) == 2:
            return ""
            
        # Calcula todos os intervalos entre saídas e entradas subsequentes
        intervalos = []
        fmt = "%H:%M"
        hora_inicio_comercial = datetime.strptime("08:00", fmt)
        hora_fim_comercial = datetime.strptime("17:48", fmt)
        
        for i in range(1, len(horarios)-1, 2):
            saida = horarios[i].strip()
            entrada = horarios[i+1].strip()
            
            t_saida = datetime.strptime(saida, fmt)
            t_entrada = datetime.strptime(entrada, fmt)
            
            # Se o intervalo estiver TOTALMENTE fora do horário comercial, ignora
            if (t_saida < hora_inicio_comercial and t_entrada < hora_inicio_comercial) or \
               (t_saida > hora_fim_comercial and t_entrada > hora_fim_comercial):
                continue
            
            # Calcula o intervalo
            intervalo = t_entrada - t_saida
            if intervalo.total_seconds() < 0:
                intervalo += timedelta(days=1)  # Ajuste para passar meia-noite
            
            intervalos.append(intervalo)
            
        if not intervalos:
            return ""
            
        # Pega o maior intervalo (mesmo que seja menor que 58 minutos)
        maior_intervalo = max(intervalos)
        horas = maior_intervalo.seconds // 3600
        minutos = (maior_intervalo.seconds % 3600) // 60
        
        return f"{horas:02d}:{minutos:02d}"
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
    df["Saldo_min"] = df["Saldo"].apply(lambda x: str_to_minutes(x) if isinstance(x, str) and x != "Menos de 4 pontos batidos" else 0)
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
        if row["Abono_min"] > 0 and row["Saldo_min"] < LIMITE_EXTRA and row["Saldo"] != "Menos de 4 pontos batidos" and row["Pontos"] != "COMPENSAÇÃO FERIADO" and not row["Saldo"].startswith("-") else "", 
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

    Returns:
        pd.DataFrame: DataFrame contendo os dados ajustados dos pontos.
    """
    df = punches.copy()

    def str_to_minutes(time_str):
        """Helper function to convert time string to minutes"""
        if not time_str or time_str in ["", None]:
            return 0
        h, m = map(int, time_str.strip("+").split(":"))
        minutes = h * 60 + m
        return minutes
    
    def minutes_to_str(minutes):
        """Helper function to convert minutes to time string"""
        sign = "-" if minutes < 0 else ""
        minutes = abs(minutes)
        return f"{sign}{minutes // 60:02}:{minutes % 60:02}"
    
    def somar_minutos_hora_str(hora_str, minutos):
        """Helper function to add minutes to a time string"""
        total_minutes = str_to_minutes(hora_str) + minutos
        return minutes_to_str(total_minutes)
    
    total_minutes = df["Hrs Extras Excedentes"].apply(str_to_minutes).sum()

    for idx, row in df.iterrows():
        # Ajustando tempo de intervalo para ser no mínimo 1:00
        if str_to_minutes(row["Intervalo"]) < 58:
            pontos = row["Pontos"]
            blocos = pontos.split(" | ")
            minutes_to_reduce = 58 - str_to_minutes(row["Intervalo"])

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

            pontos = row["Pontos"]
            blocos = pontos.split(" | ")

            if len(blocos) > 1:
                entrada_saida = blocos[-1].split(" - ")
                if len(entrada_saida) == 2:
                    nova_saida = somar_minutos_hora_str(entrada_saida[-1], minutos_para_somar)
                    nova_bloco = f"{entrada_saida[0]} - {nova_saida}"
                    blocos[1] = nova_bloco
                    df.at[idx, "Pontos"] = " | ".join(blocos)

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