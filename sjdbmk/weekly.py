#!/usr/bin/env python3
#
# Weekly script to prepare the YK Pao School Daily Bulletin's week JSON data
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
# Some rules:
# - Pass localized aware datetime objects around.
#   Minimize the use of date strings and numbers.
#   NEVER used naive datetime objects.
#   Frequently check if the tzinfo is correct or cast the zone.
# - Delete variables that aren't supposed to be used anymore.
# - Functions should be short.
# - Do not pass ConfigParser objects around.
# - Use meaningful variable names.
# - Always write type hints.
# - Use the logger! Try not to print.
#
# TODO: Check The Week Ahead's dates

from __future__ import annotations
from typing import Any, Iterable, Iterator
from configparser import ConfigParser
import argparse
import logging
import subprocess
import datetime
import zoneinfo
import os
import shutil
import json
import base64
import email
import re

import requests

from . import common, twa, menu

logger = logging.getLogger(__name__)


def generate(
    datetime_target: datetime.datetime,  # expected to be local time
    the_week_ahead_url: str,
    the_week_ahead_community_time_page_number: int,
    the_week_ahead_aod_page_number: int,
    weekly_menu_query_string: str,
    weekly_menu_sender: str,
    weekly_menu_subject_regex: str,
    weekly_menu_subject_regex_four_groups: tuple[int, int, int, int],
    graph_client_id: str,
    graph_authority: str,
    graph_username: str,
    graph_password: str,
    graph_scopes: list[str],
    calendar_address: str,
) -> str:
    if not datetime_target.tzinfo:
        raise TypeError("Naive datetimes are unsupported")
    output_filename = "week-%s.json" % datetime_target.strftime("%Y%m%d")
    logger.info("Output filename: %s" % output_filename)

    token = common.acquire_token(graph_client_id, graph_authority, graph_username, graph_password, graph_scopes)
    twa.download_or_report_the_week_ahead(token, datetime_target, the_week_ahead_url)
    menu.download_or_report_menu(token, datetime_target, weekly_menu_query_string, weekly_menu_sender, weekly_menu_subject_regex, weekly_menu_subject_regex_four_groups)
    community_time, aods = twa.parse_the_week_ahead(datetime_target, the_week_ahead_community_time_page_number, the_week_ahead_aod_page_number)
    menu_data = menu.parse_menus(datetime_target)

    logger.info("Packing final data")
    final_data = {
        "start_date": datetime_target.strftime("%Y-%m-%d"),
        "community_time": community_time,
        "aods": aods,
        "menu": menu_data,
    }

    logger.info("Dumping data to: %s" % output_filename)
    with open(output_filename, "w", encoding="utf-8") as fd:
        json.dump(final_data, fd, ensure_ascii=False, indent="\t")
    return output_filename


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Weekly script for the Daily Bulletin")
    parser.add_argument(
        "--date",
        default=None,
        help="the start of the week to generate for, in local time, YYYY-MM-DD; defaults to next Monday",
    )
    parser.add_argument("--config", default="config.ini", help="path to the configuration file")
    args = parser.parse_args()

    if args.date:
        datetime_target_naive = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    else:
        datetime_target_naive = None

    config = ConfigParser()
    config.read(args.config)

    tzinfo = zoneinfo.ZoneInfo(config["general"]["timezone"])
    if datetime_target_naive:
        datetime_target_aware = datetime_target_naive.replace(tzinfo=tzinfo)
    else:
        datetime_current_aware = datetime.datetime.now(tz=tzinfo)
        datetime_target_aware = datetime_current_aware + datetime.timedelta(days=((-datetime_current_aware.weekday()) % 7))
    logger.info("Generating for %s" % datetime_target_aware.strftime("%Y-%m-%d %Z"))

    build_path = config["general"]["build_path"]
    # TODO: check if the build path exists and create it if it doesn't
    os.chdir(build_path)

    the_week_ahead_url = config["the_week_ahead"]["file_url"]
    the_week_ahead_community_time_page_number = int(config["the_week_ahead"]["community_time_page_number"])
    the_week_ahead_aod_page_number = int(config["the_week_ahead"]["aod_page_number"])

    weekly_menu_query_string = config["weekly_menu"]["query_string"]
    weekly_menu_sender = config["weekly_menu"]["sender"]
    weekly_menu_subject_regex = config["weekly_menu"]["subject_regex"]
    weekly_menu_subject_regex_four_groups_raw = config["weekly_menu"]["subject_regex_four_groups"].split(" ")
    weekly_menu_subject_regex_four_groups = tuple([int(z) for z in weekly_menu_subject_regex_four_groups_raw])
    assert len(weekly_menu_subject_regex_four_groups) == 4
    # weekly_menu_dessert_page_number = config["weekly_menu"]["dessert_page_number"]

    graph_client_id = config["credentials"]["client_id"]
    graph_authority = config["credentials"]["authority"]
    graph_username = config["credentials"]["username"]
    graph_password = config["credentials"]["password"]
    graph_scopes = config["credentials"]["scope"].split(" ")

    calendar_address = config["calendar"]["address"]

    # TODO: Validate the configuration

    generate(
        datetime_target=datetime_target_aware,
        the_week_ahead_url=the_week_ahead_url,
        the_week_ahead_community_time_page_number=the_week_ahead_community_time_page_number,
        the_week_ahead_aod_page_number=the_week_ahead_aod_page_number,
        weekly_menu_query_string=weekly_menu_query_string,
        weekly_menu_sender=weekly_menu_sender,
        weekly_menu_subject_regex=weekly_menu_subject_regex,
        weekly_menu_subject_regex_four_groups=weekly_menu_subject_regex_four_groups,
        graph_client_id=graph_client_id,
        graph_authority=graph_authority,
        graph_username=graph_username,
        graph_password=graph_password,
        graph_scopes=graph_scopes,
        calendar_address=calendar_address,
    )


if __name__ == "__main__":
    main()
