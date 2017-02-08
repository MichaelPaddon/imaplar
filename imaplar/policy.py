import datetime
import email.policy
import email.utils
import imapclient
import itertools
import logging
import os
import quopri
from . import policy
from . import util

class Null:
    def __init__(self, config, section):
        pass

    def __call__(self, imapclient, folder, uid):
        logging.debug("{}/{}: policy null".format(folder, uid))

class Zuul(Null):
    """There is no spam, there is only Zuul."""

    def __init__(self, config, section):
        super().__init__(config, section)

        self._sent_folders = config.get(section, "sent_folders",
            fallback = "Sent").split()
        self._ham_folders = config.get(section, "ham_folders",
            fallback = "INBOX").split()
        self._spam_folders = config.get(section, "spam_folders",
            fallback = "Junk").split()
        self._my_addresses = config.get(section, "my_addresses",
            fallback = "").split()
        self._challenge_ttl = config.getint(section, "challenge_ttl",
            fallback = 7)
        self._challenge_message = config.get(section, "challenge_message",
            fallback = None)

        self._mailer = util.plugin(config,
            config.get(section, "mailer", fallback = "mailer"),
            policy.Null)

    def __call__(self, client, folder, uid):
        # get message header
        logging.debug("{}/{}: policy zuul".format(folder, uid))
        client.select_folder(folder, readonly = True)
        message = client.fetch_headers(uid)[uid]

        # get return path
        return_path = email.utils.parseaddr(
            str(message.get("Return-Path", "")))[1]
        if not return_path:
            logging.warning("{}/{}: no return path".format(folder, uid))
            return

        # glob folders
        sent_folders = client.glob_folders(self._sent_folders)
        ham_folders = client.glob_folders(self._ham_folders)
        spam_folders = client.glob_folders(self._spam_folders)

        # multi folder search
        isdistinct = lambda x, y: x != folder and y != uid
        def search(criteria, folders, iswanted = isdistinct):
            for folder in folders:
                client.select_folder(folder, True)
                for uid in client.search(criteria):
                    if iswanted(folder, uid):
                        yield (folder, uid)

        # challenge response?
        in_reply_to = email.utils.parseaddr(
            str(message.get("In-Reply-To", "")))[1]
        if in_reply_to and any(search([
                "HEADER", "Message-Id", in_reply_to], sent_folders)):
            logging.debug("{}/{}: challenge response from {}".format(
                folder, uid, return_path))
            ham_folder = ham_folders[0]
            for spam_folder in spam_folders:
                client.select_folder(spam_folder, True)
                for ham_uid in client.search([
                        "HEADER", "Return-Path", return_path]):
                    logging.info("{}/{}: moving to {}".format(
                        spam_folder, ham_uid, ham_folder))
                    client.move(ham_uid, ham_folder)
                client.expunge()
            return
        # have we sent mail to the return path?
        elif any(search([
                "NOT", "HEADER", "Auto-Submitted", "challenge",
                "OR", "HEADER", "To", return_path,
                "OR", "HEADER", "Cc", return_path,
                "OR", "HEADER", "Bcc", return_path,
                "OR", "HEADER", "Resent-To", return_path,
                "OR", "HEADER", "Resent-Cc", return_path,
                "HEADER", "Resent-Bcc", return_path], sent_folders)):
            logging.debug("{}/{}: mail previously sent to {}".format(
                folder, uid, return_path))
            return
        # have we received spam from the return path?
        elif any(search([
                "SEEN", "HEADER", "Return-Path", return_path], spam_folders)):
            logging.debug("{}/{}: spam previously received from {}".format(
                folder, uid, return_path))
            pass
        # have we received ham from the return path?
        elif any(search([
                "SEEN", "HEADER", "Return-Path", return_path], ham_folders)):
            logging.debug("{}/{}: ham previously received from {}".format(
                folder, uid, return_path))
            return
        else:
            logging.debug("{}/{}: nothing ever received from {}".format(
                folder, uid, return_path))

        def challenge():
            # don't challenge auto submitted email
            auto_submitted = email.utils.parseaddr(
                str(message.get("Auto-Submitted", "no")))[1].lower()
            if auto_submitted != "no":
                logging.info("{}/{}: autosubmitted, no challenge".format(
                    folder, uid))
                return

            # don't challenge email lists
            if any([key.lower().startswith("List-") for key in message.keys()]):
                logging.info("{}/{}: list headers present, no challenge".format(
                    folder, uid))
                return

            # don't challenge low precedence email
            precedences = {precedence.lower()
                for _, precedence in email.utils.getaddresses(
                    str(message.get_all("Precedence", [])))}
            if precedences & set(["bulk", "junk", "list"]):
                logging.info("{}/{}: low precedence, no challenge".format(
                    folder, uid))
                return

            # don't challenge email not addressed to me
            recipients = {address for _, address in email.utils.getaddresses(
                itertools.chain.from_iterable([
                    str(message.get_all("To", [])),
                    str(message.get_all("Cc", [])),
                    str(message.get_all("Bcc", [])),
                    str(message.get_all("Resent-To", [])),
                    str(message.get_all("Resent-Cc", [])),
                    str(message.get_all("Resent-Bcc", []))]))}
            if not recipients & set(self._my_addresses):
                logging.info("{}/{}: not addressed to me, no challenge".format(
                    folder, uid))
                return

            # don't challenge recently challenged originator
            since = datetime.date.today()\
                - datetime.timedelta(self._challenge_ttl)
            if any(search([
                    "SINCE", since,
                    "HEADER", "Auto-Submitted", "challenge",
                    "HEADER", "To", return_path], sent_folders)):
                logging.debug("{}/{}: recently challenged, no challenge".format(
                    folder, uid))
                return

            # construct challenge
            challenge = email.message.Message(policy = email.policy.SMTP)
            challenge["To"] = return_path
            challenge["From"] = self._my_addresses[0]
            challenge["Date"] = email.utils.format_datetime(
                email.utils.localtime())
            challenge["Subject"] = "Re: {}".format(
                "".join(str(message.get("Subject", "")).splitlines()))
            challenge["Auto-Submitted"] = "auto-replied; challenge"
            challenge["Message-Id"] = email.utils.make_msgid(
                os.urandom(8).hex())
            references = []
            if "References" in message:
                references.append(message["References"])
            if "Message-ID" in message:
                challenge["In-Reply-To"] = message["Message-Id"]
                references.append(message["Message-Id"])
            if references:
                challenge["References"] = " ".join(references)
            challenge["Content-Transfer-Encoding"] = "quoted-printable"
            challenge.set_payload(
                quopri.encodestring(self._challenge_message.encode()), "utf-8")

            # work around bug in email encoding
            try:
                challenge.as_bytes()
            except:
                challenge.replace_header("Subject", "Re:")

            # send challenge
            logging.debug("{}/{}: sending challenge".format(folder, uid))
            self._mailer.send(challenge)

            # save challenge
            logging.debug("{}/{}: saving challenge".format(folder, uid))
            client.append(sent_folders[0], challenge.as_bytes(),
                [imapclient.SEEN])

        # send challenge
        challenge()

        # quarantine message
        spam_folder = spam_folders[0]
        logging.info("{}/{}: moving to {}".format(folder, uid, spam_folder))
        client.select_folder(folder)
        client.move(uid, spam_folder)
        client.expunge()
