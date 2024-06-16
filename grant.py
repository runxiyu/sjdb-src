#!/usr/bin/env python3
#
# Request user consent for delegated permissions to manage the Daily Bulletin
# Copyright (C) 2024 Runxi Yu <https://runxiyu.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

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
        assert isinstance(result["access_token"], str)
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
        raise ValueError("Authentication error in password login", result)

    graph_response = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": "Bearer " + token},
        timeout=20,
    ).json()
    assert isinstance(graph_response, dict)
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
