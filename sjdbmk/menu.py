#!/usr/bin/env python3
#
# Utility functions to parse the XLSX menu for the Daily Bulletin
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


from typing import Optional, Any
import email
import requests
import datetime
import logging
import os

import openpyxl

import common

logger = logging.getLogger(__name__)

def menu_item_fix(s: str) -> Optional[str]:
    if not s:
        return None
    if s == "Condiments Selection\n葱，香菜，榨菜丝，老干妈，生抽，醋":
        return None
    return s.strip().replace("Biscuit /", "Biscuit/").replace("Juice /", "Juice/").replace(" \n", "\n").replace("\n ", "\n")


def parse_meal_table(rows: list[Any], initrow: int, t: list[str]) -> dict[str, dict[str, list[str]]]:
    assert rows[initrow + 1][1].value is None

    igroups = []
    i = initrow + 2
    while True:
        c = rows[i][1]
        if not isinstance(c, openpyxl.cell.MergedCell):
            igroups.append(i)
        i += 1
        if len(igroups) >= len(t):
            break
    wgroups = dict(zip(igroups + [i], t + [None]))

    ret: dict[str, dict[str, list[str]]] = {}
    kmap = {}
    for k in range(2, 7):
        ret[rows[initrow + 1][k].value[0:3]] = {}
        kmap[k] = rows[initrow + 1][k].value[0:3]

    i = 0
    wgroupskeys = list(wgroups.keys())
    while i < len(wgroupskeys) - 1:
        wgroup = wgroups[wgroupskeys[i]]
        assert wgroup is not None
        for km in ret:
            ret[km][wgroup] = []
        for j in range(wgroupskeys[i], wgroupskeys[i + 1]):
            for k in range(2, 7):
                v = menu_item_fix(rows[j][k].value)
                if v:
                    ret[kmap[k]][wgroup].append(v)
        i += 1

    return ret


def parse_menus(datetime_target: datetime.datetime) -> dict[str, dict[str, dict[str, list[str]]]]:
    logger.info("Parsing menus")
    filename = "menu-%s.xlsx" % datetime_target.strftime("%Y%m%d")
    wb = openpyxl.load_workbook(filename=filename)
    ws = wb["菜单"]
    rows = list(ws.iter_rows())

    final = {}

    i = -1
    while i < len(rows) - 1:
        i += 1
        row = rows[i]
        if not isinstance(row[1].value, str):
            continue
        elif "BREAKFAST" in row[1].value:
            final["Breakfast"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Self Pick-up",  # instead of veg and soup
                    "Fruit/Drink",
                ],
            )
        elif "LUNCH" in row[1].value:
            final["Lunch"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Vegetarian",
                    "Daily Soup",
                    "Dessert/Fruit/Drink",
                ],
            )
        elif "DINNER" in row[1].value:
            final["Dinner"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Vegetarian",
                    "Daily Soup",
                    "Dessert/Fruit/Drink",
                ],
            )
        # elif "Students Snack" in row[1].value:
        #    parse_meal_table(rows, i)

    return final

def download_menu(
    token: str,
    datetime_target: datetime.datetime,
    weekly_menu_query_string: str,
    weekly_menu_sender: str,
    weekly_menu_subject_regex: str,
    weekly_menu_subject_regex_four_groups: tuple[int, int, int, int],
    menu_filename: str,
) -> None:
    search_results = common.search_mail(token, weekly_menu_query_string)

    for hit, matched_groups in common.filter_mail_results_by_subject_regex_groups(
        common.filter_mail_results_by_sender(search_results, weekly_menu_sender),
        weekly_menu_subject_regex,
        weekly_menu_subject_regex_four_groups,
    ):
        try:
            subject_1st_month = datetime.datetime.strptime(matched_groups[0], "%b").month  # issues here are probably locales
            subject_1st_day = int(matched_groups[1])
        except ValueError:
            raise ValueError(hit["resource"]["subject"], matched_groups[0])
        if subject_1st_month == datetime_target.month and subject_1st_day == datetime_target.day:
            break
    else:
        raise ValueError("No menu email found")

    with requests.get(
        "https://graph.microsoft.com/v1.0/me/messages/%s/$value" % hit["hitId"],
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept-Encoding": "identity",
        },
        stream=True,
        timeout=20,
    ) as r:
        msg = email.message_from_bytes(r.content)

    for part in msg.walk():
        if part.get_content_type() in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            payload = part.get_payload(decode=True)
            pb = bytes(payload)

            with open(menu_filename, "wb") as w:
                w.write(pb)
            break
    else:
        raise ValueError("No proper attachment found in email")

def download_or_report_menu(token: str, datetime_target: datetime.datetime, weekly_menu_query_string: str, weekly_menu_sender: str, weekly_menu_subject_regex: str, weekly_menu_subject_regex_four_groups: tuple[int, int, int, int]) -> None:
    menu_filename = "menu-%s.xlsx" % datetime_target.strftime("%Y%m%d")
    if not (os.path.isfile(menu_filename)):
        logger.info("Menu not found, downloading")
        download_menu(
            token,
            datetime_target,
            weekly_menu_query_string,
            weekly_menu_sender,
            weekly_menu_subject_regex,
            weekly_menu_subject_regex_four_groups,
            menu_filename,
        )
        assert os.path.isfile(menu_filename)
    else:
        logger.info("Menu already exists")
