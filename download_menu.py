from __future__ import annotations
import logging
import msal  # type: ignore
import requests
import datetime
from configparser import ConfigParser
from typing import Any, Optional, Iterable
import json
from pprint import pprint
import re


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
def search_mail(token: str, query_string: str) -> list[dict[str, Any]]:
    return requests.post(
        "https://graph.microsoft.com/v1.0/search/query",
        headers={"Authorization": "Bearer " + token},
        json={
            "requests": [
                {
                    "entityTypes": ["message"],
                    "query": {"queryString": query_string},
                    "from": 0,
                    "size": 15,
                    "enableTopResults": True,
                }
            ]
        },
    ).json()["value"][0]["hitsContainers"][0]["hits"]


def filter_mail_results_by_sender(searched: Iterable[dict[str, Any]], sender: str):
    for i in searched:
        if i["resource"]["sender"]["emailAddress"]["address"].lower() == sender.lower():
            yield i


def filter_mail_results_by_subject_e(
    searched: Iterable[dict[str, Any]], subject_regex: str, srgf: str
):
    for i in searched:
        m = re.compile(subject_regex).match(i["resource"]["subject"])
        if m:
            yield (i["resource"], [m.group(int(x)) for x in srgf.split(" ")])


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    token = acquire_token(config)
    searched = search_mail(token, config["weekly_menu"]["query_string"])
    print(
        [
            s
            for s in filter_mail_results_by_subject_e(
                filter_mail_results_by_sender(
                    searched, config["weekly_menu"]["sender"]
                ),
                config["weekly_menu"]["subject_regex"],
                srgf=config["weekly_menu"]["subject_regex_four_groups"],
            )
        ]
    )
    # TODO


if __name__ == "__main__":
    main()
