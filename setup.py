import setuptools
import imaplar.version

setuptools.setup(
    name = "imaplar",
    version = imaplar.version.version,
    author = "Michael Paddon",
    author_email = "michael@paddon.org",
    description = "IMAP mailbox monitor",
    url = "https://github.com/MichaelPaddon/imaplar",
    license = "GPLv3",
    keywords = "imap",
    packages = setuptools.find_packages(),
    install_requires = [
        "imapclient",
        "tenacity"
    ],
    entry_points = {
        "console_scripts": ["imaplar=imaplar.shell:main"]
    }
)
