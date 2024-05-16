#!/usr/bin/env python3
#
# Weekly script to prepare the YK Pao School Daily Bulletin
# Copyright (C) 2024  Runxi Yu <https://runxiyu.org>
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
from typing import Any, Optional, Iterable, Iterator
from configparser import ConfigParser
from pprint import pprint
import argparse
import logging
import msal  # type: ignore
import requests
import datetime
import zoneinfo
import os
import json
import base64
import email
import re
import pptx  # type: ignore
import pptx.exc  # type: ignore

logger = logging.getLogger(__name__)

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


def zero_list(l: list[Any]) -> list[Any]:
    return [(zero_list(i) if (isinstance(i, list)) else "") for i in l]


def equal_shapes(a: list[Any], b: list[Any]) -> bool:
    return zero_list(a) == zero_list(b)


def parse_meal_tables(
    tbl: list[list[tuple[str, int, int, str]]]
) -> list[list[list[str]]]:
    windows = []
    for j in range(1, len(tbl)):
        cell = tbl[j][0]
        if cell[0] in ["o", "n"]:
            windows.append((j, j - 1 + cell[1]))

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    daysmenus: list[list[list[str]]] = [[], [], [], [], []]

    assert len(tbl[0]) == 6

    for i in range(1, len(tbl[0])):
        for s, f in windows:
            thiswindow = []
            for j in range(s, f + 1):
                if (
                    tbl[j][i][-1].strip()
                    and tbl[j][i][-1].strip().lower() != "condiments selection"
                ):
                    thiswindow.append(tbl[j][i][-1])
            daysmenus[i - 1].append(thiswindow)
    return daysmenus


class MealTableShapeError(ValueError):
    pass


def combine_parsed_meal_tables(
    en: list[list[list[str]]], cn: list[list[list[str]]]
) -> list[list[list[list[str]]]]:
    if not equal_shapes(cn, en):
        raise MealTableShapeError(
            "Augmented menus not in the same shape",
            zero_list(en),
            zero_list(cn),
            en,
            cn,
        )

    c = zero_list(en)

    for j in range(len(en)):
        for i in range(len(en[j])):
            for k in range(len(en[j][i])):
                c[j][i][k] = {"en": en[j][i][k], "zh": cn[j][i][k]}
    return c


def slide_to_srep(slide: pptx.slide) -> list[list[tuple[str, int, int, str]]]:
    for shape in slide.shapes:
        if shape.has_table:
            break
    else:
        raise ValueError("Slide doesn't contain any tables?")
    tbl = shape.table
    row_count: int = len(tbl.rows)
    col_count: int = len(tbl.columns)
    tbll = []
    for r in range(row_count):
        row: list[tuple[str, int, int, str]] = [("", 0, 0, "")] * col_count
        old_cell_text = ""
        for c in range(col_count):
            cell_text = ""
            cell = tbl.cell(r, c)
            assert type(cell.span_height) is int
            assert type(cell.span_width) is int
            paragraphs = cell.text_frame.paragraphs
            for paragraph in paragraphs:
                for run in paragraph.runs:
                    cell_text += run.text
            row[c] = (
                "o" if cell.is_merge_origin else ("s" if cell.is_spanned else "n"),
                cell.span_height,
                cell.span_width,
                cell_text.strip(),
            )
            old_cell_text = cell_text
        tbll.append(row)
    return tbll


def extract_all_menus(
    filename_en: str, filename_cn: str, config: ConfigParser
) -> dict[str, list[list[list[list[str]]]]]:
    try:
        enprs = pptx.Presentation(filename_en)
        cnprs = pptx.Presentation(filename_cn)
    except pptx.exc.PackageNotFoundError:
        raise ValueError("Presentation path doesn't exist or is broken") from None

    mtable = {}
    for meal in ["breakfast", "lunch", "dinner"]:
        try:
            mtable[meal] = (
                combine_parsed_meal_tables(
                    parse_meal_tables(
                        slide_to_srep(
                            enprs.slides[
                                int(config["weekly_menu"]["%s_page_number" % meal])
                            ]
                        )
                    ),
                    parse_meal_tables(
                        slide_to_srep(
                            cnprs.slides[
                                int(config["weekly_menu"]["%s_page_number" % meal])
                            ]
                        )
                    ),
                )
            )
        except MealTableShapeError:
            raise ValueError("Inconsistent shape for %s" % meal)
    assert len(mtable) == 3
    return mtable


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


def encode_sharing_url(url: str) -> str:
    return "u!" + base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip(
        "="
    )


