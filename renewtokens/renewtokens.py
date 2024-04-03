import logging
import os
import threading
import requests
import time
import jwt
from functools import reduce


class TokenRefresher(threading.Thread):
    def __init__(self, log):
        self.log = log
        self.api_url = os.environ["JUPYTERHUB_API_URL"]
        self.api_token = os.environ["JUPYTERHUB_API_TOKEN"]
        self.user = os.environ["JUPYTERHUB_USER"]
        self.token_file = os.environ["BEARER_TOKEN_FILE"]

        super(self.__class__, self).__init__()

    def run(self):
        while True:
            try:
                ttl = self.refresh_token()
                self.log.info(f"oAuth token refreshed. Next in {ttl}s")
            except Exception as e:
                self.log.error(
                    f"Error renewing oAuth token: {str(e)}. Trying later.",
                    exc_info=False,
                )
                ttl = 60
            time.sleep(ttl)

    def refresh_token(self):
        r = requests.get(
            f"{self.api_url}/users/{self.user}",
            headers={"Authorization": f"token {self.api_token}"},
        )

        if r.status_code != requests.codes.ok:
            raise Exception(f"Error accessing API: {r.status_code}")

        auth_state = r.json()["auth_state"]
        token = auth_state["access_token"]

        ttl = -1
        # Write the token in the corresponding file, by using the given content format
        with open(self.token_file, "w") as f:
            f.write(token)

            # renew one minute before expiration, but use the time of the token that will expire sooner
        token_decoded = jwt.decode(
            token, options={"verify_signature": False}, algorithms="RS256"
        )
        token_ttl = token_decoded["exp"] - time.time() - 60

        if ttl == -1 or token_ttl < ttl:
            ttl = token_ttl

        # If the token has already expired, something went wrong but we'll try again later
        if ttl < 60:
            ttl = 60

        return ttl


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the Jupyter server extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    log = logging.getLogger("tornado.renewtokens")
    log.name = "RenewTokens"
    log.setLevel(logging.INFO)
    log.propagate = True

    log.info("Loading Server Extension")

    try:
        thread = TokenRefresher(log)
        thread.start()
    except KeyError as e:
        log.warning(f"Error: Key {e} not defined")
    except Exception as e:
        log.warning(f"Error starting token refresh: {e}")
