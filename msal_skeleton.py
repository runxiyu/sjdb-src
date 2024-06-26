#!/usr/bin/env python3
#
# Skeleton to write new Daily Bulletin scripts that use the MSAL library
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
from configparser import ConfigParser
from typing import Any
import requests
import msal  # type: ignore


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
        assert isinstance(result["access_token"], str)
        return result["access_token"]
    raise ValueError("Authentication error in password login")


# TODO
def something(token: str) -> Any:
    return requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": "Bearer " + token},
        timeout=20,
    ).json()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    token = acquire_token(config)
    print(something(token))
    # TODO


if __name__ == "__main__":
    main()
