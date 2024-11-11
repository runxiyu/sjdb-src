#!/usr/bin/env python3
#
# Help in Daily Bulletin template development by dynamically filling templates
# with flask as the templates are being worked on. DO NOT USE IN PRODUCTION.
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
from typing import Union, TypeAlias
import json
import datetime
import zoneinfo
import os
import configparser
from jinja2 import StrictUndefined
from werkzeug.wrappers.response import Response as werkzeugResponse
from flask import (
    Flask,
    Response,
    render_template,
)

ResponseType: TypeAlias = Union[Response, werkzeugResponse, str]

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined

config = configparser.ConfigParser()
config.read("config.ini")


# extra_data = {
#     "aod": data["aods"][0],  # FIXME
#     "stddate": "2024-04-01",
#     "weekday_english": "Monday",
#     "weekday_abbrev": "Mon",
#     "next_weekday_abbrev": "Tue",
#     "weekday_chinese": "周一",
#     "day_of_cycle": "SA",
#     "today_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
#     "today_lunch": ("1", "2", "3", "4", "5", "6", "7", "8"),
#     "today_dinner": ("1", "2", "3", "4", "5", "6", "7", "8"),
#     "next_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
# }
#
# data = data | extra_data


@app.route("/")
def index() -> ResponseType:
    with open(
        os.path.join(
            config["general"]["build_path"],
            "day-%s.json"
            % (
                datetime.datetime.now(tz=zoneinfo.ZoneInfo("Asia/Shanghai"))
                + datetime.timedelta(days=1)
            ).strftime("%Y%m%d"),
        ),
        "r",
        encoding="utf-8",
    ) as fd:
        data = json.load(fd)
    return render_template("template.html", **data)


@app.route("/<date>")
def date(date: str) -> ResponseType:
    with open(
        os.path.join(config["general"]["build_path"], "day-%s.json" % date),
        "r",
        encoding="utf-8",
    ) as fd:
        data = json.load(fd)
    return render_template("template.html", **data)


# The lack of the __name__ check is intentional. This script should not be used
# in a production server.

app.run(port=8000, debug=True, use_reloader=True)
