Imaplar
*******

*Imaplar* [#f1]_ monitors one or more mailboxes on one or more IMAP servers.
Unseen and incoming messages are passed to a user defined policy for
processing.

Synopsis
========
**imaplar**
[**--config** *path*]
*server...*

**--config** *path*
  Read the specified configuration file.

*server*
  IMAP server to monitor.

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
an IMAP server::

  servers:                            -- required server configuration
    <hostname>:                       -- IMAP server name
      port: <port>                    -- port number, default 143 (993 when TLS enabled)
      tls:                            -- optional TLS configuration
        mode: <mode>                  -- TLS operation ["disabled", "enabled" (default), "starttls"]
        verify_mode: <verify_mode>    -- cert verification ["none", "optional", "required" (default)]
        check_hostname: <boolean>     -- validate server name, default True
        cafile: <cafile>              -- file of concatenated PEM certificates
        capath: <capath>              -- directory containing PEM certificates
        cadata: <cadata>              -- concatenated PEM certificates
      authentication:                 -- optional authentication configuration
        method: login                 -- authentication type ["login", "plain", "oauth2"]
        username: <username>          -- required for "login"
        password: <password>          -- required for "login" or "plain"
        identity: <identity>          -- required for "plain"
        authorization_identity: <x>   -- optional for "plain"
        user: <user>                  -- required for "oauth2"
        access_token: <access_token>  -- required for "oauth2"
        mech: <mech>                  -- optional for "oauth2"
        vendor: <vendor>              -- optional for "oauth2"
      poll: <seconds>                 -- mailbox polling period
      mailboxes:                      -- required mailbox configuration
        <mailbox>: <policy>           -- mailbox to policy mapping

.. note::
   A server is only actually monitored if it is named on the command line.

Policy Configuration
--------------------

The ``policies`` directory defines how messages are handled::

  policies:                           -- required policies configuration
    <policy>: |                       -- policy name
      <python script>                 -- arbitrary code

On connecting to a server, the python script is executed
first for every existing unseen message, and subsequently for every
newly arrived unseen message in each monitored mailbox.

The following global variables are provided to the script:

* **client**: an instance of `imapclient.IMAPClient
  <https://imapclient.readthedocs.io/en/2.1.0/api.html>`_,
  connected to the server
* **mailbox**: the name of the monitored mailbox
* **msgid**: the id of the message to process

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
