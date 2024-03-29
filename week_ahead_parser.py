from __future__ import annotations
from typing import Optional, Any
from pprint import pprint
import os
from configparser import ConfigParser
from datetime import datetime
import json
import tempfile

DAYNAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def download_from_sharepoint(
    sharepoint_site_url: str,
    sharing_link_url: str,
    credentials: tuple[str, str],
    output_to: Optional[str] = None,
) -> str:
    # TODO: Is the return type correct?
    from office365.sharepoint.client_context import ClientContext  # type: ignore
    from office365.runtime.auth.user_credential import UserCredential  # type: ignore

    client = ClientContext(sharepoint_site_url).with_credentials(
        UserCredential(*credentials)
    )
    if not output_to:
        fd, output_to = tempfile.mkstemp()
        # TODO: Is it safe to just discard fd?
    with open(output_to, "wb") as local_file:
        client.web.get_file_by_guest_url(sharing_link_url).download(
            local_file
        ).execute_query()
    return output_to


def download_the_week_ahead(
    config: ConfigParser,
) -> None:  # TODO: What happens when the download fails?
    credentials = (config["credentials"]["username"], config["credentials"]["password"])
    sharepoint_site_url = config["the_week_ahead"]["site_url"]
    sharing_link_url = config["the_week_ahead"]["file_url"]
    output_to = config["the_week_ahead"]["local_filename"]
    download_from_sharepoint(
        sharepoint_site_url, sharing_link_url, credentials, output_to
    )


def extract_community_time_from_presentation(config: ConfigParser) -> list[list[str]]:
    from pptx import Presentation  # type: ignore

    prs = Presentation(config["the_week_ahead"]["local_filename"])
    slide = prs.slides[int(config["the_week_ahead"]["community_time_page_number"])]
    for shape in slide.shapes:
        if not shape.has_table:
            continue
    tbl = shape.table
    row_count = len(tbl.rows)
    col_count = len(tbl.columns)
    if row_count != 5 or col_count != 5:
        raise ValueError(
            "Community time parsing: The Week Ahead community time table is not 5x5"
        )
    tbll = []
    for r in range(row_count):
        row = [""] * col_count
        for c in range(col_count):
            cell_text = ""
            cell = tbl.cell(r, c)
            paragraphs = cell.text_frame.paragraphs
            for paragraph in paragraphs:
                for run in paragraph.runs:
                    cell_text += run.text
            if not cell_text.strip():
                cell_text = old_cell_text  # type: ignore
                # TODO: There's probably a more robust way to detect whether a cell spans multiple columns but I'm lazy
                # TODO: Yes of course there's a way to detect that i.e. cell.is_merge_origin, cell.is_spanned, cell.span_height, cell.span_width
            row[c] = cell_text
            old_cell_text = cell_text
        tbll.append(row)
    return tbll


def extract_aod_from_presentation(config: ConfigParser) -> list[str]:
    from pptx import Presentation

    prs = Presentation(config["the_week_ahead"]["local_filename"])
    slide = prs.slides[int(config["the_week_ahead"]["aod_page_number"])]

    aods = ["", "", "", ""]
    for shape in slide.shapes:
        if hasattr(shape, "text") and "Monday: " in shape.text:
            slist = shape.text.split("\n")
            for s in slist:
                try:
                    day, aod = s.split(": ", 1)
                except ValueError:
                    pass
                day = day.lower()
                if day == "monday":
                    aods[0] = aod
                elif day == "tuesday":
                    aods[1] = aod
                elif day == "wednesday":
                    aods[2] = aod
                elif day == "thursday":
                    aods[3] = aod
            if not all(aods):
                raise ValueError(
                    "AOD parsing: The Week Ahead doesn't include all AOD days, or the formatting is borked"
                )
            return aods
            break
    else:
        raise ValueError(
            "AOD parsing: The Week Ahead's doesn't even include \"Monday\""
        )


def fix_community_time(tbll: list[list[str]]) -> list[list[str]]:
    res = []
    for i in range(1, 5):
        day = tbll[i]
        dayl = [DAYNAMES[i]]
        for j in range(1, len(day)):
            text = day[j]
            if "whole school assembly" in text.lower():
                dayl.append("Whole School Assembly")
            elif (
                "tutor group check-in" in text.lower()
                or "follow up day" in text.lower()
            ):
                dayl.append("Tutor Time")
            else:
                dayl.append(text.strip())
        res.append(dayl)
    return res


def main() -> None:
    today = datetime.today().strftime("%Y%m%d")
    config = ConfigParser()
    config.read("config.ini")
    # download_the_week_ahead(config)
    data = {
        "community_time_days": fix_community_time(
            extract_community_time_from_presentation(config)
        ),
        "aods": extract_aod_from_presentation(config),
    }
    with open(os.path.join("build/", today + "-data.json"), "w") as fd:
        json.dump(data, fd)


if __name__ == "__main__":
    main()
