from __future__ import annotations
import logging
import msal  # type: ignore
import requests
import datetime
from pprint import pprint
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
        print(when.isoformat(timespec="seconds"))
        isoval = utcwhen.isoformat(timespec="seconds").replace("+00:00", "Z")
        print(isoval)
        data["singleValueExtendedProperties"] = [
            {"id": "SystemTime 0x3FEF", "value": isoval}
        ]

    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages",
        json=data,
        headers={"Authorization": "Bearer " + token},
    ).json()
    pprint(response)
    response2 = requests.post(
        "https://graph.microsoft.com/v1.0/me/messages/%s/send" % response["id"],
        headers={"Authorization": "Bearer " + token},
    )
    pprint(response2.text)


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
        when=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=int(config["test_sendmail"]["minutes_delay"])),
        content_type="HTML",
        importance="Normal",
    )


if __name__ == "__main__":
    main()
