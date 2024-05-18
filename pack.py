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

from jinja2 import Template, StrictUndefined
from configparser import ConfigParser
import os
import json
import datetime
import argparse
import logging
import zoneinfo


def main(date: str, config: ConfigParser) -> None:

    with open("templates/template.html", "r") as template_file:
        template = Template(template_file.read(), undefined=StrictUndefined)

    with open(
        os.path.join("build", "day-" + date.replace("-", "") + ".json"), "r"
    ) as fd:
        data = json.load(fd)

    # extra_data = {
    # }
    #
    # data = data | extra_data

    template.stream(**data).dump(
        os.path.join("build", "sjdb-%s.html" % date.replace("-", ""))
    )

    # FIXME: Escape the dangerous HTML!


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO)
        parser = argparse.ArgumentParser(description="Daily Bulletin Packer")
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
            now = datetime.datetime.now(
                zoneinfo.ZoneInfo(config["general"]["timezone"])
            )
            date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        logging.info("Generating for day %s" % date)
        # main(date, config)
        main(date, config)
    except KeyboardInterrupt:
        logging.critical("KeyboardInterrupt")
