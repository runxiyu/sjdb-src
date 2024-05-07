#!/usr/bin/env python3
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
]
DAYNAMES_CHINESE = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
DAYNAMES_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main(stddate: str, config: ConfigParser) -> None:
    date = stddate.replace("-", "")
    dtdate = datetime.datetime.strptime(stddate, "%Y-%m-%d").replace(
        tzinfo=zoneinfo.ZoneInfo(config["general"]["timezone"])
    )
    weekday_enum = dtdate.weekday()
    weekday = DAYNAMES[weekday_enum]
    weekday_chinese = DAYNAMES_CHINESE[weekday_enum]
    weekday_short = DAYNAMES_SHORT[weekday_enum]
    next_weekday_short = DAYNAMES_SHORT[weekday_enum + 1]

    cycle_data = json.load(open(config["general"]["cycle_data"], "r"))
    try:
        day_of_cycle = cycle_data[stddate]
    except KeyError:
        day_of_cycle = "SA"

    for i in range(0, 5):
        week_start_date = dtdate - datetime.timedelta(days=i)
        try:
            with open(
                os.path.join(
                    config["general"]["build_path"],
                    "week-%s.json" % week_start_date.strftime("%Y%m%d"),
                ),
                "r",
            ) as week_file:
                week_data = json.load(week_file)
        except FileNotFoundError:
            continue
        else:
            break
    else:
        raise FileNotFoundError(
            "Cannot find a week-{}.json file within five prior days"
        )

    swayindex = (dtdate - week_start_date).days

    try:
        aod = week_data["aods"][swayindex]
    except IndexError:
        aod = "None"

    breakfast_today = week_data["menu"][0][swayindex]
    lunch_today = week_data["menu"][1][swayindex]
    dinner_today = week_data["menu"][2][swayindex]
    try:
        breakfast_tomorrow = week_data["menu"][0][swayindex + 1]
    except IndexError:
        breakfast_tomorrow = None

    data = {
        "stddate": stddate,
        "community_time": week_data["community_time"][swayindex:],
        "aod": aod,
        "weekday_english": weekday,
        "weekday_abbrev": weekday_short,
        "next_weekday_abbrev": next_weekday_short,  # TODO: Check if EOW
        "weekday_chinese": weekday_chinese,
        "day_of_cycle": day_of_cycle,
        "today_breakfast": (
            breakfast_today[0],
            breakfast_today[1],
            breakfast_today[2],
            breakfast_today[3],
            None,
            None,
            None,
        ),
        "today_lunch": (
            lunch_today[0],
            lunch_today[1],
            lunch_today[2],
            lunch_today[3],
            lunch_today[4],
            lunch_today[5],
            None,
        ),
        "today_dinner": (
            (
                dinner_today[0],
                dinner_today[1],
                dinner_today[2],
                dinner_today[3],
                dinner_today[4],
                dinner_today[5],
                None,
            )
            if (dinner_today and breakfast_tomorrow)
            else None
        ),  # TODO: no breakfast tomorrow implies that the dinner for today is erroneous?
        "next_breakfast": (
            (
                breakfast_tomorrow[0],
                breakfast_tomorrow[1],
                breakfast_tomorrow[2],
                breakfast_tomorrow[3],
                None,
                None,
                None,
            )
            if breakfast_tomorrow
            else None
        ),
    }
    with open(
        os.path.join(config["general"]["build_path"], "day-" + date + ".json"), "w"
    ) as fd:
        json.dump(data, fd, ensure_ascii=False)
    logger.info(
        "Data dumped to "
        + os.path.join(config["general"]["build_path"], "day-" + date + ".json")
    )


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        parser = argparse.ArgumentParser(
            description="Daily script for the Daily Bulletin"
        )
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
        config = ConfigParser()
        config.read(args.config)
        if args.date:
            date = args.date
        else:
            now = datetime.datetime.now(pytz.timezone(config["general"]["timezone"]))
            date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        logging.info("Generating for day %s" % date)
        main(date, config)
    except KeyboardInterrupt:
        logging.critical("KeyboardInterrupt")
