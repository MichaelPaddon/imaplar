import email.parser
import functools
import imaplib
import logging

class Message:
    def __init__(self, client, mailbox, msgid):
        self._client = client
        self._mailbox = mailbox
        self._msgid = msgid
        self._envelope = None
        self._message = None

    @property
    def client(self):
        return self._client

    @property
    def mailbox(self):
        return self._mailbox

    @property
    def msgid(self):
        return self._msgid

    @property
    def envelope(self):
        if not self._envelope:
            self._client.select_folder(self._mailbox, readonly = True)
            response = self._client.fetch(self._msgid, "ENVELOPE")
            self._envelope = response[self._msgid][b"ENVELOPE"]
        return self._envelope

    @property
    def message(self):
        if not self._message:
            self._client.select_folder(self._mailbox, readonly = True)
            response = self._client.fetch(self._msgid, "BODY.PEEK[]")
            parser = email.parser.BytesParser()
            self._message = parser.parsebytes(response[self._msgid][b"BODY[]"])
        return self._message

    @property
    def from_addrs(self):
        return self._addrs(self.envelope.from_)

    @property
    def sender_addrs(self):
        return self._addrs(self.envelope.sender)

    @property
    def reply_to_addrs(self):
        return self._addrs(self.envelope.reply_to)

    @property
    def to_addrs(self):
        return self._addrs(self.envelope.to)

    @property
    def cc_addrs(self):
        return self._addrs(self.envelope.cc)

    @property
    def bcc_addrs(self):
        return self._addrs(self.envelope.bcc)

    @property
    def originators(self):
        return self.from_addrs | self.sender_addrs | self.reply_to_addrs

    @property
    def recipients(self):
        return self.to_addrs | self.cc_addrs | bcc_addrs

    def fileinto(self, mailbox):
        try:
            self._client.select_folder(mailbox, readonly = True)
        except imapclient.IMAPClientError:
            logging.info("creating mailbox {}".format(mailbox))
            self._client.create_folder(mailbox)

        self._client.select_folder(self._mailbox)
        if self._client.has_capability("MOVE"):
            logging.info("move message {} to {}".format(self._msgid, mailbox))
            self._client.move([self._msgid], mailbox)
        else:
            logging.info("copy message {} to {}".format(self._msgid, mailbox))
            self._client.copy([self._msgid], mailbox)
            logging.info("delete message {} from {}".format(
                    self._msgid, self._mailbox))
            self._client.delete_messages([self._msgid])
        self._client.close_folder()

    def _addrs(self, addresses):
        return set("{}@{}".format(a.mailbox.decode(), a.host.decode())
                for a in addresses if a.mailbox and a.host)

class Query(list):
    def __init__(self, *args):
        super().__init__(args)

    def and_(self, other):
        return Query(self, other)

    def or_(self, other):
        return Query("OR", self, other)

class MultiHeaderQuery(Query):
    def __init__(self, headers, strings):
        queries = [Query("HEADER", h, s) for h in headers for s in strings]
        super().__init__(functools.reduce(lambda x, y: x.or_(y), queries))

class Policy:
    def __call__(self, message):
        logging.info("processing message {}".format(message.msgid))

        folders = ["Sent"]
        query = MultiHeaderQuery(
                ["To", "Cc", "Bcc", "Resent-To", "Resent-Cc", "Resent-Bcc"],
                message.originators)
        if any(message.client.search_folders(folders, query)):
            logging.info("found sent to originator".format(message.msgid))
            return

        folders = ["Spam"]
        query = MultiHeaderQuery(
                ["From", "Sender", "Reply-To"],
                message.originators)
        if any(message.client.search_folders(folders, query)):
            logging.info("found spam from originator".format(message.msgid))
            message.fileinto("Spam")
            return

        folders = ["Inbox"]
        query = Query("SEEN").and_(MultiHeaderQuery(
                ["From", "Sender", "Reply-To"],
                message.originators))
        if any(message.client.search_folders(folders, query)):
            logging.info("found ham from originator".format(message.msgid))
            return

        message.fileinto("Spam")
        return

default = Policy()
