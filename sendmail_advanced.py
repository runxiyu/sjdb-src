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
        subject,                                                                  
        body,                                                         
        to_recipients,                                     
        cc_recipients=None,                             
        bcc_recipients=None,                                        
        save_to_sent_items=True,                         
    ):                                                              
        """Send a new message on the fly
 
        :param str subject: The subject of the message.           
        :param str body: The body of the message. It can be in HTML or text format
        :param list[str] to_recipients: The To: recipients for the message.
        :param list[str] cc_recipients: The CC: recipients for the message.
        :param list[str] bcc_recipients: The BCC: recipients for the message.
        :param bool save_to_sent_items: Indicates whether to save the message in Sent Items. Specify it only if
            the parameter is false; default is true      
        """                                                    
        return_type = Message(me.context)               
        return_type.subject = subject                                   
        return_type.body = body  
        [
            return_type.to_recipients.add(Recipient.from_email(email))
            for email in to_recipients
        ]
        if bcc_recipients is not None:
            [
                return_type.bcc_recipients.add(Recipient.from_email(email))
                for email in bcc_recipients
            ]
        if cc_recipients is not None:
            [
                return_type.cc_recipients.add(Recipient.from_email(email))
                for email in cc_recipients
            ]
 
        payload = {"message": return_type, "saveToSentItems": save_to_sent_items}
        qry = ServiceOperationQuery(me, "sendmail", None, payload)
        me.context.add_query(qry)
        return return_type

def sendmail(client: GraphClient, config: ConfigParser) -> None:
    _send_mail(client.me,
        subject=config["test_sendmail"]["subject"],
        body=open(config["test_sendmail"]["local_html_path"], "r").read(),
        to_recipients=config["test_sendmail"]["recipients"].split(" "),
        save_to_sent_items=True,
    ).execute_query()


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    client = get_client(config)
    sendmail(client, config)


if __name__ == "__main__":
    main()
