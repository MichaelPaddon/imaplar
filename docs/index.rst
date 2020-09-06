Imaplar
*******

*Imaplar* [#f1]_ monitors one or more mailboxes on one or more IMAP servers.
Unseen and incoming messages are passed to a user defined policy for
processing.

.. toctree::
  :caption: Table of Contents:

Synopsis
========
**imaplar**
[**--config** *path*]
[*server...*]

**--config** *path*
  Read the specified configuration file.

*server*
  IMAP server to monitor. If no servers are specified, then servers
  marked as default in the configuration will be monitored.

Configuration
=============

*Imaplar* is configured by a `YAML <https://yaml.org>`_ file, 
by default ``~/.imaplar``.
This can be overridden on the command line.

.. note::
   You must supply a configuration for *imaplar* to do anything useful.

.. caution::
   The configuration file contains authentication secrets
   and code which will be executed.
   It should be readable and writable only by its owner.

Server Configuration
--------------------

The ``servers`` directory defines how to connect to and monitor
an IMAP server. Defaults are shown as literal values::

  servers:                                 -- server configurations [required]
    <hostname>:                            -- IMAP server host name [required]
      default: False                       -- flagged as a default server
      port: 993                            -- port number (143 if TLS not enabled)
      tls:                                 -- TLS configuration [optional]
        mode: enabled                      -- TLS mode: "disabled", "enabled", "starttls"
        verify_mode: required              -- verify certificate: "none", "optional", "required"
        check_hostname: True               -- validate server name
        cafile: <file>                     -- file of PEM certificates [optional]
        capath: <directory>                -- directory of PEM certificates [optional]
        cadata: <cadata>                   -- literal PEM certificates [optional]
      authentication:                      -- authentication configuration [optional]
        method: <method>                   -- auth method: "login", "plain", "oauth2" [required]
        login_username: <username>         -- login username
        login_password: <password>         -- login password
        plain_identity: <identity>         -- plain identity
        plain_password: <password>         -- plain password
        plain_authorization_identity: <x>  -- plain authorization identity [optional]
        oauth2_user: <user>                -- oauth2 user
        oauth2_access_token: <token>       -- oauth2 access token
        oauth2_mech: XOAUTH2               -- aouth2 mechanism ("XOAUTH2")
        oauth2_vendor: <vendor>            -- oauth2 vendor [optional]
      poll: 60                             -- mailbox polling period
      idle: 900                            -- mailbox idle period
      mailboxes:                           -- mailbox configurations [required]
        <mailbox>: <policy>                -- mailbox name mapped to policy name
      parameters:                          -- per-server policy parameters [optional]
        ...                                -- user defined parameters

.. note::
   A server is only actually monitored if it is named on the command line.

Policy Configuration
--------------------

The ``policies`` directory defines how messages are handled::

  policies:                           -- policy configurations [required]
    <policy>: |                       -- policy name
      <python script>                 -- policy implementation

On connecting to a server, the python script is executed
first for every existing unseen message, and subsequently for every
newly arrived unseen message in each monitored mailbox.

The following global variables are provided to the script:

* **client**: an instance of `imapclient.IMAPClient
  <https://imapclient.readthedocs.io/en/2.1.0/api.html>`_,
  connected to the server
* **mailbox**: the name of the monitored mailbox
* **message**: the message id
* **parameters**: server specific parameters (if any)

.. note::
   A policy script should *not* assume that the currently selected
   mailbox (if any) is the monitored mailbox.

Logging Configuration
---------------------

If a ``logging`` directory is present, it is passed to the `standard python logging configuration mechanism <https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema>`_.

Example
-------
A simple example configuration file looks like this::

  ---
  servers:
    mail.example.com:
      tls:
        mode: starttls
      authentication:
        method: login
        username: myname
        password: mypassword
      mailboxes:
        inbox: mypolicy

  policies:
    mypolicy: |
      # this is a python script
      pass

  logging:
    version: 1
    root:
      handlers: [stdout]
      level: INFO 
    handlers:
      stdout:
        class: logging.StreamHandler
        stream: ext://sys.stdout
        formatter: timestamp
    formatters:
      timestamp:
        format: "%(asctime)s %(levelname)s %(message)s"

Systemd User Service (Optional)
===============================

If you are running Systemd, you may configure a user service in order to run
*imaplar* automatically.

1. Create the file ``~/.config/systemd/imaplar.server``::

     [Unit]
     Description = Imaplar IMAP monitoring service

     [Service]
     ExecStart = <path-to-imap-command>
     Restart = always

     [Install]
     WantedBy = default.target

2. Enable and start the service::

     $ systemctl --user enable imaplar
     $ systemctl --user start imaplar

.. rubric:: Footnotes
.. [#f1] The `Lares (singular Lar) <https://en.wikipedia.org/wiki/Lares>`_
   were ancient Roman guardian deities.
