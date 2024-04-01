from __future__ import annotations
import logging
import msal  # type: ignore
import requests
import datetime
from configparser import ConfigParser
from typing import Any, Optional
import json


def acquire_token(config: ConfigParser) -> str:
    app = msal.PublicClientApplication(
        config["credentials"]["client_id"],
        authority=config["credentials"]["authority"],
    )
    result = app.acquire_token_by_username_password(
        config["credentials"]["username"],
        config["credentials"]["password"],
        scopes=config["credentials"]["scope"].split(" "),
    )

    if "access_token" in result:
        assert type(result["access_token"]) is str
        return result["access_token"]
    else:
        raise ValueError("Authentication error in password login")


# TODO
def something(token: str) -> dict[str, Any]:
    return requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": "Bearer " + token},
    ).json()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    token = acquire_token(config)
    print(something(token))
    # TODO


if __name__ == "__main__":
    main()
