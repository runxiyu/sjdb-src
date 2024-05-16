from jinja2 import Template, StrictUndefined
import os
import json
import datetime
from configparser import ConfigParser
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

    template.stream(**data).dump(os.path.join("build", "sjdb-%s.html" % date.replace("-", "")))

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