def download_share_url(
    token: str, url: str, local_filename: str, chunk_size: int = 1310720
) -> None:
    logger.debug("Retreiving direct download URL")
    download_direct_url = requests.get(
        "https://graph.microsoft.com/v1.0/shares/%s/driveItem"
        % encode_sharing_url(url),
        headers={"Authorization": "Bearer " + token},
    ).json()["@microsoft.graph.downloadUrl"]
    logger.debug("Making direct download request")
    r = requests.get(download_direct_url, stream=True)
    downloaded_size = 0
    target_size = int(r.headers.get("content-length", 0))
    logger.debug("Total size %d" % target_size)
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
            downloaded_size += chunk_size
            logger.debug("Downloaded %d of %d" % (downloaded_size, target_size))
    logger.debug("Download finished")


def extract_community_time_from_presentation(
    date: str, prs: pptx.Presentation, config: ConfigParser
) -> list[list[str]]:

    slide = prs.slides[int(config["the_week_ahead"]["community_time_page_number"])]
    for shape in slide.shapes:
        if not shape.has_table:
            continue
    tbl = shape.table
    row_count = len(tbl.rows)
    col_count = len(tbl.columns)
    if row_count != 5 or col_count != 5:
        raise ValueError(
            "Community time parsing: The Week Ahead community time table is not 5x5"
        )
    tbll = []
    for r in range(row_count):
        row = [""] * col_count
        for c in range(col_count):
            cell_text = ""
            cell = tbl.cell(r, c)
            paragraphs = cell.text_frame.paragraphs
            for paragraph in paragraphs:
                for run in paragraph.runs:
                    cell_text += run.text
            if not cell_text.strip():
                cell_text = old_cell_text  # type: ignore
                # TODO: Use cell.is_merge_origin, cell.is_spanned,
                # cell.span_height, cell.span_width instead
            row[c] = cell_text
            old_cell_text = cell_text
        tbll.append(row)
    return tbll


def extract_aod_from_presentation(
    date: str, prs: pptx.Presentation, config: ConfigParser
) -> list[str]:
    slide = prs.slides[int(config["the_week_ahead"]["aod_page_number"])]

    aods = ["", "", "", ""]
    for shape in slide.shapes:
        if hasattr(shape, "text") and "Monday: " in shape.text:
            slist = shape.text.split("\n")
            for s in slist:
                try:
                    day, aod = s.split(": ", 1)
                except ValueError:
                    pass
                day = day.lower()
                if day == "monday":
                    aods[0] = aod
                elif day == "tuesday":
                    aods[1] = aod
                elif day == "wednesday":
                    aods[2] = aod
                elif day == "thursday":
                    aods[3] = aod
            if not all(aods):
                raise ValueError(
                    "AOD parsing: The Week Ahead doesn't include all AOD days, or the formatting is borked"
                )
            return aods
            break
    else:
        raise ValueError(
            "AOD parsing: The Week Ahead's doesn't even include \"Monday\""
        )


def get_message(
    token: str,
    hitid: str,
) -> bytes:
    print("Getting message")
    return requests.get(
        "https://graph.microsoft.com/v1.0/me/messages/%s/$value" % hitid,
        headers={"Authorization": "Bearer " + token},
    ).content


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


def fix_community_time(tbll: list[list[str]]) -> list[list[str]]:
    res = []
    for i in range(1, 5):
        day = tbll[i]
        dayl = []
        for j in range(1, len(day)):
            text = day[j]
            if "whole school assembly" in text.lower():
                dayl.append("Whole School Assembly")
            elif (
                "tutor group check-in" in text.lower()
                or "follow up day" in text.lower()
            ):
                dayl.append("Tutor Time")
            else:
                dayl.append(text.strip())
        res.append(dayl)
    return res


