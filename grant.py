from __future__ import annotations
from typing import Optional, Any, Callable
import os
from configparser import ConfigParser
from office365.graph_client import GraphClient # type: ignore
import msal # type: ignore
import logging

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

def acquire_consent(config: ConfigParser) -> None:
    client = GraphClient.with_token_interactive(
        config["credentials"]["tenant_id"], config["credentials"]["client_id"]
    )
    me = client.me.get().execute_query()
    if not me.given_name:
        raise ValueError("Cannot acquire consent") from None


def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    print("Acquiring consent... check your web browser")
    acquire_consent(config)
    print("Finished acquiring consent, verifying login...")
    client = GraphClient(acquire_token(config))
    me = client.me.get().execute_query()
    print("Authentication complete and verified with account %s." % me.user_principal_name)

if __name__ == "__main__":
    main()
