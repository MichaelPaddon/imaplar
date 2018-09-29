Imaplar
*******

*Imaplar* [#f1]_ monitors mailboxes on IMAP servers for incoming messages.
When a message arrives, it is passed to a user defined policy
which decides how it should be handled.

Synopsis
========
**imaplar**
[**--config** *path*]
[*server...*]

**--config** *path*
  Read the specified configuration file.
  This option may be specified multiple times,
  in which case the files are processed in order.

*server*
  Process the configuration section named *server*.
  By default, the section named "server" is processed.

Configuration
=============

*Imaplar* is configured by one or more files in the
`usual Python format <https://docs.python.org/3/library/configparser.html>`_.
By default, the following configuration files (if they exist)
are processed in order:

  1. ``~/.imaplar``
  2. ``~/.imaplar.cfg``
  3. ``.imaplar``
  4. ``.imaplar.cfg``

This may be overridden on the command line.

.. note::
   You must supply a configuration for *imaplar* to do anything useful.

Server Configuration
--------------------

Each monitored IMAP server requires a configuration section.
The basic options are:

========= ======= ========= ===========
Option    Type    Default   Description
========= ======= ========= ===========
host      string  localhost IMAP server name
port      integer 143       IMAP server port
ssl       boolean false     enable connecting over SSL
                            (changes default port to 993)
starttls  boolean false     enable STARTTLS after connecting
stream    boolean false     interpret *host* as a
                            command which connects its stdin/stdout
                            to the IMAP server
timeout   float             socket timeout, in seconds
mailboxes string  inbox     whitespace separated list of mailbox section names
========= ======= ========= ===========

.. note::
   Enabling SSL or STARTTLS is strongly recommended
   if your server supports it.

SSL Options
###########

If SSL or STARTTLS is enabled, certificate verification may be configured:

================== ======= ======= ===========
Option             Type    Default Description
================== ======= ======= ===========
ssl_cert_required  boolean true    require server's certificate to
                                   verify successfully
ssl_check_hostname boolean true    require the server's hostname to
                                   match its certificate
ssl_cafile         string          file containing CA certificates
                                   in PEM format
ssl_capath         string          directory containing CA certificates
                                   in PEM format
ssl_cadata         string          string containing CA certificates
                                   in PEM format
================== ======= ======= ===========

.. note::
   If you don't supply any CA certificates, *imaplar* will default to using
   the system default ones. This is sufficient for most cases.

Authentication
##############

Most servers require connections to be authenticated:

============== ====== ======= ===========
Option         Type   Default Description
============== ====== ======= ===========
authentication string         authentication method (*login* or *oauth2*)
============== ====== ======= ===========

Login authentication is configured with these options:

============== ====== ======= ===========
Option         Type   Default Description
============== ====== ======= ===========
login_username string         username
login_password string         password
============== ====== ======= ===========

OAUTH2 authentication is configured with these options:

=================== ====== ======= ===========
Option              Type   Default Description
=================== ====== ======= ===========
oauth2_user         string         user
oauth2_access_token string         access token
oauth2_mech         string XOAUTH2 mechanism
oauth2_vendor       string         vendor
=================== ====== ======= ===========

Mailbox Configuration
---------------------

Each server configuration specifies a list of mailbox sections,
one for each mailbox to be monitored.
The following options are supported in mailbox sections:

======= ====== ====================== ===========
Option  Type   Default                Description
======= ====== ====================== ===========
mailbox string *section name*         IMAP mailbox name
query   string UNSEEN                 IMAP search criteria to select messages
                                      to process on startup
                                      ("NOT ALL" disables startup processing)
poll    float  0                      polling interval in seconds
                                      (0 enables use of IMAP IDLE option)
policy  string imaplar.policy.default Python callable implementing user policy
======= ====== ====================== ===========

.. note::
   The default policy does nothing.

Logging Configuration
---------------------

Logging may be configured using the `standard python mechanism <https://docs.python.org/3/library/logging.config.html#logging-config-fileformat>`_.

Example
-------
A simple example configuration file looks like this::

  [server]
  host = imap.example.com
  starttls = true
  mailboxes = inbox

  [inbox]
  policy = user.policy

Logging to standard output may be enabled with additional sections::

  [loggers]
  keys = root

  [handlers]
  keys = stdout

  [formatters]
  keys = timestamp

  [logger_root]
  level = INFO
  handlers = stdout

  [handler_stdout]
  class = StreamHandler
  formatter = timestamp
  args = [sys.stdout]

  [formatter_timestamp]
  format = %(asctime)s %(levelname)s %(message)s

Policies
========

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. toctree::
   :maxdepth: 2

.. rubric:: Footnotes
.. [#f1] The `Lares (singular Lar) <https://en.wikipedia.org/wiki/Lares>`_ were ancient Roman guardian deities.
