#!/usr/bin/env python3
#
# Use the Outlook REST API to delay sending an email
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
import datetime
from configparser import ConfigParser
from typing import Any, Optional


def acquire_token(app: msal.PublicClientApplication, config: ConfigParser) -> str:
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


def sendmail(
    token: str,
    subject: str,
    body: str,
    to: list[str],
    bcc: list[str],
    cc: list[str],
    when: Optional[datetime.datetime] = None,
    content_type: str = "HTML",
    importance: str = "Normal",
) -> None:
    data = {
        "subject": subject,
        "importance": importance,
        "body": {"contentType": content_type, "content": body},
        "toRecipients": [{"emailAddress": {"address": a}} for a in to],
        "ccRecipients": [{"emailAddress": {"address": a}} for a in cc],
        "bccRecipients": [{"emailAddress": {"address": a}} for a in bcc],
    }

    if when is not None:
        if when.tzinfo is None:
            raise ValueError("Naive datetimes are no longer supported")
        utcwhen = when.astimezone(datetime.timezone.utc)
        isoval = utcwhen.isoformat(timespec="seconds").replace("+00:00", "Z")
        data["singleValueExtendedProperties"] = [
            {"id": "SystemTime 0x3FEF", "value": isoval}
        ]

    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages",
        json=data,
        headers={"Authorization": "Bearer " + token},
    ).json()
    response2 = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages/%s/send" % response["id"],
        headers={"Authorization": "Bearer " + token},
    )
    if response2.status_code != 202:
        raise ValueError(
            "Graph response to messages/%s/send returned someething other than 202 Accepted"
            % response["id"],
            response2,
        )
    # TODO: Handle more errors


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    app = msal.PublicClientApplication(
        config["credentials"]["client_id"],
        authority=config["credentials"]["authority"],
    )
    token = acquire_token(app, config)
    sendmail(
        token,
        subject=config["test_sendmail"]["subject"],
        body=open(config["test_sendmail"]["local_html_path"], "r").read(),
        to=config["test_sendmail"]["to"].split(" "),
        cc=config["test_sendmail"]["cc"].split(" "),
        bcc=config["test_sendmail"]["bcc"].split(" "),
        when=datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=int(config["test_sendmail"]["minutes_delay"])),
        content_type="HTML",
        importance="Normal",
    )


if __name__ == "__main__":
    main()
