Imaplar
*******

*Imaplar* [#f1]_ monitors one or more mailboxes on one or more IMAP servers.
Unseen messages are passed to a user defined policy for processing.

*Imaplar* is intended for the automated processing of incoming mail.
Use cases include anti-spam measures and automated redirection.
The tool operates in two phases:

1. Startup. Each mailbox is examined for unseen messages.
   Each unseen message is processed by the mailbox's policy.

2. Ongoing. Each mailbox is monitored for new unseen messages.
   When they arrive, they are processed by the policy.

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

Installation
============

Imaplar is `released on PyPI <https://pypi.org/project/imaplar/>`_,
so all you need to do is:

.. code-block:: shell-session

   $ pip3 install imaplar

Configuration
=============

*Imaplar* is configured by a `YAML <https://yaml.org>`_ file, 
by default the ``~/.imaplar`` file.
This can be overridden on the command line.

.. caution::
   The configuration file contains authentication secrets
   and code which will be executed.
   It should be readable and writable only by its owner.

The configuration file defines a dictionary with the following members:

``servers`` [dictionary, required]
  A dictionary mapping IMAP server hostnames to server configurations.

``policies`` [dictionary, required]
  A dictionary mapping policy names to python scripts.

``logging`` [dictionary, optional]
  A dictionary specifying logging configuration.
  If present, it is passed to the
  `python logging configuration mechanism
  <https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema>`_.

Server Configuration
--------------------

Each server has an associated configuration dictionary with the
following members:

``default`` [boolean, default = False]
  A server flagged as default will be monitored if
  no servers a specified on the command line.

``port`` [integer, default = 993 if TLS is enabled, otherwise 143]
  The IMAP server port.

``tls`` [dictionary, optional]
  TLS configuration.

``authentication`` [dictionary, optional]
  Authentication configuration.

``poll`` [integer, default = 60]
  Server polling interval in seconds.
  Only used when IDLE is not supported by the server.

``idle`` [integer, default = 900]
  Server idling interval in seconds.
  Only used when IDLE is supported by the server.

``mailboxes`` [dictionary, required]
  A mapping of mailbox names to policy names.
  Each mailbox will be monitored, with messages passed to the specified policy.

``parameters`` [dictionary, optional]
  Per-server parameters that will be passed to the policy.

TLS Configuration
#################

A TLS configuration  dictionary has the following members:

``mode`` [string, default = "enabled"]
  The TLS mode. This may be "enabled", "disabled" or "starttls".

``verify_mode`` [string, default = "required"]
  Certificate verification mode. This may be "none", "optional" or "required".
  Set this to "optional" or "none" if you are using a self signed certificate.

``check_hostname`` [boolean, default = true]
  Validate that the server name matches the certificate.
  Set this to false if there is a mismatch (such as connecting to localhost).

``cafile`` [string, optional]
  The path to a file containing
  `concatenated PEM certificates
  <https://docs.python.org/3/library/ssl.html#ssl-certificates>`_.
  If defined, the system default certificate store is ignored.

``capath`` [string, optional]
  The path to a directory containing PEM certifcates as per the
  `OpenSSL layout
  <https://www.openssl.org/docs/man1.1.1/man3/SSL_CTX_load_verify_locations.html>`_.
  If defined, the system default certificate store is ignored.

``cadata`` [string, optional]
  A string containing
  `concatenated PEM certificates
  <https://docs.python.org/3/library/ssl.html#ssl-certificates>`_.
  If defined, the system default certificate store is ignored.

Authentication Configuration
############################

An authetication configuration dictionary has the following members:

``method`` [string, required]
  The authentication method to use.
  Must be one of "login", "plain" or "oauth2".

``login_username`` [string, required when method is "login"]
  The login username.

``login_password`` [string, required when method is "login"]
  The login password.

``plain_identity`` [string, required when method is "plain"]
  The plain identity.

``plain_password`` [string, required when method is "plain"]
  The plain password.

``plain_authorization_identity`` [string, optional when method is "plain"]
  The plain authorization identity.

``oauth2_user`` [string, required when method is "oauth2"]
  The oauth2 user.

``oauth2_access_token`` [string, required when method is "oauth2"]
  The oauth2 access token.

``oauth2_mech`` [string, default = "XOAUTH2" when method is "oauth2"]
  The oauth2 mechanism.

``oauth2_vendor`` [string, optional when method is "oauth2"]
  The oauth2 vendor.

Example Configuration
---------------------

A simple example configuration file looks like this:

.. code-block:: YAML

  ---
  servers:
    mail.example.com:
      authentication:
        method: login
        username: myname
        password: mypassword
      mailboxes:
        inbox: mypolicy

  policies:
    mypolicy: |
      # this policy just logs a message
      import logging
      logging.info("Handled {}/{}".format(mailbox, message))

Systemd User Service (Optional)
-------------------------------

If you are running Systemd, you may configure a user service in order to run
*imaplar* automatically.

1. Create the file ``~/.config/systemd/imaplar.server``:

   .. code-block:: INI

     [Unit]
     Description = Imaplar IMAP monitoring service

     [Service]
     ExecStart = <path-to-imap-command>
     Restart = always

     [Install]
     WantedBy = default.target

2. Enable and start the service with these shell commands:

   .. code-block:: shell-session

     $ systemctl --user enable imaplar
     $ systemctl --user start imaplar

3. If you want the service to keep running when you are logged out, run the following command as root:

   .. code-block:: shell-session

     # loginctl enable-linger <your-username>

Writing Policies
================

Each policy is a python script. The following global variables are provided:

* **client**: an instance of `imapclient.IMAPClient
  <https://imapclient.readthedocs.io/en/2.1.0/api.html>`_,
  connected to the server
* **mailbox**: the name of the monitored mailbox
* **message**: the message id
* **parameters**: parameters specified in the server configuration

.. note::
   A policy script should *not* assume that the currently selected
   mailbox (if any) is the monitored mailbox.

The imaplar.policy module
-------------------------

.. automodule:: imaplar.policy
   :members:
   :member-order: bysource
   :special-members:
   :exclude-members: __init__, __weakref__
   :show-inheritance:

.. rubric:: Footnotes
.. [#f1] The `Lares (singular Lar) <https://en.wikipedia.org/wiki/Lares>`_
   were ancient Roman guardian deities.

.. toctree::
   :hidden:

   index
