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

from __future__ import annotations
from configparser import ConfigParser
import json
import argparse
import logging
import datetime
import zoneinfo
import os
import base64
import mimetypes
import typing

# import legacy_wikipedia

logger = logging.getLogger(__name__)

DAYNAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "Monday",
]
DAYNAMES_CHINESE = ["周一", "周二", "周三", "周四", "周五", "周六", "周日", "周一"]
DAYNAMES_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon"]


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Daily script for the Daily Bulletin")
    parser.add_argument(
        "--date",
        default=None,
        help="the day to generate for, in local time, in YYYY-MM-DD; defaults to tomorrow",
        # TODO: Verify validity of date
        # TODO: Verify consistency of date elsewhere
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
        datetime_target_aware = datetime_current_aware + datetime.timedelta(days=1)
        del datetime_current_aware
    del datetime_target_naive
    logger.info("Generating for %s" % datetime_target_aware.strftime("%Y-%m-%d %Z"))

    build_path = config["general"]["build_path"]
    os.chdir(build_path)

    cycle_data_path = config["general"]["cycle_data"]
    with open(cycle_data_path, "r", encoding="utf-8") as cycle_data_file:
        cycle_data = json.load(cycle_data_file)

    the_week_ahead_url = config["the_week_ahead"]["file_url"]

    generate(
        datetime_target_aware,
        cycle_data=cycle_data,
        the_week_ahead_url=the_week_ahead_url,
    )


def generate(
    datetime_target: datetime.datetime,
    the_week_ahead_url: str,
    cycle_data: dict[str, str],
) -> str:
    weekday_enum = datetime_target.weekday()
    weekday_en = DAYNAMES[weekday_enum]
    weekday_zh = DAYNAMES_CHINESE[weekday_enum]
    weekdays_short = DAYNAMES_SHORT[weekday_enum:]
    weekday_short = weekdays_short[0]
    next_weekday_short = weekdays_short[1]
    try:
        day_of_cycle = cycle_data[datetime_target.strftime("%Y-%m-%d")]
    except KeyError:
        day_of_cycle = "SA"
        logger.warning('Cycle day not found, using "SA"')

    for days_since_beginning in range(0, 5):
        week_start_date = datetime_target - datetime.timedelta(
            days=days_since_beginning
        )
        try:
            with open(
                "week-%s.json" % week_start_date.strftime("%Y%m%d"),
                "r",
                encoding="utf-8",
            ) as week_file:
                week_data = json.load(week_file)
        except FileNotFoundError:
            continue
        else:
            break
    else:
        raise FileNotFoundError(
            "Cannot find a week-{date}.json file without five prior days"
        )

    try:
        aod = week_data["aods"][days_since_beginning]
    except IndexError:
        logger.warning("AOD not found")
        aod = "None"

    breakfast_today = week_data["menu"]["Breakfast"][weekday_short]
    lunch_today = week_data["menu"]["Lunch"][weekday_short]
    try:
        dinner_today = week_data["menu"]["Dinner"][weekday_short]
    except KeyError:
        dinner_today = None
    try:
        breakfast_tomorrow = week_data["menu"]["Breakfast"][next_weekday_short]
    except KeyError:
        breakfast_tomorrow = None
    try:
        snack_morning = week_data["snacks"]["Morning"][days_since_beginning]
    except (KeyError, IndexError):
        snack_morning = None
    try:
        snack_afternoon = week_data["snacks"]["Afternoon"][days_since_beginning]
    except (KeyError, IndexError):
        snack_afternoon = None
    try:
        snack_evening = week_data["snacks"]["Evening"][days_since_beginning]
    except (KeyError, IndexError):
        snack_evening = None

    logger.info("Checking for inspirations")
    # TODO: Should probably allow inspirations to be reused on the same day
    # e.g. "used" should be set to the date it was used on
    for inspfn in os.listdir():
        if not inspfn.startswith("inspire-"):
            continue
        with open(inspfn, "r", encoding="utf-8") as inspfd:
            inspjq = json.load(inspfd)
            if (not inspjq["approved"]) or inspjq["used"]:
                continue
            inspjq["used"] = True
        with open(inspfn, "w", encoding="utf-8") as inspfd:
            json.dump(inspjq, inspfd, indent="\t")
        inspiration_type = inspjq["type"]
        if inspiration_type not in ["text", "media", "canteen"]:
            logger.warning("Inspiration type for %s invalid, skipping" % inspfn)
            continue
        inspiration_origin = inspjq["origin"]
        inspiration_shared_by = inspjq["uname"]
        inspiration_text = inspjq["text"]
        inspiration_image_fn = inspjq["file"]
        if inspiration_image_fn:
            logger.info("Inspiration has attachment %s" % inspiration_image_fn)
            inspiration_image_mime, inspiration_image_extra_encoding = (
                mimetypes.guess_type(inspiration_image_fn)
            )
            assert not inspiration_image_extra_encoding
            with open(
                "inspattach-%s" % os.path.basename(inspiration_image_fn), "rb"
            ) as ifd:
                inspiration_image_data = base64.b64encode(ifd.read()).decode("ascii")
        else:
            inspiration_image_data = None
            inspiration_image_mime = None
        break
    else:
        inspiration_image_data = None
        inspiration_image_mime = None
        inspiration_type = None
        inspiration_origin = None
        inspiration_shared_by = None
        inspiration_text = None
        inspiration_image_fn = None

    logger.info("Finished processing inspirations")
    logger.info("Starting On This Day")

    on_this_day_html_en = None
    on_this_day_html_zh = None
    # on_this_day_html_en: typing.Optional[str]
    # try:
    #     with open("otd_en-%s.html" % datetime_target.strftime("%m-%d"), "r") as fd:
    #         on_this_day_html_en = fd.read()
    # except FileNotFoundError:
    #     logger.warning("On This Day English not found")
    # on_this_day_html_zh: typing.Optional[str]
    # try:
    #     with open("otd_zh-%s.html" % datetime_target.strftime("%m-%d"), "r") as fd:
    #         on_this_day_html_zh = fd.read()
    # except FileNotFoundError:
    #     logger.warning("On This Day Chinese not found")
    # logger.info("Finished On This Day")

    in_the_news_html_en = None
    in_the_news_html_zh = None
    # logger.info("Starting In The News")
    # in_the_news_html_en = legacy_wikipedia.get_in_the_news_en()
    # in_the_news_html_zh = legacy_wikipedia.get_in_the_news_zh()
    # logger.info("Finished In The News")

    data = {
        "stddate": datetime_target.strftime("%Y-%m-%d"),
        "community_time": week_data["community_time"][days_since_beginning:],
        "days_after_this": len(week_data["community_time"][days_since_beginning:]) - 1,
        "aod": aod,
        "weekday_english": weekday_en,
        "weekdays_abbrev": weekdays_short,
        "weekday_chinese": weekday_zh,
        "day_of_cycle": day_of_cycle,
        "today_breakfast": breakfast_today,
        "today_lunch": lunch_today,
        "today_dinner": dinner_today,
        "next_breakfast": breakfast_tomorrow,
        "the_week_ahead_url": the_week_ahead_url,
        "today_snack": {
            "Morning": snack_morning,
            "Afternoon": snack_afternoon,
            "Evening": snack_evening,
        },
        "inspiration_type": inspiration_type,
        "inspiration_shared_by": inspiration_shared_by,
        "inspiration_origin": inspiration_origin,
        "inspiration_text": inspiration_text,
        "inspiration_image_data": inspiration_image_data,
        "inspiration_image_mime": inspiration_image_mime,
        "on_this_day_html_en": on_this_day_html_en,
        "on_this_day_html_zh": on_this_day_html_zh,
        "in_the_news_html_en": in_the_news_html_en,
        "in_the_news_html_zh": in_the_news_html_zh,
    }
    with open(
        "day-%s.json" % datetime_target.strftime("%Y%m%d"), "w", encoding="utf-8"
    ) as fd:
        json.dump(data, fd, ensure_ascii=False, indent="\t")
    logger.info(
        "Data dumped to " + "day-%s.json" % datetime_target.strftime("%Y%m%d"),
    )
    return "day-%s.json" % datetime_target.strftime("%Y%m%d")


if __name__ == "__main__":
    main()
