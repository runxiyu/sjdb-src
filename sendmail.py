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
from configparser import ConfigParser
from typing import Optional
from pprint import pprint
import datetime
import zoneinfo
import argparse
import os

import requests
import msal  # type: ignore


def acquire_token(app: msal.PublicClientApplication, config: ConfigParser) -> str:
    result = app.acquire_token_by_username_password(
        config["credentials"]["username"],
        config["credentials"]["password"],
        scopes=config["credentials"]["scope"].split(" "),
    )

    if "access_token" in result:
        assert isinstance(result["access_token"], str)
        return result["access_token"]
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
    reply_to: Optional[str] = None,
) -> str:
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
            raise TypeError("Naive datetimes are no longer supported")
        utcwhen = when.astimezone(datetime.timezone.utc)
        isoval = utcwhen.isoformat(timespec="seconds").replace("+00:00", "Z")
        data["singleValueExtendedProperties"] = [
            {"id": "SystemTime 0x3FEF", "value": isoval}
        ]

    if not reply_to:
        response = requests.post(
            "https://graph.microsoft.com/v1.0/me/messages",
            json=data,
            headers={
                "Authorization": "Bearer %s" % token,
                "Prefer": 'IdType="ImmutableId"',
            },
            timeout=20,
        ).json()
    else:
        response = requests.post(
            "https://graph.microsoft.com/v1.0/me/messages/%s/createReply" % reply_to,
            json=data,
            headers={
                "Authorization": "Bearer %s" % token,
                "Prefer": 'IdType="ImmutableId"',
            },
            timeout=20,
        ).json()

    try:
        msgid = response["id"]
    except KeyError:
        pprint(response)
        raise ValueError("Unable to add email to drafts")

    assert isinstance(msgid, str)

    response2 = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages/%s/send" % msgid,
        headers={"Authorization": "Bearer " + token},
        timeout=20,
    )

    if response2.status_code != 202:
        pprint(response2.content.decode("utf-8", "replace"))
        raise ValueError(
            "Graph response to messages/%s/send returned something other than 202 Accepted"
            % response["id"],
        )

    return msgid


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily Bulletin Sender")
    parser.add_argument(
        "-d",
        "--date",
        default=None,
        help="the date of the bulletin to send, in local time, in YYYY-MM-DD; defaults to tomorrow",
    )
    parser.add_argument(
        "-r",
        "--reply",
        action="store_true",
        help="Reply to the previous bulletin when sending (BROKEN)",
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
    with open(html_filename, "r", encoding="utf-8") as html_fd:
        html = html_fd.read()

    app = msal.PublicClientApplication(
        config["credentials"]["client_id"],
        authority=config["credentials"]["authority"],
    )
    token = acquire_token(app, config)

    if not args.reply:
        a = sendmail(
            token,
            subject=config["sendmail"]["subject_format"]
            % date.strftime(config["sendmail"]["subject_date_format"]),
            body=html,
            to=config["sendmail"]["to_1"].split(" "),
            cc=config["sendmail"]["cc_1"].split(" "),
            bcc=config["sendmail"]["bcc_1"].split(" "),
            when=date.replace(
                hour=int(config["sendmail"]["hour"]),
                minute=int(config["sendmail"]["minute"]),
                second=0,
                microsecond=0,
            ),
            content_type="HTML",
            importance="Normal",
        )
        assert a
        with open("last-a.txt", "w") as fd:
            fd.write(a)
        b = sendmail(
            token,
            subject=config["sendmail"]["subject_format"]
            % date.strftime(config["sendmail"]["subject_date_format"]),
            body=html,
            to=config["sendmail"]["to_2"].split(" "),
            cc=config["sendmail"]["cc_2"].split(" "),
            bcc=config["sendmail"]["bcc_2"].split(" "),
            when=date.replace(
                hour=int(config["sendmail"]["hour"]),
                minute=int(config["sendmail"]["minute"]),
                second=0,
                microsecond=0,
            ),
            content_type="HTML",
            importance="Normal",
        )
        assert b
        with open("last-b.txt", "w") as fd:
            fd.write(b)
    else:
        with open("last-a.txt", "r") as fd:
            last_a = fd.read().strip()
        a = sendmail(
            token,
            subject=config["sendmail"]["subject_format"]
            % date.strftime(config["sendmail"]["subject_date_format"]),
            body=html,
            to=config["sendmail"]["to_1"].split(" "),
            cc=config["sendmail"]["cc_1"].split(" "),
            bcc=[
                w.strip()
                for w in open(config["sendmail"]["bcc_1_file"], "r").readlines()
                if w.strip()
            ],
            when=date.replace(
                hour=int(config["sendmail"]["hour"]),
                minute=int(config["sendmail"]["minute"]),
                second=0,
                microsecond=0,
            ),
            content_type="HTML",
            importance="Normal",
            reply_to=last_a,
        )
        assert a
        with open("last-a.txt", "w") as fd:
            fd.write(a)
        with open("last-b.txt", "r") as fd:
            last_b = fd.read().strip()
        b = sendmail(
            token,
            subject=config["sendmail"]["subject_format"]
            % date.strftime(config["sendmail"]["subject_date_format"]),
            body=html,
            to=config["sendmail"]["to_2"].split(" "),
            cc=config["sendmail"]["cc_2"].split(" "),
            bcc=[
                w.strip()
                for w in open(config["sendmail"]["bcc_2_file"], "r").readlines()
                if w.strip()
            ],
            when=date.replace(
                hour=int(config["sendmail"]["hour"]),
                minute=int(config["sendmail"]["minute"]),
                second=0,
                microsecond=0,
            ),
            content_type="HTML",
            importance="Normal",
            reply_to=last_b,
        )
        assert b
        with open("last-b.txt", "w") as fd:
            fd.write(b)


if __name__ == "__main__":
    main()
