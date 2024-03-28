import os
import json
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

with open("secrets.json", "r") as f:
    secrets = json.load(f)

client = ClientContext(
    "https://ykpaoschool-my.sharepoint.com/personal/cora_chen_ykpaoschool_cn"
).with_credentials(UserCredential(secrets["username"], secrets["password"]))

sharing_link_url = "https://ykpaoschool-my.sharepoint.com/:p:/g/personal/cora_chen_ykpaoschool_cn/ES8-D2AEochFhwvz7-fL5GEBqVI9dhtYoFi3PdKTKV04Jg"

download_path = "the_week_ahead.pptx"
with open(download_path, "wb") as local_file:
    file = (
        client.web.get_file_by_guest_url(sharing_link_url)
        .download(local_file)
        .execute_query()
    )
