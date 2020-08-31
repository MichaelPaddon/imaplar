Imaplar
*******

*Imaplar* [#f1]_ monitors mailboxes on IMAP servers for incoming messages.
When a message arrives, it is passed to a user defined policy
which decides how it should be handled.

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

*Imaplar* is configured by a YAML file.
The default confguration file is ``~/.imaplar``.
This can be overridden on the command line.

.. note::
   You must supply a configuration for *imaplar* to do anything useful.

Server Configuration
--------------------

The ``servers`` directory defines how to connect to and monitor
an IMAP server::

  servers:                            -- required dictionary
    <hostname>:                       -- the IMAP server
      port: <port number>             -- default 143 (993 if TLS is enabled)
      tls:                            -- optional dictionary
        mode: <mode>                  -- "enabled" (default), "disabled" or "starttls"
      authentication:                 -- optional dictionary
        method: login                 -- "login", "plain" or "oauth2"
        username: <username>          -- required for "login"
        password: <password>          -- required for "login" or "plain"
        identity: <identity>          -- required for "plain"
        authorization_identity: <x>   -- optional for "plain"
        user: <user>                  -- required for "oauth2"
        access_token: <access_token>  -- required for "oauth2"
        mech: <mech>                  -- optional for "oauth2"
        vendor: <vendor>              -- optional for "oauth2"
      poll: <seconds>                 -- polling interval
      mailboxes:                      -- required
        <mailbox>: <policy>           -- mailbox to policy mapping

.. note::
   A server is only actually monitored if it is named on the command line.

Policy Configuration
--------------------

The ``policies`` directory defines how messages are handled::

  policies:                           -- required dictionary
    <policy>: |                       -- policy name
      <python script>                 -- arbitrary code

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
    
.. toctree::
   :maxdepth: 2

.. rubric:: Footnotes
.. [#f1] The `Lares (singular Lar) <https://en.wikipedia.org/wiki/Lares>`_ were ancient Roman guardian deities.
