from __future__ import annotations
from typing import Optional, Any
import os
from configparser import ConfigParser
from datetime import datetime
import json
import tempfile
import pptx  # type: ignore
import pptx.exc  # type: ignore
from pprint import pprint

DAYNAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def slide_to_srep(slide: pptx.slide) -> list[list[tuple[str, int, int, str]]]:
    for shape in slide.shapes:
        if shape.has_table:
            break
    else:
        raise ValueError("Slide doesn't contain any tables?")
    tbl = shape.table
    row_count: int = len(tbl.rows)
    col_count: int = len(tbl.columns)
    tbll = []
    for r in range(row_count):
        row: list[tuple[str, int, int, str]] = [("", 0, 0, "")] * col_count
        old_cell_text = ""
        for c in range(col_count):
            cell_text = ""
            cell = tbl.cell(r, c)
            assert type(cell.span_height) is int
            assert type(cell.span_width) is int
            paragraphs = cell.text_frame.paragraphs
            for paragraph in paragraphs:
                for run in paragraph.runs:
                    cell_text += run.text
            row[c] = (
                "o" if cell.is_merge_origin else ("s" if cell.is_spanned else "n"),
                cell.span_height,
                cell.span_width,
                cell_text.strip(),
            )
            old_cell_text = cell_text
        tbll.append(row)
    return tbll


def zero_list(l: list[Any]) -> list[Any]:
    return [(zero_list(i) if (isinstance(i, list)) else "") for i in l]


def equal_shapes(a: list[Any], b: list[Any]) -> bool:
    return zero_list(a) == zero_list(b)


def parse_meal_tables(
    tbl: list[list[tuple[str, int, int, str]]]
) -> list[list[list[str]]]:
    windows = []
    for j in range(1, len(tbl)):
        cell = tbl[j][0]
        if cell[0] in ["o", "n"]:
            windows.append((j, j - 1 + cell[1]))

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    daysmenus: list[list[list[str]]] = [[], [], [], [], []]

    assert len(tbl[0]) == 6

    for i in range(1, len(tbl[0])):
        for s, f in windows:
            thiswindow = []
            for j in range(s, f + 1):
                if (
                    tbl[j][i][-1].strip()
                    and tbl[j][i][-1].strip().lower() != "condiments selection"
                ):
                    thiswindow.append(tbl[j][i][-1])
            daysmenus[i - 1].append(thiswindow)
    return daysmenus


def combine_parsed_meal_tables(
    en: list[list[list[str]]], cn: list[list[list[str]]]
) -> list[list[list[str]]]:
    if not equal_shapes(cn, en):
        raise ValueError("Augmented menus not in the same shape")

    c = zero_list(en)

    for j in range(len(en)):
        for i in range(len(en[j])):
            for k in range(len(en[j][i])):
                c[j][i][k] = en[j][i][k] + "\n" + cn[j][i][k]
    return c


def extract_all_menus(
    filename_en: str, filename_cn: str, config: ConfigParser
) -> list[list[list[list[str]]]]:
    try:
        enprs = pptx.Presentation(filename_en)
        cnprs = pptx.Presentation(filename_cn)
    except pptx.exc.PackageNotFoundError:
        raise ValueError("Presentation path doesn't exist or is broken") from None

    return [
        combine_parsed_meal_tables(
            parse_meal_tables(
                slide_to_srep(
                    enprs.slides[int(config["weekly_menu"]["%s_page_number" % meal])]
                )
            ),
            parse_meal_tables(
                slide_to_srep(
                    cnprs.slides[int(config["weekly_menu"]["%s_page_number" % meal])]
                )
            ),
        )
        for meal in ["breakfast", "lunch", "dinner"]
    ]


def main() -> None:
    today = datetime.today().strftime("%Y%m%d")
    config = ConfigParser()
    config.read("config.ini")
    open("build/menu.json", "w").write(
        json.dumps(
            extract_all_menus(
                "build/20240408-menu-en.pptx", "build/20240408-menu-cn.pptx", config
            ),
            ensure_ascii=False,
            indent=4,
        )
    )


if __name__ == "__main__":
    main()
