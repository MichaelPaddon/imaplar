import logging
from .. import policy

class Policy(policy.Policy):
    def __init__(self, config, section):
        super().__init__(config, section)
        self._sent_mailboxes = config.get(section,
                "sent_mailboxes", fallback = "Sent").split()
        self._spam_mailboxes = config.get(section,
                "spam_mailboxes", fallback = "Spam").split()
        self._ham_mailboxes = config.get(section,
                "ham_mailboxes", fallback = "Inbox").split()

    def process(self, message):
        originators = message.originators()
        if originators:
            query = self.recipient_query(originators)
            if any(message.client.search_folders(query, self._sent_mailboxes)):
                logging.info("mail sent to an originator")
                return

            query = self.originator_query(originators)
            if any(message.client.search_folders(query, self._spam_mailboxes)):
                logging.info("spam received from an originator")
                logging.info("file into {}".format(self._spam_mailboxes[0]))
                message.fileinto(self._spam_mailboxes[0])
                return

            query = ["SEEN"] + self.originator_query(originators)
            if any(message.client.search_folders(query, self._ham_mailboxes)):
                logging.info("ham received from an originator")
                return

        logging.info("unknown originator(s)")
        if self._spam_mailboxes:
            logging.info("file into {}".format(self._spam_mailboxes[0]))
            message.fileinto(self._spam_mailboxes[0])
        else:
            logging.warn("no spam mailboxes defined")
