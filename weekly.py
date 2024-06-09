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
from typing import Any, Optional, Iterable, Iterator
from configparser import ConfigParser
from pprint import pprint
import argparse
import logging
import requests
import subprocess
import datetime
import zoneinfo
import os
import shutil
import json
import base64
import email
import re
import io

import msal  # type: ignore
import pptx  # type: ignore
import pptx.exc  # type: ignore
import pypdf

logger = logging.getLogger(__name__)


class MealTableShapeError(ValueError):
    pass


def zero_list(l: list[Any]) -> list[Any]:
    return [(zero_list(i) if (isinstance(i, list)) else "") for i in l]


def equal_shapes(a: list[Any], b: list[Any]) -> bool:
    return zero_list(a) == zero_list(b)


def generate(
    datetime_target: datetime.datetime,  # expected to be local time
    the_week_ahead_url: str,
    the_week_ahead_community_time_page_number: int,
    the_week_ahead_aod_page_number: int,
    weekly_menu_breakfast_page_number: int,
    weekly_menu_lunch_page_number: int,
    weekly_menu_dinner_page_number: int,
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
    soffice: str,
) -> str:
    if not datetime_target.tzinfo:
        raise TypeError("Naive datetimes are unsupported")
    output_filename = "week-%s.json" % datetime_target.strftime("%Y%m%d")
    logger.info("Output filename: %s" % output_filename)

    token: str = acquire_token(
        graph_client_id, graph_authority, graph_username, graph_password, graph_scopes
    )

    calendar_response = requests.get(
        "https://graph.microsoft.com/v1.0/users/%s/calendar/calendarView"
        % calendar_address,
        headers={"Authorization": "Bearer " + token},
        params={
            "startDateTime": datetime_target.replace(microsecond=0).isoformat(),
            "endDateTime": (datetime_target + datetime.timedelta(days=7))
            .replace(microsecond=0)
            .isoformat(),
        },
    )
    if calendar_response.status_code != 200:
        raise ValueError(
            "Calendar response status code is not 200", calendar_response.content
        )
    calendar_object = calendar_response.json()
    pprint(calendar_object)
    # exit(1)

    the_week_ahead_filename = "the_week_ahead-%s.pptx" % datetime_target.strftime(
        "%Y%m%d"
    )
    if not os.path.isfile(the_week_ahead_filename):
        logger.info(
            "The Week Ahead doesn't seem to exist at %s, downloading"
            % the_week_ahead_filename
        )
        download_share_url(token, the_week_ahead_url, the_week_ahead_filename)
        logger.info("Downloaded The Week Ahead to %s" % the_week_ahead_filename)
        assert os.path.isfile(the_week_ahead_filename)
    else:
        logger.info("The Week Ahead already exists at %s" % the_week_ahead_filename)

    menu_en_filename = "menu-%s-en.pptx" % datetime_target.strftime("%Y%m%d")
    menu_zh_filename = "menu-%s-zh.pptx" % datetime_target.strftime("%Y%m%d")
    menu_pdf_filename = "menu-%s.pdf" % datetime_target.strftime(
        "%Y%m%d"
    )  # TODO: Snacks
    if not (
        os.path.isfile(menu_en_filename)
        and os.path.isfile(menu_zh_filename)
        and os.path.isfile(menu_pdf_filename)
    ):
        logger.info("Not all menus exist, downloading")
        download_menu(
            token,
            datetime_target,
            weekly_menu_query_string,
            weekly_menu_sender,
            weekly_menu_subject_regex,
            weekly_menu_subject_regex_four_groups,
            menu_en_filename,
            menu_zh_filename,
            menu_pdf_filename,
        )
        assert (
            os.path.isfile(menu_en_filename)
            and os.path.isfile(menu_zh_filename)
            and os.path.isfile(menu_pdf_filename)
        )
    else:
        logger.info("All menus already exist")

    logger.info("Beginning to parse The Week Ahead")
    the_week_ahead_presentation = pptx.Presentation(the_week_ahead_filename)
    try:
        community_time = extract_community_time(
            the_week_ahead_presentation,
            the_week_ahead_community_time_page_number,
        )
    except ValueError:
        logger.error(
            "Invalid community time! Opening The Week Ahead for manual intervention."
        )
        del the_week_ahead_presentation
        subprocess.run([soffice, the_week_ahead_filename])
        the_week_ahead_presentation = pptx.Presentation(the_week_ahead_filename)
        community_time = extract_community_time(
            the_week_ahead_presentation,
            the_week_ahead_community_time_page_number,
        )
    del the_week_ahead_filename

    aods = extract_aods(the_week_ahead_presentation, the_week_ahead_aod_page_number)
    # We're assuming the the AODs don't need manual intervention. I think that's fair.
    del the_week_ahead_presentation
    logger.info("Finished parsing The Week Ahead")

    logger.info("Beginning to extract menus")
    try:
        menu = extract_pptx_menus(
            menu_en_filename,
            menu_zh_filename,
            weekly_menu_breakfast_page_number,
            weekly_menu_lunch_page_number,
            weekly_menu_dinner_page_number,
        )
        snacks = fix_snacks(extract_snacks(menu_pdf_filename))
    except MealTableShapeError as e:
        logger.error(
            "Invalid menus! Opening both PPTX menus for manual intervention.", e.args[0]
        )
        subprocess.run([soffice, menu_en_filename, menu_zh_filename])
        menu = extract_pptx_menus(
            menu_en_filename,
            menu_zh_filename,
            weekly_menu_breakfast_page_number,
            weekly_menu_lunch_page_number,
            weekly_menu_dinner_page_number,
        )
        snacks = fix_snacks(extract_snacks(menu_pdf_filename))
    del menu_en_filename
    del menu_zh_filename
    del menu_pdf_filename
    logger.info("Finished extracting menus")

    final_data = {
        "start_date": datetime_target.strftime("%Y-%m-%d"),
        "community_time": community_time,
        "aods": aods,
        "menu": menu,
        "snacks": snacks,
    }

    with open(output_filename, "w") as fd:
        json.dump(final_data, fd, ensure_ascii=False, indent="\t")
    logger.info("Dumped to: %s" % output_filename)
    return output_filename


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Weekly script for the Daily Bulletin")
    parser.add_argument(
        "--date",
        default=None,
        help="the start of the week to generate for, in local time, YYYY-MM-DD; defaults to next Monday",
    )
    parser.add_argument(
        "--config", default="config.ini", help="path to the configuration file"
    )
    args = parser.parse_args()

    if args.date:
        datetime_target_naive = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    else:
        datetime_target_naive = None
    del args.date

    config = ConfigParser()
    config.read(args.config)

    tzinfo = zoneinfo.ZoneInfo(config["general"]["timezone"])
    if datetime_target_naive:
        datetime_target_aware = datetime_target_naive.replace(tzinfo=tzinfo)
    else:
        datetime_current_aware = datetime.datetime.now(tz=tzinfo)
        datetime_target_aware = datetime_current_aware + datetime.timedelta(
            days=((-datetime_current_aware.weekday()) % 7)
        )
        del datetime_current_aware
    del datetime_target_naive
    logger.info("Generating for %s" % datetime_target_aware.strftime("%Y-%m-%d %Z"))

    build_path = config["general"]["build_path"]
    # TODO: check if the build path exists and create it if it doesn't
    os.chdir(build_path)

    the_week_ahead_url = config["the_week_ahead"]["file_url"]
    the_week_ahead_community_time_page_number = int(
        config["the_week_ahead"]["community_time_page_number"]
    )
    the_week_ahead_aod_page_number = int(config["the_week_ahead"]["aod_page_number"])

    weekly_menu_breakfast_page_number = int(
        config["weekly_menu"]["breakfast_page_number"]
    )
    weekly_menu_lunch_page_number = int(config["weekly_menu"]["lunch_page_number"])
    weekly_menu_dinner_page_number = int(config["weekly_menu"]["dinner_page_number"])
    weekly_menu_query_string = config["weekly_menu"]["query_string"]
    weekly_menu_sender = config["weekly_menu"]["sender"]
    weekly_menu_subject_regex = config["weekly_menu"]["subject_regex"]
    weekly_menu_subject_regex_four_groups_raw = config["weekly_menu"][
        "subject_regex_four_groups"
    ].split(" ")
    weekly_menu_subject_regex_four_groups = tuple(
        [int(z) for z in weekly_menu_subject_regex_four_groups_raw]
    )
    assert len(weekly_menu_subject_regex_four_groups) == 4
    del weekly_menu_subject_regex_four_groups_raw
    # weekly_menu_dessert_page_number = config["weekly_menu"]["dessert_page_number"]

    graph_client_id = config["credentials"]["client_id"]
    graph_authority = config["credentials"]["authority"]
    graph_username = config["credentials"]["username"]
    graph_password = config["credentials"]["password"]
    graph_scopes = config["credentials"]["scope"].split(" ")

    calendar_address = config["calendar"]["address"]

    soffice = config["general"]["soffice"]

    # TODO: make a function that checks the configuration

    generate(
        datetime_target=datetime_target_aware,
        the_week_ahead_url=the_week_ahead_url,
        the_week_ahead_community_time_page_number=the_week_ahead_community_time_page_number,
        the_week_ahead_aod_page_number=the_week_ahead_aod_page_number,
        weekly_menu_breakfast_page_number=weekly_menu_breakfast_page_number,
        weekly_menu_lunch_page_number=weekly_menu_lunch_page_number,
        weekly_menu_dinner_page_number=weekly_menu_dinner_page_number,
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
        soffice=soffice,
    )
    # NOTE: generate() can get the timezone from datetime_target_aware
    # It returns the generated filename.


