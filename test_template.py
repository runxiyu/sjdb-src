#!/usr/bin/env python3

from __future__ import annotations
from typing import Union, TypeAlias
from jinja2 import Template, StrictUndefined
import json
from flask import (
    Flask,
    Response,
    render_template,
    request,
    redirect,
    abort,
    send_from_directory,
    make_response,
)
from werkzeug.wrappers.response import Response as werkzeugResponse
from datetime import datetime
import os

ResponseType: TypeAlias = Union[Response, werkzeugResponse, str]

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined

with open(
    os.path.join("build", datetime.today().strftime("%Y%m%d") + "-data.json"), "r"
) as fd:
    data = json.load(fd)

extra_data = {
    "aod": data["aods"][0], # FIXME
    "stddate": "2024-04-01",
    "weekday_english": "Monday",
    "weekday_abbrev": "Mon",
    "next_weekday_abbrev": "Tue",
    "weekday_chinese": "周一",
    "day_of_cycle": "SA",
    "today_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
    "today_lunch": ("1", "2", "3", "4", "5", "6", "7", "8"),
    "today_dinner": ("1", "2", "3", "4", "5", "6", "7", "8"),
    "next_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
}

data = data | extra_data


@app.route("/")
def index() -> ResponseType:
    return render_template("template.html", **data)


app.run(port=8000, debug=True, use_reloader=True)
