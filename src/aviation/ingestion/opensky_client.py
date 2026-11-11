
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

TOKEN_URL = (
    "https://auth.opensky-network.org/"
    "auth/realms/opensky-network/protocol/openid-connect/token"
)

STATES_URL = "https://opensky-network.org/api/states/all"

# Area aproximada do estado de Sao Paulo
REGION = {
    "lamin": -25.3,
    "lamax": -19.7,
    "lomin": -53.2,
    "lomax": -44.0,
}


def get_access_token():
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("Credenciais OpenSky nao configuradas.")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=20,
    )

    response.raise_for_status()

    token = response.json().get("access_token")

    if not token:
        raise ValueError("Token de acesso nao recebido.")

    return token


def get_aircraft_states():
    token = get_access_token()

    response = requests.get(
        STATES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params=REGION,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Resposta inesperada da OpenSky.")

    states = data.get("states")

    if states is not None and not isinstance(states, list):
        raise ValueError("Formato invalido para states.")

    return data


if __name__ == "__main__":
    try:
        result = get_aircraft_states()

        aircraft = result.get("states") or []

        print("Consulta OpenSky realizada com sucesso.")
        print(f"Timestamp: {result.get('time')}")
        print(f"Aeronaves encontradas: {len(aircraft)}")

    except requests.exceptions.HTTPError as error:
        status = error.response.status_code
        print(f"Erro HTTP OpenSky: {status}")

    except requests.exceptions.RequestException as error:
        print(f"Erro de comunicacao: {type(error).__name__}")

    except ValueError as error:
        print(f"Erro de validacao: {error}")
