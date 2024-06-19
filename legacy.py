#!/usr/bin/env python3
#
# Legacy Daily Bulletin components that need to be replaced
# Copyright (C) 2024      Runxi Yu <https://runxiyu.org>
# Copyright (C) 2023-2024 Albert Tan <albert-tan@qq.com>
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
import re
import copy
import datetime

import requests
import bs4


def get_on_this_day_zh() -> None:
    months = list(map(lambda x: str(x) + "月", range(1, 13)))

    for index in range(12):

        month = months[index]
        day = 1

        url = "https://zh.m.wikipedia.org/zh-cn/Wikipedia:历史上的今天/" + month
        response = requests.get(url)
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        div_elements = soup.find_all("div", class_="selected-anniversary")

        for div_element in div_elements:

            datetime_time = datetime.datetime(2000, index + 1, day)
            formatted_time_yearless = datetime_time.strftime("%m-%d")

            p_element = div_element.find("p")
            dl_element = div_element.find("dl")
            event_elements = dl_element.find_all("div", class_="event")
            ul_element = soup.new_tag("ul")

            for event in event_elements:
                li_element = soup.new_tag("li")
                li_element.append(event)
                ul_element.append(li_element)

            result = str(p_element).replace(
                "/wiki", "https://zh.wikipedia.org/zh-cn"
            ).replace('<span class="otd-year">', "<b>").replace(
                "</span>：", "：</b>"
            ) + str(
                ul_element
            ).replace(
                "/wiki", "https://zh.wikipedia.org/zh-cn"
            ).replace(
                "</dt><dd>", " – "
            ).replace(
                '<div class="event">\n<dt>', ""
            ).replace(
                "</dd>\n</div>", ""
            )
            result = re.sub(r"<small>.*?图.*?</small>", "", result)

            with open(formatted_time_yearless + ".html", "w") as file:
                file.write(result)
                file.close()
                day += 1


def get_on_this_day_en() -> None:
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    for index in range(12):

        month = months[index]
        day = 1
        url = (
            "https://en.m.wikipedia.org/wiki/Wikipedia:Selected_anniversaries/" + month
        )
        response = requests.get(url)
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        p_elements = soup.find_all("p")

        for p_element in p_elements:

            try:
                datetime_time = datetime.datetime(2000, index + 1, day)
                formatted_time_yearless = datetime_time.strftime("%m-%d")
            except ValueError:
                break

            if not re.search(
                f'<p><b><a href="/wiki/{month}_\\d+" title="{month} \\d+">{month} \\d+</a></b',
                str(p_element),
            ):
                continue
            div_element = p_element.find_next("div")
            ul_element = div_element.find_next_sibling("ul")
            ul_element_2 = ul_element.find_next("ul")
            p_element_2 = soup.new_tag("p")
            li_contents = list(ul_element_2.find_all("li"))

            for li in li_contents:
                p_element_2.append(li)

            result = (
                str(p_element).replace("/wiki", "https://en.wikipedia.org/wiki")
                + str(ul_element).replace("/wiki", "https://en.wikipedia.org/wiki")
                + "\n"
                + str(p_element_2)
                .replace("</li><li>", "; ")
                .replace("<li>", "<b>Births and Deaths: </b>")
                .replace("</li>", "")
                .replace("/wiki", "https://en.wikipedia.org/wiki")
            )
            result = re.sub(r" <i>.*?icture.*?</i>", "", result)

            with open(formatted_time_yearless + ".html", "w") as file:
                file.write(result)
                file.close()
                day += 1


