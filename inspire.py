#!/usr/bin/env python3
#
# Daily script to prepare the YK Pao School Daily Bulletin's JSON data files
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
# TODO: Check for potential filename injections
#

from __future__ import annotations
from configparser import ConfigParser
import json
import argparse
import logging
import datetime
import zoneinfo
import os
import sys
import requests
import shutil

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Download Daily Inspirations")
    # parser.add_argument("--changeme", default=None, help="changeme")
    parser.add_argument(
        "--config", default="config.ini", help="path to the configuration file"
    )
    args = parser.parse_args()

    config = ConfigParser()
    config.read(args.config)

    build_path = config["general"]["build_path"]
    os.chdir(build_path)

    api_base = config["web_service"]["api_base"].rstrip("/") + "/"
    token = config["web_service"]["token"].strip()

    response_json = requests.get(
        api_base + "rs", headers={"Authorization": "Bearer %s" % token}
    ).json()
    assert type(response_json) is list
    remote_submission_list = set(response_json)

    local_submission_list = set(
        [sn.lstrip("inspire-") for sn in os.listdir() if sn.startswith("inspire-")]
    )

    for sn in remote_submission_list - local_submission_list:
        with requests.get(
            api_base + "rs/" + sn,
            headers={
                "Authorization": "Bearer %s" % token,
                "Accept-Encoding": "identity",
            },
            stream=True,
        ) as r:
            with open("inspire-%s" % os.path.basename(sn), "w+b") as fd:
                shutil.copyfileobj(r.raw, fd)
                fd.flush()
                fd.seek(0)
                try:
                    sub = json.load(fd)
                except json.decoder.JSONDecodeError:
                    logger.error("inspire-%s is broken, skipping" % sn)
        if sub["file"] is not None:
            with requests.get(
                api_base + "rf/" + os.path.basename(sub["file"]),
                headers={
                    "Authorization": "Bearer %s" % token,
                    "Accept-Encoding": "identity",
                },
                stream=True,
            ) as r:
                with open("inspattach-%s" % os.path.basename(sub["file"]), "wb") as fd:
                    shutil.copyfileobj(r.raw, fd)
                    fd.flush()


if __name__ == "__main__":
    main()
