#!/usr/bin/env python3

from __future__ import annotations
from typing import Union, TypeAlias
from jinja2 import Template, StrictUndefined
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

ResponseType: TypeAlias = Union[Response, werkzeugResponse, str]

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined

data = {
        "stddate": "2024-04-01",
        "weekday_english": "Monday",
        "weekday_abbrev": "Mon",
        "next_weekday_abbrev": "Tue",
        "weekday_chinese": "周一",
        "day_of_cycle": "SA",
        "community_time_days": (
            ("Mon", "Assembly", "Assembly", "Assembly", "Assembly"),
            ("Tue", "Tutor time", "Tutor time", "Nope", "Nope"),
            ("Wed", "Yes", "Yes", "No", "Nope!"),
            ("Thu", "Nope!", "No!!!", "Yep.", "Yep."),
            ("Yay", "One", "Two", "Three", "Four"),
        ),
        "today_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
        "today_lunch": ("1", "2", "3", "4", "5", "6", "7", "8"),
        "today_dinner": ("1", "2", "3", "4", "5", "6", "7", "8"),
        "next_breakfast": ("1", "2", "3", "4", "5", "6", "7", "8"),
        }

@app.route("/")
def index() -> ResponseType:
    return render_template("template.html", **data)

app.run(port=8000, debug=True, use_reloader=True)