def get_in_the_news_en() -> None:
    url = "https://en.m.wikipedia.org/wiki/Main_Page"
    response = requests.get(url)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")

    h2_element = soup.find("h2", id="mp-itn-h2")
    assert h2_element
    ul_element = h2_element.find_next("ul")
    assert ul_element
    ul_element_2 = ul_element.find_next("ul")
    assert ul_element_2
    div_element = ul_element_2.find_next("div")
    assert div_element
    ul_element_3 = div_element.find_next("ul")
    assert ul_element_3

    p_element_2 = soup.new_tag("p")
    p_element_3 = soup.new_tag("p")
    assert isinstance(ul_element_2, bs4.Tag)
    assert isinstance(ul_element_3, bs4.Tag)
    li_contents_2 = list(ul_element_2.find_all("li"))
    li_contents_3 = list(ul_element_3.find_all("li"))
    skip = False
    for li in li_contents_2:
        if skip:
            skip = False
            continue
        if li.find("ul"):
            new_li = copy.deepcopy(li)
            new_li.find("ul").decompose()
            p_element_2.append(new_li)
            skip = True
        else:
            p_element_2.append(li)
    for li in li_contents_3:
        if skip:
            skip = False
            continue
        if li.find("ul"):
            new_li = copy.deepcopy(li)
            new_li.find("ul").decompose()
            p_element_3.append(new_li)
            skip = True
        else:
            p_element_3.append(li)

    result = (
        str(ul_element).replace("/wiki", "https://en.wikipedia.org/wiki")
        + str(p_element_2)
        .replace("</li><li>", "; ")
        .replace("<li>", "<b>Ongoing: </b>")
        .replace("</li>", "")
        .replace("\n;", ";")
        .replace("/wiki", "https://en.wikipedia.org/wiki")
        .replace("</p>", "<br>")
        + str(p_element_3)
        .replace("</li><li>", "; ")
        .replace("<li>", "<b>Recent deaths: </b>")
        .replace("</li>", "")
        .replace("\n;", ";")
        .replace("/wiki", "https://en.wikipedia.org/wiki")
        .replace("<p>", "")
    )
    result = re.sub(r" <i>\(.*?\)</i>", "", result)

    with open("latest.html", "r") as file:
        existing_content = file.read()

    if existing_content != result:
        datetime_time = datetime.datetime.today() + datetime.timedelta(days=-1)
        formatted_time = datetime_time.strftime("%Y-%m-%d")
        new_filename = formatted_time + ".html"

        with open(new_filename, "w") as file:
            file.write(existing_content)
            file.close()

        with open("latest.html", "w") as file:
            file.write(result)
            file.close()


def get_in_the_news_zh() -> None:
    url = "https://zh.m.wikipedia.org/zh-cn/Wikipedia:%E9%A6%96%E9%A1%B5"
    response = requests.get(url)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")

    div_element = soup.find("div", id="column-itn")
    assert div_element
    ul_element = div_element.find("ul")
    assert isinstance(ul_element, bs4.Tag)
    ul_element_2 = ul_element.find_next("ul")
    assert isinstance(ul_element_2, bs4.Tag)
    ul_element_3 = ul_element_2.find_next("ul")
    assert isinstance(ul_element_3, bs4.Tag)
    span_element_2 = ul_element_2.find("span", class_="hlist inline")
    span_element_3 = ul_element_3.find("span", class_="hlist inline")
    assert span_element_2 and span_element_3
    p_element_2 = soup.new_tag("p")
    p_element_3 = soup.new_tag("p")
    p_element_2.append(span_element_2)
    p_element_3.append(span_element_3)

    result = (
        str(ul_element).replace("/wiki", "https://zh.wikipedia.org/zh-cn")
        + str(p_element_2)
        .replace('<span class="hlist inline">', "<b>正在发生：</b>")
        .replace("</span>", "")
        .replace("－", "；")
        .replace(
            '（<a href="/wiki/%E4%BF%84%E7%BE%85%E6%96%AF%E5%85%A5%E4%BE%B5%E7%83%8F%E5%85%8B%E8%98%AD%E6%99%82%E9%96%93%E8%BB%B8" title="俄罗斯入侵乌克兰时间轴">时间轴</a>）',
            "",
        )
        .replace("/wiki", "https://zh.wikipedia.org/zh-cn")
        + str(p_element_3)
        .replace('<span class="hlist inline">', "<b>最近逝世：</b>")
        .replace("</span>", "")
        .replace("－", "；")
        .replace("/wiki", "https://zh.wikipedia.org/zh-cn")
    ).replace("</p><p>", "<br>")
    result = re.sub(r"<small.*?>.*?</small>", "", result)

    with open("latest.html", "r") as file:
        existing_content = file.read()

    if existing_content != result:
        datetime_time = datetime.datetime.today() + datetime.timedelta(days=-1)
        formatted_time = datetime_time.strftime("%Y-%m-%d")
        new_filename = formatted_time + ".html"

        with open(new_filename, "w") as file:
            file.write(existing_content)
            file.close()

        with open("latest.html", "w") as file:
            file.write(result)
            file.close()
