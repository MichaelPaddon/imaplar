import setuptools

setuptools.setup(
    name = "imaplar",
    version = "0.3",
    author = "Michael Paddon",
    author_email = "michael@paddon.org",
    description = "IMAP folder monitor",
    url = "https://github.com/MichaelPaddon/imaplar",
    license = "GPLv3",
    keywords = "imap",
    packages = setuptools.find_packages(),
    install_requires = [
        "imapclient"
    ],
    entry_points = {
        "console_scripts": ["imaplar=imaplar.cli:main"]
    }
)
