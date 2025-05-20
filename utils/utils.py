from datetime import datetime
import pandas as pd
from babel.dates import format_date, format_datetime, format_time
from babel import Locale

# Configura o locale para português do Brasil
locale = Locale('pt', 'BR')

def converter_data_para_ms(data: datetime) -> int:
    """Converte datetime para milissegundos desde epoch."""
    return int(data.timestamp() * 1000)

def converter_data_iso_para_ddmmaaaa(data_iso: str) -> str:
    """
    Converte uma data no formato ISO (YYYY-MM-DD) para o formato brasileiro (DD/MM/AAAA) usando Babel.

    Args:
        data_iso (str): Data no formato ISO, como '2025-05-12'.

    Returns:
        str: Data formatada no padrão brasileiro, como '12/05/2025'.

    Raises:
        ValueError: Se a string fornecida não for uma data válida no formato ISO.
    """
    try:
        data = datetime.strptime(data_iso, "%Y-%m-%d")
        return format_date(data, format='short', locale=locale)
    except Exception as e:
        raise ValueError(f"Data inválida ou em formato incorreto: '{data_iso}'. Esperado 'YYYY-MM-DD'.") from e

def obter_dia_semana(data_iso: str) -> str:
    """
    Retorna o nome completo do dia da semana em português para uma data no formato ISO (YYYY-MM-DD).

    Args:
        data_iso (str): Data no formato ISO, por exemplo, '2025-05-12'.

    Returns:
        str: Nome do dia da semana em português, por exemplo, 'segunda-feira'.

    Raises:
        ValueError: Se a string fornecida não for uma data válida no formato ISO.
    """
    try:
        data = datetime.strptime(data_iso, "%Y-%m-%d")
        return format_date(data, format='full', locale=locale).split(',')[0].lower()
    except ValueError:
        raise ValueError(f"Data inválida ou em formato incorreto: '{data_iso}'. Esperado 'YYYY-MM-DD'.")

def converter_milisegundos_para_hhmm(ms: int) -> str:
    """
    Converte milissegundos para o formato 'HH:MM', com minutos arredondados.

    Args:
        ms (int): Tempo em milissegundos.

    Returns:
        str: Tempo formatado como 'HH:MM'.
    """
    if ms < 0:
        raise ValueError("O tempo em milissegundos não pode ser negativo.")

    # Converter para minutos (com fração) e arredondar
    total_minutos = round(ms / 1000 / 60)
    
    horas = total_minutos // 60
    minutos = total_minutos % 60

    return f"{horas:02d}:{minutos:02d}"

def str_to_minutes(s):
    if not s: return 0
    h, m = map(int, s.split(":"))
    return h * 60 + m

def minutes_to_str(mins):
    sign = "-" if mins < 0 else "+"
    mins = abs(mins)
    return f"{sign}{mins // 60:02}:{mins % 60:02}"

from typing import List, Dict
from datetime import datetime, timedelta
from api.api import get_punch

def fetch_punches_in_chunks(start_ms: int, end_ms: int, colaborador_id, token: str) -> List[Dict]:
    """
    Busca os registros de ponto em blocos de 8 dias, evitando sobrecarga na API.

    Args:
        start_ms (int): Timestamp inicial em milissegundos.
        end_ms (int): Timestamp final em milissegundos.
        colaborador_id: ID do colaborador.
        token (str): Token de autenticação.

    Returns:
        List[Dict]: Lista acumulada de registros de ponto.
    """
    punches = []
    current_start = datetime.fromtimestamp(start_ms / 1000)
    final_end = datetime.fromtimestamp(end_ms / 1000)

    while current_start < final_end:
        current_end = current_start + timedelta(days=8)

        # Limita a data final ao limite real
        if current_end > final_end:
            current_end = final_end

        # Converte para milissegundos
        current_start_ms = int(current_start.timestamp() * 1000)
        current_end_ms = int(current_end.timestamp() * 1000)

        # Busca os dados para o intervalo atual
        chunk = get_punch(current_start_ms, current_end_ms, colaborador_id, token)
        punches.extend(chunk)

        # Avança para o próximo bloco
        current_start = current_end

    return punches