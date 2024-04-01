#!/usr/bin/env python3

from __future__ import annotations
from typing import Any, Optional
from configparser import ConfigParser

import argparse
import logging
import msal  # type: ignore
import requests
import datetime
import pytz
import os
import json
import base64
import pptx  # type: ignore
import pptx.exc  # type: ignore

logger = logging.getLogger(__name__)


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


def combine_parsed_meal_tables(
    en: list[list[list[str]]], cn: list[list[list[str]]]
) -> list[list[list[list[str]]]]:
    if not equal_shapes(cn, en):
        raise ValueError("Augmented menus not in the same shape")

    c = zero_list(en)

    for j in range(len(en)):
        for i in range(len(en[j])):
            for k in range(len(en[j][i])):
                c[j][i][k] = [en[j][i][k], cn[j][i][k]]
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
) -> list[list[list[list[list[str]]]]]:
    try:
        enprs = pptx.Presentation(filename_en)
        cnprs = pptx.Presentation(filename_cn)
    except pptx.exc.PackageNotFoundError:
        raise ValueError("Presentation path doesn't exist or is broken") from None

    return [
        combine_parsed_meal_tables(
            parse_meal_tables(
                slide_to_srep(
                    enprs.slides[int(config["weekly_menu"]["%s_page_number" % meal])]
                )
            ),
            parse_meal_tables(
                slide_to_srep(
                    cnprs.slides[int(config["weekly_menu"]["%s_page_number" % meal])]
                )
            ),
        )
        for meal in ["breakfast", "lunch", "dinner"]
    ]


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
    token: str, url: str, local_filename: str, chunk_size: int = 131072
) -> None:
    download_direct_url = requests.get(
        "https://graph.microsoft.com/v1.0/shares/%s/driveItem"
        % encode_sharing_url(url),
        headers={"Authorization": "Bearer " + token},
    ).json()["@microsoft.graph.downloadUrl"]
    r = requests.get(download_direct_url, stream=True)
    with open(local_filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)


def extract_community_time_from_presentation(
    date: str, config: ConfigParser
) -> list[list[str]]:
    try:
        prs = pptx.Presentation(
            os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
    except pptx.exc.PackageNotFoundError:
        raise ValueError("The Week Ahead is missing, empty, or broken") from None

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


def extract_aod_from_presentation(date: str, config: ConfigParser) -> list[str]:
    prs = pptx.Presentation(
        os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
    )
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


def main(stddate: str, config: ConfigParser) -> None:
    date = stddate.replace("-", "")
    logger.info("Acquiring token")
    token = acquire_token(config)

    logger.info("Downloading The Week Ahead")
    download_share_url(
        token,
        config["the_week_ahead"]["file_url"],
        os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date),
    )

    logger.info("Extracting Community Time")
    try:
        community_time = fix_community_time(
            extract_community_time_from_presentation(date, config)
        )
    except ValueError:
        logger.warning(
            "Irregular Community Time; opening The Week Ahead for manual editing. Press ENTER after saving."
        )  # TODO: interactive elements in non-interactive functions
        os.system(
            "open "
            + os.path.join(config["general"]["build_path"], "twa-%s.pptx" % date)
        )
        input("PRESS ENTER TO CONTINUE >>>")
        community_time = fix_community_time(
            extract_community_time_from_presentation(date, config)
        )
    logger.info("Extracting AODs")
    aods = extract_aod_from_presentation(date, config)
    logger.info("Extracting menu")
    menu = extract_all_menus(
        os.path.join(config["general"]["build_path"], "menu-%s-en.pptx" % date),
        os.path.join(config["general"]["build_path"], "menu-%s-cn.pptx" % date),
        config
    )

    logger.info("Packing data")
    data = {
        "start_date": stddate,
        "community_time": community_time,
        "aods": aods,
        "menu": menu,
    }

    with open(os.path.join("build", "week-" + date + ".json"), "w") as fd:
        json.dump(data, fd, ensure_ascii=False)
    logger.info("Data dumped to " + os.path.join("build", "week-" + date + ".json"))


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
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
            now = datetime.datetime.now(pytz.timezone(config["general"]["timezone"]))
            date = (now + datetime.timedelta(days=(-now.weekday()) % 7)).strftime(
                "%Y-%m-%d"
            )
        logging.info("Generating for %s" % date)
        main(date, config)
    except KeyboardInterrupt:
        logging.critical("KeyboardInterrupt")
