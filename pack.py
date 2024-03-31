from jinja2 import Template, StrictUndefined
import os
import json
from datetime import datetime

with open("templates/template.html", "r") as template_file:
    template = Template(template_file.read(), undefined=StrictUndefined)


with open(
    os.path.join("build", datetime.today().strftime("%Y%m%d") + "-data.json"), "r"
) as fd:
    data = json.load(fd)

extra_data = {
    "aod": data["aods"][0],  # FIXME
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

template.stream(**data).dump("build/test.html")

# FIXME: Escape the dangerous HTML!