def encode_sharing_url(url: str) -> str:
    return "u!" + base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip(
        "="
    )


def download_share_url(
    token: str, url: str, local_filename: str, chunk_size: int = 65536
) -> None:

    download_direct_url = requests.get(
        "https://graph.microsoft.com/v1.0/shares/%s/driveItem"
        % encode_sharing_url(url),
        headers={"Authorization": "Bearer " + token},
    ).json()["@microsoft.graph.downloadUrl"]

    with requests.get(
        download_direct_url,
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept-Encoding": "identity",
        },
        stream=True,
    ) as r:
        with open(local_filename, "wb") as fd:
            shutil.copyfileobj(r.raw, fd)
            fd.flush()


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
    result = app.acquire_token_by_username_password(
        graph_username, graph_password, scopes=graph_scopes
    )

    if "access_token" in result:
        assert type(result["access_token"]) is str
        return result["access_token"]
    else:
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
    ).json()["value"][0]["hitsContainers"][0]["hits"]
    assert type(hits) is list
    assert type(hits[0]) is dict
    return hits


def slide_to_srep(slide: pptx.slide) -> list[list[tuple[str, int, int, str]]]:
    # NOTE: Only processes FIRST table.
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


def parse_meal_tables(
    tbl: list[list[tuple[str, int, int, str]]]
) -> list[list[list[str]]]:
    windows = []
    for j in range(1, len(tbl)):
        cell = tbl[j][0]
        if cell[0] in ["o", "n"]:
            windows.append((j, j - 1 + cell[1]))

    daysmenus: list[list[list[str]]] = [[], [], [], [], []]

    assert len(tbl[0]) == 6

    for i in range(1, len(tbl[0])):
        for s, f in windows:
            thiswindow = []
            for j in range(s, f + 1):
                if (
                    tbl[j][i][-1].strip()
                    and tbl[j][i][-1].strip().lower()
                    != "condiments selection"  # seriously
                ):
                    thiswindow.append(
                        tbl[j][i][-1]
                        .replace("， ", ", ")
                        .replace("，", ", ")
                        .replace("Juice /", "Juice/")
                    )
            daysmenus[i - 1].append(thiswindow)
    return daysmenus


