#!/usr/bin/env python3
#
# Common functions for the Daily Bulletin Build System
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

from typing import Any, Iterable, Iterator
import logging
import re
import base64
import shutil

import requests
import msal  # type: ignore

def acquire_token(
    graph_client_id: str,
    graph_authority: str,
    graph_username: str,
    graph_password: str,
    graph_scopes: list[str],
) -> str:
    app = msal.PublicClientApplication(
        graph_client_id,
        authority=graph_authority,
    )
    result = app.acquire_token_by_username_password(graph_username, graph_password, scopes=graph_scopes)

    if "access_token" in result:
        assert isinstance(result["access_token"], str)
        return result["access_token"]
    raise ValueError("Authentication error in password login")

def search_mail(token: str, query_string: str) -> list[dict[str, Any]]:
    hits = requests.post(
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
        timeout=20,
    ).json()["value"][
        0
    ]["hitsContainers"][
        0
    ]["hits"]
    assert isinstance(hits, list)
    assert isinstance(hits[0], dict)
    return hits

def encode_sharing_url(url: str) -> str:
    return "u!" + base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def download_share_url(token: str, url: str, local_filename: str, chunk_size: int = 65536) -> None:

    download_direct_url = requests.get(
        "https://graph.microsoft.com/v1.0/shares/%s/driveItem" % encode_sharing_url(url),
        headers={"Authorization": "Bearer " + token},
        timeout=20,
    ).json()["@microsoft.graph.downloadUrl"]

    with requests.get(
        download_direct_url,
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept-Encoding": "identity",
        },
        stream=True,
        timeout=20,
    ) as r:
        with open(local_filename, "wb") as fd:
            shutil.copyfileobj(r.raw, fd)
            fd.flush()

def filter_mail_results_by_sender(original: Iterable[dict[str, Any]], sender: str) -> Iterator[dict[str, Any]]:
    for hit in original:
        if hit["resource"]["sender"]["emailAddress"]["address"].lower() == sender.lower():
            yield hit


# TODO: Potentially replace this with a pattern-match based on strptime().
def filter_mail_results_by_subject_regex_groups(
    original: Iterable[dict[str, Any]],
    subject_regex: str,
    subject_regex_groups: Iterable[int],
) -> Iterator[tuple[dict[str, Any], list[str]]]:
    for hit in original:
        logging.debug("Trying %s" % hit["resource"]["subject"])
        matched = re.compile(subject_regex).match(hit["resource"]["subject"])
        if matched:
            yield (hit, [matched.group(group) for group in subject_regex_groups])

class DailyBulletinError(Exception):
    pass
