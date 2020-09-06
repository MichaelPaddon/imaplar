import email.utils
import functools
import itertools

def fetch_envelope(client, message):
    response = client.fetch([message], ["ENVELOPE"])
    return response[message][b"ENVELOPE"]

class Originators(set):
    def __init__(self, envelope):
        super().__init__(itertools.chain(
            envelope.from_, envelope.sender, envelope.reply_to))

class Recipients(set):
    def __init__(self, envelope):
        super().__init__(itertools.chain(
            envelope.to, envelope.cc, envelope.bcc))

class OrQuery(list):
    def __init__(self, queries):
        super().__init__()
        try:
            queries = iter(queries)
            self.extend(functools.reduce(
                lambda x, y: ["OR", x, y], queries, next(queries)))
        except StopIteration:
            pass

class AddressQuery(OrQuery):
    def __init__(self, keys, addresses):
        addresses = list(filter(None,
            (email.utils.parseaddr(str(a))[1] for a in addresses)))
        super().__init__(k + [a] for k in keys for a in addresses)

class OriginatorAddressQuery(AddressQuery):
    def __init__(self, addresses):
        super().__init__(
            [["FROM"], ["HEADER", "Sender"], ["HEADER", "Reply-To"]], addresses)

class RecipientAddressQuery(AddressQuery):
    def __init__(self, addresses):
        super().__init__([["TO"], ["CC"], ["BCC"]], addresses)
