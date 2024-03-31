from __future__ import annotations
from typing import Optional, Any, Callable
from pprint import pprint
import os
from configparser import ConfigParser
from datetime import datetime
import json
import tempfile
from office365.graph_client import GraphClient  # type: ignore
import msal  # type: ignore
import logging

loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(logging.DEBUG)


def sendmail(config: ConfigParser) -> None:
    client = GraphClient.with_username_and_password(
        config["credentials"]["tenant_id"],
        config["credentials"]["client_id"],
        config["credentials"]["username"],
        config["credentials"]["password"],
    )
    client.me.send_mail(
        subject=config["test_sendmail"]["subject"],
        body=open(config["test_sendmail"]["local_html_path"], "r").read(),
        to_recipients=config["test_sendmail"]["recipients"].split(" "),
        save_to_sent_items=True,
    ).execute_query()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    sendmail(config)


if __name__ == "__main__":
    main()
