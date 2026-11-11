
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

TOKEN_URL = (
    "https://auth.opensky-network.org/"
    "auth/realms/opensky-network/protocol/openid-connect/token"
)


def test_authentication():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "Credenciais OpenSky ausentes no arquivo .env"
        )

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=20,
    )

    response.raise_for_status()

    token = response.json().get("access_token")

    if not token:
        raise RuntimeError(
            "A resposta nao contem um access_token."
        )

    print("Autenticacao OpenSky realizada com sucesso.")
    print("Token recebido e validado quanto a sua presenca.")


if __name__ == "__main__":
    test_authentication()
