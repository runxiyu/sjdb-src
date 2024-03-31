from __future__ import annotations
from typing import Optional, Any, Callable
from pprint import pprint
import os
from configparser import ConfigParser
from datetime import datetime
import json
import tempfile
from office365.graph_client import GraphClient  # type: ignore
from office365.outlook.mail.messages.message import Message
from office365.outlook.mail.recipient import Recipient
from office365.runtime.queries.service_operation import ServiceOperationQuery


import msal  # type: ignore
import logging

loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(logging.DEBUG)


def get_client(config: ConfigParser) -> GraphClient:
    return GraphClient.with_username_and_password(
        config["credentials"]["tenant_id"],
        config["credentials"]["client_id"],
        config["credentials"]["username"],
        config["credentials"]["password"],
    )

def _send_mail(                                                             
        me,                                             
        msg: Message,
        save_to_sent_items=True,                         
    ):                                                              
        qry = ServiceOperationQuery(me, "sendmail", None, {"message": msg, "saveToSentItems": save_to_sent_items})
        me.context.add_query(qry)
        return msg
        # what should I return?

def sendmail(client: GraphClient, config: ConfigParser) -> None:
    # construct the message
    msg = Message(client.me.context)
    msg.subject = config["test_sendmail"]["subject"]
    msg.body = open(config["test_sendmail"]["local_html_path"]).read() # TODO

    to_recipients = [a for a in config["test_sendmail"]["to"].split(" ") if a]
    bcc_recipients = [a for a in config["test_sendmail"]["bcc"].split(" ") if a]
    cc_recipients = [a for a in config["test_sendmail"]["cc"].split(" ") if a]
    print(to_recipients, bcc_recipients, cc_recipients)
    if to_recipients:
        for email in to_recipients:
            msg.to_recipients.add(Recipient.from_email(email))
    if bcc_recipients:
        for email in bcc_recipients:
            msg.bcc_recipients.add(Recipient.from_email(email))
    if cc_recipients:
        for email in cc_recipients:
            msg.cc_recipients.add(Recipient.from_email(email))

    _send_mail(client.me,
        msg=msg,
        save_to_sent_items=True,
    ).execute_query()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    client = get_client(config)
    sendmail(client, config)


if __name__ == "__main__":
    main()
