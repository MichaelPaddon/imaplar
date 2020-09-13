"""
This module provides convenience classes and methods to help
make writing policies easier.
"""

import email.utils
import functools
import imapclient
import itertools

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
    """A list of IMAP search criteria, which may be passed to
    imapclient.IMAPClient.search().
    """

    pass

class OrQuery(Query):
    """A query built from OR'd together sub-queries.

    :param queries: sub-queries
    :type queries: iterable of lists
    """

    def __init__(self, queries):
        super().__init__()
        try:
            queries = iter(queries)
            self.extend(functools.reduce(
                lambda x, y: ["OR", x, y], queries, next(queries)))
        except StopIteration:
            pass

class ToQuery(OrQuery):
    """A query for "To" addresses.

    :param addresses: match any of these addresses
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["TO", e] for e in emails)

class CcQuery(OrQuery):
    """A query for "Cc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["CC", e] for e in emails)

class BccQuery(OrQuery):
    """A query for "Bcc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["BCC", e] for e in emails)

class FromQuery(OrQuery):
    """A query for "From" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["FROM", e] for e in emails)

class SenderQuery(OrQuery):
    """A query for "Sender" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["HEADER", "Sender", e] for e in emails)

class ReplyToQuery(OrQuery):
    """A query for "Reply-To" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        emails = [email.utils.parseaddr(str(a))[1] for a in addresses] 
        super().__init__(["HEADER", "Reply-To", e] for e in emails)

class OriginatorQuery(OrQuery):
    """A query for "From", "Sender" and "Reply-To" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__([
            FromQuery(addresses),
            SenderQuery(addresses),
            ReplyToQuery(addresses)])

class RecipientQuery(OrQuery):
    """A query for "To", "Cc" and "Bcc" addresses.

    :param addresses: match any of these addresses 
    :type addresses: iterable of imapclient.response_types.Address objects
    """

    def __init__(self, addresses):
        super().__init__([
            ToQuery(addresses),
            CcQuery(addresses),
            BccQuery(addresses)])

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

def search_mailbox(client, mailbox, query):
    """Search a mailbox.

    :param client: imap client
    :param mailbox: mailbox name
    :param query: search criteria
    :type client: imapclient.IMAPClient
    :type mailbox: string
    :type query: list of query terms
    :return: message ids
    :rtype: list
    """

    client.select_folder(mailbox, readonly = True)
    return client.search(query)