def extract_pptx_menus(
    menu_en_filename: str,
    menu_zh_filename: str,
    breakfast_page_number: int,
    lunch_page_number: int,
    dinner_page_number: int,
) -> dict[str, list[list[list[list[str]]]]]:
    try:
        enprs = pptx.Presentation(menu_en_filename)
        zhprs = pptx.Presentation(menu_zh_filename)
    except pptx.exc.PackageNotFoundError:
        raise ValueError("Presentation path doesn't exist or is broken") from None

    mtable = {}
    for meal, pageno in {
        "breakfast": breakfast_page_number,
        "lunch": lunch_page_number,
        "dinner": dinner_page_number,
    }.items():
        try:
            mtable[meal] = combine_parsed_meal_tables(
                parse_meal_tables(slide_to_srep(enprs.slides[pageno])),
                parse_meal_tables(slide_to_srep(zhprs.slides[pageno])),
            )
        except MealTableShapeError:
            raise MealTableShapeError(meal) from None
    assert len(mtable) == 3
    return mtable


def extract_aods(prs: pptx.Presentation, aod_page_number: int) -> list[str]:
    slide = prs.slides[aod_page_number]
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
    # TODO: this is one of those places where Monday is *expected* to be the first day.
    # TODO: revamp this. this is ugly!


