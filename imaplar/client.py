#
# Copyright (C) 2017-2022 Michael Paddon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import collections.abc
import dataclasses
import enum
import imapclient
import imaplib
import logging
import ssl
import tenacity
import time

class ConnectionError(Exception):
    pass

class TLSMode(enum.Enum):
    DISABLED = 0
    ENABLED = 1
    STARTTLS = 2

@dataclasses.dataclass
class LoginAuthenticator:
    username: str
    password: str

    def __call__(self, client):
        return client.login(self.username, self.password)

@dataclasses.dataclass
class OAuth2Authenticator:
    user: str
    access_token: str
    mech: str = "XOAUTH2"
    vendor: str = None

    def __call__(self, client):
        return client.oauth2_login(self.user, self.access_token,
            self.mech, self.vendor)

@dataclasses.dataclass
class PlainAuthenticator:
    identity: str
    password: str
    authorization_identity: str = None

    def __call__(self, client):
        return client.plain_login(self.identity, self.password,
            self.authorization_identity)

@dataclasses.dataclass
class Session:
    host: str
    port: int = 993
    tls_mode: TLSMode = TLSMode.ENABLED
    ssl_context: ssl.SSLContext = None
    authenticator: collections.abc.Callable = None
    poll: float = 60
    idle: float = 900
    mailbox: str = "inbox"
    policy: collections.abc.Callable = None
    parameters: collections.abc.Mapping = None

    @tenacity.retry(
        before = tenacity.before_log(logging.getLogger(), logging.DEBUG))
    def run_forever(self, min = 1, max = 300):
        """Repeatedly connect to the server and monitor for unseen mail.

        Exponentially backoff on retries unless the connection was
        aborted by the server. In that case, the backoff is reset to the
        minimum value.

        :param min: minimum backoff in seconds
        :type min: int
        :param max: maxiumum backoff in seconds
        :type max: int
        """

        try:
            logger = logging.getLogger()
            backoff = tenacity.Retrying(
                retry = tenacity.retry_unless_exception_type(
                    imaplib.IMAP4.abort),
                wait = tenacity.wait_exponential(min = min, max = max),
                before = tenacity.before_log(logger, logging.DEBUG))
            backoff(self.run)
        except:
            logging.exception("session aborted")
            raise

    def run(self):
        """Connect to the server and monitor for unseen mail."""

        # connect to IMAP server
        client = imapclient.IMAPClient(self.host,
            port = self.port, 
            ssl = self.tls_mode == TLSMode.ENABLED, 
            ssl_context = self.ssl_context) 

        with client:
            # start TLS?
            if self.tls_mode == TLSMode.STARTTLS:
                client.starttls(self.ssl_context)

            # perform authentication
            if self.authenticator:
                self.authenticator(client)

            # choose wait mechanism
            has_idle = b"IDLE" in client.capabilities()
            wait = self._wait_idle if has_idle else self._wait_poll

            # process unseen messages
            client.select_folder(self.mailbox, readonly = True)
            messages = client.search(["UNSEEN"])
            for message in messages:
                self._process(client, message)

            # process incoming messages
            next_message = max(messages) + 1 if messages else 1
            while True:
                client.select_folder(self.mailbox, readonly = True)
                wait(client)
                messages = client.search(
                    ["{}:*".format(next_message), "UNSEEN"])
                for message in messages:
                    self._process(client, message)
                if messages:
                    next_message = max(messages) + 1

    def _process(self, client, message):
        if self.policy:
            namespace = {
                "client": client,
                "mailbox": self.mailbox,
                "message": message,
                "parameters": dict(self.parameters) if self.parameters else {}
            }

            logging.info("processing {}({})/{}/{}".format(
                self.host, self.port, self.mailbox, message))
            try:
                exec(self.policy, namespace)
            except Exception as e:
                logging.exception("policy exception")

    def _wait_poll(self, client):
        while True:
            response = client.noop()
            logging.debug("waiting: noop: {}".format(response))
            if response:
                if any([x for x in response[1] if x[1] == b"EXISTS"]):
                    return
            else:
                raise ConnectionError("connection dropped")

            time.sleep(self.poll)

    def _wait_idle(self, client):
        now = time.time()
        alarm = now + self.idle
        client.idle()
        while True:
            response = client.idle_check(alarm - now)
            logging.debug("waiting: idle_check: {}".format(response))
            if response:
                if any([x for x in response if x[1] == b"EXISTS"]):
                    client.idle_done()
                    return
            else:
                raise ConnectionError("connection dropped")

            now = time.time()
            if now >= alarm:
                alarm = now + self.idle
                client.idle_done()
                client.idle()
