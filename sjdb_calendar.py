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
