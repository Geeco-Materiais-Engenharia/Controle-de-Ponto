import requests
from dotenv import load_dotenv
from typing import List, Dict
from datetime import datetime

# Carregar variáveis do arquivo .env
load_dotenv()

def get_colaboradores(token: str) -> List[str]:
    """
    Retorna uma lista de colaboradores disponíveis.

    Returns:
        List[str]: Lista de colaboradores.
    """
    
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    URL = "https://api.tangerino.com.br/api/employer/employee/find-all"

    try:
        response = requests.get(url=URL, headers=headers)
        response.raise_for_status()
        return response.json().get("content", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar colaboradores: {e}")
        return []

def get_punch(start_ms: int, end_ms: int, colaborador, token: str) -> List[Dict]:
    """
    Gets all employee punches within the given time range.

    Args:
        start_ms (int): Start timestamp in milliseconds.
        end_ms (int): End timestamp in milliseconds.

    Returns:
        List[Dict]: A list of punch records. Returns an empty list if the request fails or no data is found.

    Raises:
        Value Error: If the API token is not found in the environment variables.
    """

    URL = f"https://apis.tangerino.com.br/punch/?employeeId={colaborador}&endDate={end_ms}&startDate={start_ms}"

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url=URL, headers=headers)
        response.raise_for_status()
        return response.json().get("content", [])
    except requests.exceptions.RequestException as e:
        print(f'Erro ao buscar pontos: {e}')
        return []

def get_holidays_between(start_ms: int, end_ms: int, token: str) -> List[str]:
    """
    Busca e retorna uma lista de feriados entre os anos da data inicial e final.

    Args:
        start_ms (int): Timestamp inicial em milissegundos.
        end_ms (int): Timestamp final em milissegundos.

    Returns:
        List[str]: Lista de datas de feriados no formato "YYYY-MM-DD".
    """

    start_year = datetime.fromtimestamp(start_ms / 1000).year
    end_year = datetime.fromtimestamp(end_ms / 1000).year

    holidays = []

    for year in range(start_year, end_year + 1):
        try:
            url = f"https://api.tangerino.com.br/api/employer/holiday-calendar/?year={year}"
            headers = {
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            year_holidays = data["item"][0]["holidays"]
            holidays.extend([holiday["date"] for holiday in year_holidays])
        except Exception as e:
            print(f"Erro ao buscar feriados para {year}: {e}")

    return holidays



