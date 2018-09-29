"""
Configuration
=============


"""

import imapclient
import importlib
import logging
import ssl
import tenacity
import time
from . import policy

class ConfigurationError(Exception):
    pass

class SSLContext(ssl.SSLContext):
    def __init__(self, verify_mode, check_hostname, cafile, capath, cadata):
        super().__init__(ssl.PROTOCOL_TLS)
        self.verify_mode = verify_mode
        self.check_hostname = check_hostname
        if cafile or capath or cadata:
            self.load_verify_locations(cafile, capath, cadata)
        self.load_default_certs(ssl.Purpose.SERVER_AUTH)

    @classmethod
    def configure(cls, config, section): 
        """Configure SSL Context"""
        cert_required = config.getboolean(section, "ssl_cert_required",
                fallback = True)
        check_hostname = config.getboolean(section, "ssl_check_hostname",
                fallback = True)
        cafile = config.get(section, "ssl_cafile", fallback = None)
        capath = config.get(section, "ssl_capath", fallback = None)
        cadata = config.get(section, "ssl_cadata", fallback = None)
        return cls(ssl.CERT_REQUIRED if cert_required else ssl.CERT_NONE,
                check_hostname, cafile, capath, cadata)

class IMAPClient(imapclient.IMAPClient):
    def glob_folder(self, pattern):
        if "*" in pattern or "%" in pattern:
            for flags, delimiter, name in self.list_folders(
                    pattern = pattern):
                yield name
            else:
                yield pattern

    def search_folders(self, folders, query):
        for folder in folders:
            self.select_folder(folder, readonly = True)
            for msgid in self.search(query):
                yield folder, msgid

    def wait_poll(self, poll):
        while True:
            logging.info("poll for new messages")
            response = self.noop()
            if response:
                if any([x for x in response[1] if x[1] == b"EXISTS"]):
                    return response[1]
            else:
                raise imapclient.IMAPClientAbortError("connection dropped")
            logging.info("sleep for {} seconds".format(poll))
            time.sleep(poll)

    def wait_idle(self):
        self.idle()
        while True:
            logging.info("idle for new messages")
            response = self.idle_check()
            if response:
                if any([x for x in response if x[1] == b"EXISTS"]):
                    self.idle_done()
                    return response[1:]
            else:
                raise imapclient.IMAPClientAbortError("connection dropped")

class IMAPClientFactory:
    def __init__(self, host, **kwargs):
        self._host = host
        self._kwargs = kwargs

    def new(self):
        logging.debug("connect to {} ({})".format(self._host, self._kwargs))
        return IMAPClient(self._host, **self._kwargs)

    @classmethod
    def configure(cls, config, section):
        host = config.get(section, "host", fallback = "localhost")
        port = config.getint(section, "port", fallback = None)
        ssl = config.getboolean(section, "ssl", fallback = False)
        ssl_context = SSLContext.configure(config, section) if ssl else None
        stream = config.getboolean(section, "stream", fallback = False)
        timeout = config.getint(section, "timeout", fallback = None)
        return cls(host, port = port, ssl = ssl, ssl_context = ssl_context,
                stream = stream, timeout = timeout)

class Authenticator:
    @classmethod
    def configure(cls, config, section):
        authentication = config.get(section, "authentication", fallback = None)
        if authentication is None:
            return None
        for subclass in cls.__subclasses__():
            if subclass.authentication == authentication:
                return subclass.configure(config, section)
        raise ConfigurationError(
                "{}: unknown authentication type '{}'".format(
                    section, authentication))

class LoginAuthenticator(Authenticator):
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def authenticate(self, client):
        logging.debug("login {}".format(self._username))
        return client.login(self._username, self._password)

    authentication = "login"

    @classmethod
    def configure(cls, config, section):
        username = config.get(section, "login_username")
        password = config.get(section, "login_password")
        return cls(username, password)

class OAuth2Authenticator(Authenticator):
    def __init__(self, user, access_token, mech, vendor):
        self._user = user
        self._access_token = access_token
        self._mech = mech
        self._vendor = vendor

    def authenticate(self, client):
        logging.debug("oauth2 login {}".format(self._user))
        return client.oauth2_login(self._user, self._access_token,
                self._mech, self._vendor)

    authentication = "oauth2"

    @classmethod
    def configure(cls, config, section):
        user = config.get(section, "oauth2_user")
        access_token = config.get(section, "oauth2_access_token")
        mech = config.get(section, "oauth2_mech", fallback = "XOAUTH2")
        vendor = config.get(section, "oauth2_vendor", fallback = None)
        return cls(url, user, access_token, mech, vendor)

class Session:
    def __init__(self, clientfactory, starttls, authenticator,
            mailbox, query, poll, policy):
        self._clientfactory = clientfactory
        self._starttls = starttls
        self._authenticator = authenticator
        self._mailbox = mailbox
        self._query = query
        self._poll = poll
        self._policy = policy

    @tenacity.retry(
            wait = tenacity.wait_exponential(max = 120)
                    + tenacity.wait_random(5),
            after = tenacity.after_log(logging.getLogger(), logging.ERROR))
    def retry(self):
        try:
            self.run()
        except:
            logging.exception("session aborted")
            raise

    def run(self):
        # connect to serve
        client = self._clientfactory.new()

        # start TLS?
        if self._starttls:
            logging.debug("start TLS")
            client.starttls(self._starttls)

        # perform authentication
        if self._authenticator:
            self._authenticator.authenticate(client)

        # choose wait mechanism
        wait = client.wait_idle\
            if self._poll <= 0\
            else lambda: client.wait_poll(self._poll)

        # process initial query messages
        client.select_folder(self._mailbox, readonly = True)
        msgids = client.search(self._query)
        self._process(client, self._mailbox, msgids)

        # process incoming messages
        nextid = msgids[-1] + 1 if msgids else 1
        while True:
            client.select_folder(self._mailbox, readonly = True)
            wait()
            logging.debug("new messages arrived")
            msgids = client.search("{}:* UNSEEN".format(nextid))
            self._process(client, self._mailbox, msgids)
            nextid = msgids[-1] + 1 if msgids else nextid

    def _process(self, client, mailbox, msgids):
        for msgid in msgids:
            self._policy(policy.Message(client, mailbox, msgid))

    @classmethod
    def configure(cls, config, section):
        clientfactory = IMAPClientFactory.configure(config, section)
        starttls = SSLContext.configure(config, section)\
                if config.getboolean(section, "starttls", fallback = False)\
                else None
        authenticator = Authenticator.configure(config, section)

        mailboxes = config.get(section, "mailboxes", fallback = "inbox").split()
        for subsection in mailboxes:
            mailbox = config.get(subsection, "mailbox", fallback = subsection)
            query = config.get(subsection, "query", fallback = "UNSEEN")
            poll = config.getfloat(subsection, "poll", fallback = 0)
            policy = config.get(subsection, "policy",
                    fallback = "imaplar.policy.Policy")

            policy_module_name, _, policy_class_name = policy.rpartition(".")
            policy_module = importlib.import_module(policy_module_name)
            policy_class = getattr(policy_module, policy_class_name)
            policy_callable = policy_class(config)

            yield cls(clientfactory, starttls, authenticator,
                    mailbox, query, poll, policy_callable)
