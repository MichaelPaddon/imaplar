import collections.abc
import dataclasses
import enum
import imapclient
import logging
import ssl
import tenacity
import time
from . import policy

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
            wait = tenacity.wait_exponential(max = 300),
            after = tenacity.after_log(logging.getLogger(), logging.ERROR))
    def run_forever(self):
        try:
            self.run()
        except:
            logging.exception("session aborted")
            raise

    def run(self):
        client = imapclient.IMAPClient(self.host,
            port = self.port, 
            ssl = self.tls_mode == TLSMode.ENABLED, 
            ssl_context = self.ssl_context) 

        # start TLS?
        if self.tls_mode == TLSMode.STARTTLS:
            client.starttls(self.ssl_context)

        # perform authentication
        if self.authenticator:
            self.authenticator(client)

        # server capabilities
        capabilities = client.capabilities()
        has_idle = b"IDLE" in capabilities
        has_move = b"MOVE" in capabilities

        # choose wait mechanism
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
            messages = client.search(["{}:*", "UNSEEN"].format(next_message))
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
                "parameters": dict(self.parameters) if self.parameters else {},
                "policy": policy
            }
            exec(self.policy, namespace)

    def _wait_poll(self, client):
        while True:
            response = client.noop()
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
            if response:
                if any([x for x in response if x[1] == b"EXISTS"]):
                    client.idle_done()
                    return

            now = time.time()
            if now >= alarm:
                alarm = now + self.idle
                client.idle_done()
                client.idle()
