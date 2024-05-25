#!/usr/bin/env python3
#
# Send the Daily Bulletin the next morning
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
import os
import requests
import datetime
import zoneinfo
import argparse
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
    parser = argparse.ArgumentParser(description="Daily Bulletin Sender")
    parser.add_argument(
        "--date",
        default=None,
        help="the date of the bulletin to send, in local time, in YYYY-MM-DD; defaults to tomorrow",
    )
    parser.add_argument(
        "--config", default="config.ini", help="path to the configuration file"
    )
    args = parser.parse_args()
    config = ConfigParser()
    config.read(args.config)
    if args.date:
        date = datetime.datetime.strptime(args.date, "%Y-%m-%d").replace(
            tzinfo=zoneinfo.ZoneInfo(config["general"]["timezone"])
        )
    else:
        date = datetime.datetime.now(
            zoneinfo.ZoneInfo(config["general"]["timezone"])
        ) + datetime.timedelta(days=1)

    os.chdir(config["general"]["build_path"])

    html_filename = "sjdb-%s.html" % date.strftime("%Y%m%d")
    with open(html_filename, "r") as html_fd:
        html = html_fd.read()

    app = msal.PublicClientApplication(
        config["credentials"]["client_id"],
        authority=config["credentials"]["authority"],
    )
    token = acquire_token(app, config)

    sendmail(
        token,
        subject=config["sendmail"]["subject_format"]
        % date.strftime(config["sendmail"]["subject_date_format"]),
        body=html,
        to=config["sendmail"]["to_1"].split(" "),
        cc=config["sendmail"]["cc_1"].split(" "),
        bcc=config["sendmail"]["bcc_1"].split(" "),
        when=date.replace(
            hour=int(config["test_sendmail"]["hour"]),
            minute=int(config["test_sendmail"]["minute"]),
            second=0,
            microsecond=0,
        ),
        content_type="HTML",
        importance="Normal",
    )
    sendmail(
        token,
        subject=config["sendmail"]["subject_format"]
        % date.strftime(config["sendmail"]["subject_date_format"]),
        body=html,
        to=config["sendmail"]["to_2"].split(" "),
        cc=config["sendmail"]["cc_2"].split(" "),
        bcc=config["sendmail"]["bcc_2"].split(" "),
        when=date.replace(
            hour=int(config["test_sendmail"]["hour"]),
            minute=int(config["test_sendmail"]["minute"]),
            second=0,
            microsecond=0,
        ),
        content_type="HTML",
        importance="Normal",
    )


if __name__ == "__main__":
    main()
