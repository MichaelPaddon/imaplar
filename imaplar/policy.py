#
# Copyright (C) 2017-2020 Michael Paddon
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

"""
This module provides convenience classes and methods to help
make writing policies easier.
"""

import email.utils
import functools
import itertools
import logging

class Originators(set):
    """Envelope originator addresses.

    :param envelope: message envelope
    :type envelope: imapclient.response_types.Envelope
    """

    def __init__(self, envelope):
        super().__init__(itertools.chain(
            envelope.from_, envelope.sender, envelope.reply_to))

class Recipients(set):
    """Envelope recipient addresses.

    :param envelope: message envelope
    :type envelope: imapclient.response_types.Envelope
    """

    def __init__(self, envelope):
        super().__init__(itertools.chain(
            envelope.to, envelope.cc, envelope.bcc))

class Query(list):
    """A list of IMAP search criteria.

    :param criteria: search criteria
    :type criteria: iterable of strings
    """

    def __call__(self, client, *mailboxes):
        """Generate message ids by executing query.

        :param client: imap client
        :param mailboxes: mailbox names
        :type client: imapclient.IMAPClient
        :type mailboxes: strings
        :return: message ids
        :rtype: generator of ints
        """

        for mailbox in mailboxes:
            client.select_folder(mailbox, readonly = True)
            logging.debug("query {}".format(str(self)))
            yield from client.search(self)

    def __and__(self, query):
        """AND queries together.

        :param query: other query
        :type query: Query
        :return: a new query
        :rtype: Query
        """

        return Query([self, query])

    def __or__(self, query):
        """OR queries together.

        :param query: other query
        :type query: Query
        :return: a new query
        :rtype: Query
        """

        return Query(["OR", self, query])

    def __not__(self):
        """NOT this query.

        :return: a new query
        :rtype: Query
        """

        return Query(["NOT", query])

class ToQuery(Query):
    """A query for "To" addresses.

    :param addresses: match any of these addresses
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["TO", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class CcQuery(Query):
    """A query for "Cc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["CC", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class BccQuery(Query):
    """A query for "Bcc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["BCC", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class FromQuery(Query):
    """A query for "From" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["FROM", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class SenderQuery(Query):
    """A query for "Sender" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["HEADER", "Sender", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class ReplyToQuery(Query):
    """A query for "Reply-To" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(functools.reduce(lambda x, y: x | y,
            (Query(["HEADER", "Reply-To", email.utils.parseaddr(str(a))[1]])
                for a in addresses)))

class OriginatorQuery(Query):
    """A query for "From", "Sender" and "Reply-To" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(FromQuery(addresses)
            | SenderQuery(addresses)
            | ReplyToQuery(addresses))

class RecipientQuery(Query):
    """A query for "To", "Cc" and "Bcc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__(ToQuery(addresses)
            | CcQuery(addresses)
            | BccQuery(addresses))

def fetch_envelope(client, mailbox, message):
    """Fetch the envelope of a message.

    :param client: imap client
    :param mailbox: mailbox name
    :param message: message id
    :type client: imapclient.IMAPClient
    :type mailbox: string
    :type message: int
    :return: an envelope
    :rtype: imapclient.response_types.Envelope
    """

    client.select_folder(mailbox, readonly = True)
    response = client.fetch([message], ["ENVELOPE"])
    return response[message][b"ENVELOPE"]

def move_message(client, mailbox, message, to_mailbox):
    """Move a message to a different mailbox.

    Uses the IMAP MOVE capability if available, otherwise it copies the
    message to the destination and then deletes the original.

    :param client: imap client
    :param mailbox: source mailbox name
    :param message: message id
    :param to_mailbox: destination mailbox name
    :type client: imapclient.IMAPClient
    :type mailbox: string
    :type message: int
    :type to_mailbox: string
    """

    if mailbox == to_mailbox:
        return

    client.select_folder(mailbox)
    if b"MOVE" in client.capabilities():
        client.move([message], to_mailbox)
    else:
        client.copy([message], to_mailbox)
        client.delete_messages([message])
    client.close_folder()
