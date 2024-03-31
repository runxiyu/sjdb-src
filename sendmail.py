from __future__ import annotations
from typing import Optional, Any, Callable
from pprint import pprint
import os
from configparser import ConfigParser
from datetime import datetime
import json
import tempfile
from office365.graph_client import GraphClient # type: ignore
import msal # type: ignore
import logging

loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(logging.DEBUG)


def acquire_token(config: ConfigParser) -> Callable[[], dict[str, str]]:
    def _() -> dict[str, str]:
        authority_url = "https://login.microsoftonline.com/{0}".format(
            config["credentials"]["tenant_id"]
        )
        app = msal.PublicClientApplication(
            authority=authority_url, client_id=config["credentials"]["client_id"]
        )

        result = app.acquire_token_by_username_password(
            username=config["credentials"]["username"],
            password=config["credentials"]["password"],
            scopes=["Mail.Send", "User.Read"],
        )
        assert type(result) is dict
        return result

    return _


def sendmail(config: ConfigParser) -> None:
    client = GraphClient.with_username_and_password(
        config["credentials"]["tenant_id"],
        config["credentials"]["client_id"],
        config["credentials"]["username"],
        config["credentials"]["password"],
    )
    client.me.send_mail(
        subject=config["test_sendmail"]["subject"],
        body=config["test_sendmail"]["message"],
        to_recipients=config["test_sendmail"]["recipients"].split(" "),
    ).execute_query()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    client = GraphClient(acquire_token(config))
    me = client.me.get().execute_query()
    print(me.user_principal_name)
    sendmail(config)


if __name__ == "__main__":
    main()
