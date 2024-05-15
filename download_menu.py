from __future__ import annotations
import logging
import msal  # type: ignore
import requests
import datetime
from configparser import ConfigParser
from typing import Any, Optional, Iterable, Iterator
import json
from pprint import pprint
import re
import os
import email




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
    r = requests.post(
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
    assert type(r) is list
    assert type(r[0]) is dict
    return r


def filter_mail_results_by_sender(
    searched: Iterable[dict[str, Any]], sender: str
) -> Iterator[dict[str, Any]]:
    for i in searched:
        if i["resource"]["sender"]["emailAddress"]["address"].lower() == sender.lower():
            yield i


def filter_mail_results_by_subject_e(
    searched: Iterable[dict[str, Any]], subject_regex: str, srgf: str
) -> Iterator[tuple[dict[str, Any], list[str]]]:
    for i in searched:
        m = re.compile(subject_regex).match(i["resource"]["subject"])
        if m:
            yield (i, [m.group(int(x)) for x in srgf.split(" ")])


def get_message(
    token: str,
    hitid: str,
) -> bytes:
    return requests.get(
        "https://graph.microsoft.com/v1.0/me/messages/%s/$value" % hitid,
        headers={"Authorization": "Bearer " + token},
    ).content


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def main() -> None:
    # should be inputs
    # uh I'm using very inconsistent days and months and in the rest of the
    # program I'm using datetime objects, can someone make it consistent?

    target_month = 5
    target_day = 6
    target_year_str = datetime.datetime.now().strftime("%Y")

    config = ConfigParser()
    config.read("config.ini")
    token = acquire_token(config)
    searched = search_mail(token, config["weekly_menu"]["query_string"])
    for s in filter_mail_results_by_subject_e(
        filter_mail_results_by_sender(searched, config["weekly_menu"]["sender"]),
        config["weekly_menu"]["subject_regex"],
        srgf=config["weekly_menu"]["subject_regex_four_groups"],
    ):
        try:
            month = MONTHS[s[1][0]]
        except KeyError:
            raise ValueError("%s has a sussy month name" % s[0]["resource"]["subject"])
        try:
            day = int(s[1][1])
        except KeyError:
            raise ValueError("%s has a sussy day" % s[0]["resource"]["subject"])
        if not 1 < day < 32:
            raise ValueError("%s has a sussy day" % s[0]["resource"]["subject"])
        if month == target_month and day == target_day:
            break
    else:
        raise ValueError("No SJ-menu email found")
    msg_bytes = get_message(token, s[0]["hitId"])
    with open(
        os.path.join(
            config["general"]["build_path"],
            "menu-%s%02d%02d.eml"
            % (target_year_str, target_month, target_day),
        ),
        "wb",
    ) as wf:
        wf.write(msg_bytes)

    msg = email.message_from_bytes(msg_bytes)

    for part in msg.walk():
        if part.get_content_type() in ["application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/pdf"]:
            pl = part.get_payload(decode=True)
            ft = email.header.decode_header(part.get_filename())
            assert len(ft) == 1
            assert len(ft[0]) == 2
            if type(ft[0][0]) is bytes:
                filename = ft[0][0].decode(ft[0][1])
            elif type(ft[0][0]) is str:
                filename = ft[0][0]
            else:
                raise TypeError(ft, "not bytes or str???")

            if part.get_content_type() == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                if "EN" in filename:
                    lang = "en"
                elif "CH" or "CN" in filename:
                    lang = "zh"
                else:
                    raise ValueError("%s does not contain a language specification string", filename)
                formatted_filename = "menu-%s%02d%02d-%s.pptx" % (target_year_str, target_month, target_day, lang)
            elif part.get_content_type() == "application/pdf":
                formatted_filename = "menu-%s%02d%02d.pdf" % (target_year_str, target_month, target_day)

            with open(os.path.join(config["general"]["build_path"], formatted_filename), "wb") as w:
                w.write(pl)

    # TODO


if __name__ == "__main__":
    main()
