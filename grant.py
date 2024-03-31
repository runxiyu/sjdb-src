from __future__ import annotations
import logging
import msal  # type: ignore
import requests
from pprint import pprint
from configparser import ConfigParser
from typing import Any

# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger("msal").setLevel(logging.INFO)


def acquire_token_interactive(
    app: msal.PublicClientApplication, config: ConfigParser
) -> str:
    result = app.acquire_token_interactive(
        config["credentials"]["scope"].split(" "),
        login_hint=config["credentials"]["username"],
    )

    if "access_token" in result:
        assert type(result["access_token"]) is str
        return result["access_token"]
    else:
        raise ValueError(
            "Authentication error while trying to interactively acquire a token"
        )


def test_login(
    app: msal.PublicClientApplication, config: ConfigParser
) -> dict[str, Any]:
    result = app.acquire_token_by_username_password(
        config["credentials"]["username"],
        config["credentials"]["password"],
        scopes=config["credentials"]["scope"].split(" "),
    )

    if "access_token" in result:
        token = result["access_token"]
    else:
        raise ValueError("Authentication error in password login")

    graph_response = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": "Bearer " + token},
    ).json()
    assert type(graph_response) is dict
    return graph_response


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    app = msal.PublicClientApplication(
        config["credentials"]["client_id"],
        authority=config["credentials"]["authority"],
    )
    acquire_token_interactive(app, config)
    pprint(test_login(app, config))


if __name__ == "__main__":
    main()
