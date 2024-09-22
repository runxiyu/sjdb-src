#!/usr/bin/env python3
#
# Utility functions to parse the XLSX menu for the Daily Bulletin
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

import openpyxl
from pprint import pprint
import json


def menu_item_fix(s):
    if not s:
        return None
    if s == "Condiments Selection\n葱，香菜，榨菜丝，老干妈，生抽，醋":
        return None
    return (
        s.strip()
        .replace("Biscuit /", "Biscuit/")
        .replace("Juice /", "Juice/")
        .replace(" \n", "\n")
        .replace("\n ", "\n")
    )


rows = list(ws.iter_rows())


def parse_meal_table(rows, initrow, t):
    assert rows[initrow + 1][1].value is None

    igroups = []
    i = initrow + 2
    while True:
        c = rows[i][1]
        if not isinstance(c, openpyxl.cell.MergedCell):
            igroups.append(i)
        i += 1
        if len(igroups) >= len(t):
            break
    wgroups = dict(zip(igroups + [i], t + [None]))

    ret = {}
    kmap = {}
    for k in range(2, 7):
        ret[rows[initrow + 1][k].value[0:3]] = {}
        kmap[k] = rows[initrow + 1][k].value[0:3]

    i = 0
    wgroupskeys = list(wgroups.keys())
    while i < len(wgroupskeys) - 1:
        wgroup = wgroups[wgroupskeys[i]]
        for km in ret:
            ret[km][wgroup] = []
        for j in range(wgroupskeys[i], wgroupskeys[i + 1]):
            for k in range(2, 7):
                v = menu_item_fix(rows[j][k].value)
                if v:
                    ret[kmap[k]][wgroup].append(v)
        i += 1

    return ret


def parse_menus(filename):
    wb = openpyxl.load_workbook(filename=filename)
    ws = wb["菜单"]

    final = {}

    i = -1
    while i < len(rows) - 1:
        i += 1
        row = rows[i]
        if not isinstance(row[1].value, str):
            continue
        elif "BREAKFAST" in row[1].value:
            final["Breakfast"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Self Pick-up",  # instead of veg and soup
                    "Fruit/Drink",
                ],
            )
        elif "LUNCH" in row[1].value:
            final["Lunch"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Vegetarian",
                    "Daily Soup",
                    "Dessert/Fruit/Drink",
                ],
            )
        elif "DINNER" in row[1].value:
            final["Dinner"] = parse_meal_table(
                rows,
                i,
                [
                    "Taste of Asia",
                    "Eat Global",
                    "Revolution Noodle",
                    "Piccola Italia",
                    "Vegetarian",
                    "Daily Soup",
                    "Dessert/Fruit/Drink",
                ],
            )
        # elif "Students Snack" in row[1].value:
        #    parse_meal_table(rows, i)

    return final