def download_menu(token: str, config: ConfigParser, date: str) -> tuple[str, str, str]:
    dtuple = date.split("-")
    assert len(dtuple) == 3

    target_month = int(dtuple[1])
    target_day = int(dtuple[2])
    target_year_str = dtuple[0]

    fpptxen = "menu-%s%02d%02d-en.pptx" % (
        target_year_str,
        target_month,
        target_day,
    )
    fpptxzh = "menu-%s%02d%02d-zh.pptx" % (
        target_year_str,
        target_month,
        target_day,
    )
    fpdf = "menu-%s%02d%02d.pdf" % (
        target_year_str,
        target_month,
        target_day,
    )

    if all(
        [
            os.path.isfile(os.path.join(config["general"]["build_path"], x))
            for x in [fpptxen, fpptxzh, fpdf]
        ]
    ):
        return fpptxen, fpptxzh, fpdf

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
            "menu-%s%02d%02d.eml" % (target_year_str, target_month, target_day),
        ),
        "wb",
    ) as wf:
        wf.write(msg_bytes)

    msg = email.message_from_bytes(msg_bytes)

    for part in msg.walk():
        if part.get_content_type() in [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/pdf",
        ]:
            pl = part.get_payload(decode=True)
            pfn = part.get_filename()
            if not pfn:
                raise ValueError("PPTX/PDF doesn't have a filename")
            ft = email.header.decode_header(pfn)
            assert len(ft) == 1
            assert len(ft[0]) == 2
            if type(ft[0][0]) is bytes:
                if type(ft[0][1]) is not str:
                    raise ValueError("Header component for the filename isn't a string")
                filename = ft[0][0].decode(ft[0][1])
            elif type(ft[0][0]) is str:
                filename = ft[0][0]
            else:
                raise TypeError(ft, "not bytes or str???")

            if (
                part.get_content_type()
                == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ):
                if "EN" in filename:
                    lang = "en"
                    formatted_filename = fpptxen
                elif "CH" or "CN" in filename:
                    lang = "zh"
                    formatted_filename = fpptxzh
                else:
                    raise ValueError(
                        "%s does not contain a language specification string", filename
                    )
            elif part.get_content_type() == "application/pdf":
                formatted_filename = fpdf

            with open(
                os.path.join(config["general"]["build_path"], formatted_filename), "wb"
            ) as w:
                w.write(pl)

    return fpptxen, fpptxzh, fpdf


def main(stddate: str, config: ConfigParser) -> None:
    date = stddate.replace("-", "")
    logger.info("Acquiring token")
    token = acquire_token(config)
    logger.info("Extracting Community Time")
    try:
        prs = pptx.Presentation(
            os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
    except pptx.exc.PackageNotFoundError:
        logger.info("Downloading The Week Ahead")
        download_share_url(
            token,
            config["the_week_ahead"]["file_url"],
            os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date),
        )
        prs = pptx.Presentation(
            os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
    try:
        community_time = fix_community_time(
            extract_community_time_from_presentation(date, prs, config)
        )
    except ValueError:
        logger.warning(
            "Irregular Community Time; opening The Week Ahead for manual editing. Press ENTER after saving."
        )  # TODO: interactive elements in non-interactive functions
        del prs
        os.system(
            "open "
            + os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
        # input("PRESS ENTER TO CONTINUE >>>")
        prs = pptx.Presentation(
            os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
        community_time = fix_community_time(
            extract_community_time_from_presentation(date, prs, config)
        )
    logger.info("Extracting AODs")
    aods = extract_aod_from_presentation(date, prs, config)
    logger.info("Downloading menu")

    en_menu_filename, zh_menu_filename, pdf_menu_filename = download_menu(
        token, config, stddate
    )

    # TODO: pdf_menu_filename not parsed!

    logger.info("Extracting menu")
    menu = extract_all_menus(
        os.path.join(config["general"]["build_path"], en_menu_filename),
        os.path.join(config["general"]["build_path"], zh_menu_filename),
        config,
    )

    logger.info("Packing data")
    data = {
        "start_date": stddate,
        "community_time": community_time,
        "aods": aods,
        "menu": menu,
    }

    with open(
        os.path.join(config["general"]["build_path"], "week-" + date + ".json"), "w"
    ) as fd:
        json.dump(data, fd, ensure_ascii=False, indent="\t")
    logger.info(
        "Data dumped to "
        + os.path.join(config["general"]["build_path"], "week-" + date + ".json")
    )


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG)
        parser = argparse.ArgumentParser(
            description="Weekly script for the Daily Bulletin"
        )
        parser.add_argument(
            "--date",
            default=None,
            help="the start of week to generate for, in local time, in YYYY-MM-DD",
            # TODO: Verify validity of date
            # TODO: Verify consistency of date elsewhere
        )
        parser.add_argument(
            "--config", default="config.ini", help="path to the configuration file"
        )
        args = parser.parse_args()
        config = ConfigParser()
        config.read(args.config)
        if args.date:
            date = args.date
        else:
            now = datetime.datetime.now(
                zoneinfo.ZoneInfo(config["general"]["timezone"])
            )
            date = (now + datetime.timedelta(days=(-now.weekday()) % 7)).strftime(
                "%Y-%m-%d"
            )
        logging.info("Generating for %s" % date)
        main(date, config)
    except KeyboardInterrupt:
        logging.critical("KeyboardInterrupt")
