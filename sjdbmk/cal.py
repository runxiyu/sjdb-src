#!/usr/bin/env python3
#
# Calendar Interpretation in the Songjiang Daily Bulletin Build System
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

from typing import Any 
import datetime

import requests

def calfetch(token: str, calendar_address: str, datetime_target: datetime.datetime) -> Any:
    calendar_response = requests.get(
        "https://graph.microsoft.com/v1.0/users/%s/calendar/calendarView" % calendar_address,
        headers={"Authorization": "Bearer " + token},
        params={
            "startDateTime": datetime_target.replace(microsecond=0).isoformat(),
            "endDateTime": (datetime_target + datetime.timedelta(days=7)).replace(microsecond=0).isoformat(),
        },
        timeout=15,
    )
    if calendar_response.status_code != 200:
        raise ValueError("Calendar response status code is not 200", calendar_response.content)
    calendar_object = calendar_response.json()
    return calendar_object
