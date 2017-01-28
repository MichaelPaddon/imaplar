import smtplib
import socket
import ssl

class Null:
    def __init__(self, config, section):
        pass

    def send(self, message):
        pass

class Smtp(Null):
    def __init__(self, config, section):
        super().__init__(config, section)

        # smtp server configuration
        self._host = config.get(section, "host", fallback = "")
        self._port = config.getint(section, "port", fallback = 0)
        self._local_hostname = config.getboolean(section, "local_hostname",
            fallback = None) 
        self._timeout = config.getint(section, "timeout",
            fallback = socket._GLOBAL_DEFAULT_TIMEOUT)
        self._source_address = (
            config.get(section, "source_host", fallback = ""),
            config.getint(section, "source_port", fallback = 0))
        self._debug = config.getint(section, "debug", fallback = 0)

        # security configuration
        self._ssl = config.getboolean(section, "ssl", fallback = False)
        self._starttls = config.getboolean(section, "starttls", fallback = True)
        self._keyfile = config.get(section, "keyfile", fallback = None)
        self._certfile = config.get(section, "keyfile", fallback = None)
        if self._ssl or self._starttls:
            self._context = ssl.create_default_context(
                cafile = config.get(section, "ssl_cafile", fallback = None),
                capath = config.get(section, "ssl_capath", fallback = None),
                cadata = config.get(section, "ssl_cadata", fallback = None))
            self._context.check_hostname = config.getboolean(section,
                "ssl_check_hostname", fallback = True)
            if config.getboolean(section, "ssl_cert_required", fallback = True):
                self._context.verify_mode = ssl.CERT_REQUIRED
            else:
                self._context.verify_mode = ssl.CERT_NONE

        # authentication configuration
        authenticate = config.get(section, "authenticate", fallback = None)
        if authenticate is None:
            self._authenticate = lambda client: None
            pass
        elif authenticate == "login":
            self._authenticate = lambda client: client.login(
                config.get(section, "login_username"),
                config.get(section, "login_password"))
        else:
            raise Exception("{}: unknown authentication".format(authenticate))

    def send(self, message):
        if self._ssl:
            client = smtplib.SMTP_SSL(self._host, self._port,
                self._local_hostname, self._keyfile, self._certfile,
                self._timeout, self._source_address, self._context)
        else:
            client = smtplib.SMTP(self._host, self._port,
                self._local_hostname, self._timeout, self._source_address)
            if self._starttls:
                client.starttls(self._keyfile, self._certfile, self._context)

        client.set_debuglevel(self._debug)
        self._authenticate(client)
        client.send_message(message)
        client.quit()
