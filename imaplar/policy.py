import email.parser
import itertools
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

    def envelope(self):
        if not self._envelope:
            self._client.select_folder(self._mailbox, readonly = True)
            response = self._client.fetch(self._msgid, "ENVELOPE")
            self._envelope = response[self._msgid][b"ENVELOPE"]
        return self._envelope

    def message(self):
        if not self._message:
            self._client.select_folder(self._mailbox, readonly = True)
            response = self._client.fetch(self._msgid, "BODY.PEEK[]")
            parser = email.parser.BytesParser()
            self._message = parser.parsebytes(response[self._msgid][b"BODY[]"])
        return self._message

    def froms(self):
        return self.addr_specs(self.envelope().from_)

    def senders(self):
        return self.addr_specs(self.envelope().sender)

    def reply_tos(self):
        return self.addr_specs(self.envelope().reply_to)

    def tos(self):
        return self.addr_specs(self.envelope().to)

    def ccs(self):
        return self.addr_specs(self.envelope().cc)

    def bccs(self):
        return self.addr_specs(self.envelope().bcc)

    def originators(self):
        return self.froms() | self.senders() | self.reply_tos()

    def recipients(self):
        return self.tos() | self.ccs() | self.bccs()

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

    @staticmethod
    def addr_specs(addresses):
        return set(b"%s@%s" % (a.mailbox, a.host)
                for a in addresses if a.mailbox and a.host)

class Policy:
    def __init__(self, config, section):
        self._config = config
        self._section = section

    @property
    def config(self):
        return self._config

    @property
    def section(self):
        return self._section

    def __call__(self, message):
        logging.info("processing message {}/{}".format(
                message.mailbox, message.msgid))
        self.process(message)
        logging.info("processing completed")

    def process(self, message):
        pass

    def recipient_query(self, strings):
        return self.header_query(
                ["To", "Cc", "Bcc", "Resent-To", "Resent-Cc", "Resent-Bcc"],
                strings)

    def originator_query(self, strings):
        return self.header_query(
                ["From", "Sender", "Reply-To"],
                strings)

    @staticmethod
    def header_query(fields, strings):
        terms = len(fields) * len(strings)
        query = ["OR"] * (terms - 1)
        query.extend(itertools.chain.from_iterable(
            [["HEADER", f, s] for f in fields for s in strings]))
        return query

class DefaultPolicy(Policy):
    def process(self, message):
        originators = message.originators()
        if originators:
            query = self.recipient_query(originators)
            if any(message.client.search_folders(query, ["Sent"])):
                logging.info("mail sent to an originator")
                return

            query = self.originator_query(originators)
            if any(message.client.search_folders(query, ["Spam"])):
                logging.info("spam received from an originator")
                logging.info("file into {}".format("Spam"))
                message.fileinto("Spam")
                return

            query = ["SEEN"] + self.originator_query(originators)
            if any(message.client.search_folders(query, ["Inbox"])):
                logging.info("ham received from an originator")
                return

        logging.info("unknown originator(s)")
        logging.info("file into {}".format("Spam"))
        message.fileinto("Spam")