def extract_community_time(
    prs: pptx.Presentation, community_time_page_number: int
) -> list[list[str]]:

    slide = prs.slides[community_time_page_number]
    for shape in slide.shapes:
        if not shape.has_table:
            continue
    tbl = shape.table
    row_count = len(tbl.rows)
    col_count = len(tbl.columns)
    if col_count not in [4, 5]:
        raise ValueError(
            "Community time parsing: The Week Ahead community time table does not have 4 or 5 columns"
        )
    if col_count == 4:
        logger.warning(
            "Community time warning: only four columns found, assuming that Y12 has graduated"
        )

    res = [["" for c in range(col_count)] for r in range(row_count)]

    for r in range(row_count):
        for c in range(col_count):
            cell = tbl.cell(r, c)
            if not cell.is_spanned:
                t = ""
                for p in cell.text_frame.paragraphs:
                    for pr in p.runs:
                        t += pr.text
                t = t.strip()
                if "whole school assembly" in t.lower():
                    t = "Whole School Assembly"
                elif (
                    "tutor group check-in" in t.lower()
                    or "follow up day" in t.lower()
                    or "open session for tutor and tutee" in t.lower()
                ):
                    t = "Tutor Time"
                res[r][c] = t
                if cell.is_merge_origin:
                    for sh in range(cell.span_height):
                        for sw in range(cell.span_width):
                            res[r + sh][c + sw] = t

    return [x[1:] for x in res[1:]]


def filter_mail_results_by_sender(
    original: Iterable[dict[str, Any]], sender: str
) -> Iterator[dict[str, Any]]:
    for hit in original:
        if (
            hit["resource"]["sender"]["emailAddress"]["address"].lower()
            == sender.lower()
        ):
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


def download_menu(
    token: str,
    datetime_target: datetime.datetime,
    weekly_menu_query_string: str,
    weekly_menu_sender: str,
    weekly_menu_subject_regex: str,
    weekly_menu_subject_regex_four_groups: tuple[int, int, int, int],
    menu_en_filename: str,
    menu_zh_filename: str,
    menu_pdf_filename: str,
) -> None:
    search_results = search_mail(token, weekly_menu_query_string)

    for hit, matched_groups in filter_mail_results_by_subject_regex_groups(
        filter_mail_results_by_sender(search_results, weekly_menu_sender),
        weekly_menu_subject_regex,
        weekly_menu_subject_regex_four_groups,
    ):
        try:
            subject_1st_month = datetime.datetime.strptime(
                matched_groups[0], "%B"
            ).month
            subject_1st_day = int(matched_groups[1])
        except ValueError:
            raise ValueError(hit["resource"]["subject"]) from None
        if (
            subject_1st_month == datetime_target.month
            and subject_1st_day == datetime_target.day
        ):
            break
    else:
        raise ValueError("No SJ-menu email found")

    with requests.get(
        "https://graph.microsoft.com/v1.0/me/messages/%s/$value" % hit["hitId"],
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept-Encoding": "identity",
        },
        stream=True,
    ) as r:
        msg = email.message_from_bytes(r.content)

    for part in msg.walk():
        if part.get_content_type() in [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/pdf",
        ]:
            payload = part.get_payload(decode=True)
            payload_filename_encoded = part.get_filename()
            if not payload_filename_encoded:
                raise ValueError("pptx/pdf doesn't have a filename, very unexpected")
            payload_filename_mix = email.header.decode_header(payload_filename_encoded)
            assert len(payload_filename_mix) == 1
            payload_filename_encoded, payload_filename_encoding = payload_filename_mix[
                0
            ]

            if payload_filename_encoding is None:
                assert type(payload_filename_encoded) is str
                filename = payload_filename_encoded
            elif type(payload_filename_encoded) is bytes:  # type: ignore
                filename = payload_filename_encoded.decode(payload_filename_encoding)  # type: ignore
            else:
                raise TypeError("What?")
            if (
                part.get_content_type()
                == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            ):
                if "EN" in filename:
                    lang = "en"
                    formatted_filename = menu_en_filename
                elif "CH" or "CN" in filename:
                    lang = "zh"
                    formatted_filename = menu_zh_filename
                else:
                    raise ValueError(
                        "%s does not contain a language specification string (EN/CH/CN)",
                        filename,
                    )
            elif part.get_content_type() == "application/pdf":
                formatted_filename = menu_pdf_filename

            pb = bytes(payload)

            with open(formatted_filename, "wb") as w:
                w.write(pb)


