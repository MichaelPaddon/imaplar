import logging
from .. import policy

class Policy(policy.Policy):
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
