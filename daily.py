#!/usr/bin/env python3
#
# Daily script to prepare the YK Pao School Daily Bulletin Copyright (C) 2024
# Runxi Yu <https://runxiyu.org>
#
# This program is free softhe_week_aheadre: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Softhe_week_aheadre Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
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

    cycle_data_path = config["general"]["cycle_data"]
    with open(cycle_data_path, "r") as cycle_data_file:
        cycle_data = json.load(cycle_data_file)

    build_path = config["general"]["build_path"]
    os.chdir(build_path)

    generate(datetime_target_aware, cycle_data=cycle_data)


def generate(datetime_target: datetime.datetime, cycle_data: dict[str, str]) -> str:
    weekday_enum = datetime_target.weekday()
    weekday_en = DAYNAMES[weekday_enum]
    weekday_zh = DAYNAMES_CHINESE[weekday_enum]
    weekday_short = DAYNAMES_SHORT[weekday_enum]
    next_weekday_short = DAYNAMES_SHORT[weekday_enum + 1]
    try:
        day_of_cycle = cycle_data[datetime_target.strftime("%Y-%m-%d")]
    except KeyError:
        day_of_cycle = "SA"
        logger.info('Note: Cycle day not found, using "SA"')

    for days_since_beginning in range(0, 5):
        week_start_date = datetime_target - datetime.timedelta(
            days=days_since_beginning
        )
        try:
            with open(
                "week-%s.json" % week_start_date.strftime("%Y%m%d"), "r"
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

    breakfast_today = week_data["menu"]["breakfast"][days_since_beginning]
    lunch_today = week_data["menu"]["lunch"][days_since_beginning]
    dinner_today = week_data["menu"]["dinner"][days_since_beginning]
    try:
        breakfast_tomorrow = week_data["menu"]["breakfast"][days_since_beginning + 1]
    except IndexError:
        breakfast_tomorrow = None

    data = {
        "stddate": datetime_target.strftime("%Y-%m-%d"),
        "community_time": week_data["community_time"][days_since_beginning:],
        "aod": aod,
        "weekday_english": weekday_en,
        "weekday_abbrev": weekday_short,
        "next_weekday_abbrev": next_weekday_short,  # TODO: Check if EOW
        "weekday_chinese": weekday_zh,
        "day_of_cycle": day_of_cycle,
        "today_breakfast": breakfast_today,
        "today_lunch": lunch_today,
        "today_dinner": dinner_today,
        "next_breakfast": breakfast_tomorrow,
    }
    with open("day-%s.json" % datetime_target.strftime("%Y%m%d"), "w") as fd:
        json.dump(data, fd, ensure_ascii=False, indent="\t")
    logger.info(
        "Data dumped to " + "day-%s.json" % datetime_target.strftime("%Y%m%d"),
    )
    return "day-%s.json" % datetime_target.strftime("%Y%m%d")


if __name__ == "__main__":
    main()