def extract_snacks(fn: str) -> tuple[list[str], list[str], list[str]]:

    visitor_state: list[Optional[float]] = [None, None]

    def visitor_1st_run(
        text: str,
        cm: list[float],
        tm: list[float],
        fdict: Optional[pypdf.generic._data_structures.DictionaryObject],
        fsize: Optional[float],
    ) -> None:
        if "students snack" in text.lower():
            visitor_state[0], visitor_state[1] = tm[-2], tm[-1]

    pdf = pypdf.PdfReader(fn)
    page = pdf.pages[2]
    page.extract_text(visitor_text=visitor_1st_run)

    snack_state: list[int] = [0]
    morning: list[str] = []
    afternoon: list[str] = []
    evening: list[str] = []

    if (not visitor_state[0]) or (not visitor_state[1]):
        page = pdf.pages[3]
        page.extract_text(visitor_text=visitor_1st_run)

        snack_state = [0]
        morning = []
        afternoon = []
        evening = []

    def visitor_2nd_run(
        text: str,
        cm: list[float],
        tm: list[float],
        fdict: Optional[pypdf.generic._data_structures.DictionaryObject],
        fsize: Optional[float],
    ) -> None:
        assert visitor_state[1] is not None
        if tm[-1] < visitor_state[1]:
            tsl = text.strip().lower()
            if "morning snack" in tsl:
                snack_state[0] = 1
            elif "afternoon snack" in tsl:
                snack_state[0] = 2
            elif "evening snack" in tsl:
                snack_state[0] = 3
            elif tsl:
                match snack_state[0]:
                    case 1:
                        morning.append(text.strip())
                    case 2:
                        afternoon.append(text.strip())
                    case 3:
                        evening.append(text.strip())
                    case _:
                        pass

    page.extract_text(visitor_text=visitor_2nd_run)

    return morning, afternoon, evening


def fix_snacks(
    extracted: tuple[list[str], list[str], list[str]]
) -> list[list[dict[str, str]]]:
    res: list[list[dict[str, str]],] = []
    for snackset in extracted:
        sres = []
        if len(snackset) % 2 == 0:
            pass
        else:
            roasted_bread = False
            actual_snack_set = []
            for p in snackset:
                if p == "Roasted Bread":
                    roasted_bread = True
                elif roasted_bread and p == "with Ham and Cheese":
                    actual_snack_set.append("Roasted Bread with Ham and Cheese")
                    roasted_bread = False
                else:
                    actual_snack_set.append(p)
            snackset = actual_snack_set
        for i in range(0, len(snackset), 2):
            sres.append({"en": snackset[i], "zh": snackset[i + 1]})
        res.append(sres)

    assert len(res) == 3
    return res


if __name__ == "__main__":
    main()
