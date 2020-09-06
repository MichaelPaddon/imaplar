import os.path
import setuptools

directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name = "imaplar",
    version = "0.7.1",
    author = "Michael Paddon",
    author_email = "michael@paddon.org",
    description = "IMAP mailbox monitor",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    classifiers = [
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Communications :: Email'
    ],
    url = "https://github.com/MichaelPaddon/imaplar",
    license = "GPLv3+",
    keywords = "imap",
    packages = setuptools.find_namespace_packages(include = ["imaplar"]),
    python_requires = ">=3.7",
    install_requires = [
        "Cerberus",
        "PyYaml",
        "imapclient",
        "importlib-metadata; python_version < '3.8'",
        "tenacity"
    ],
    entry_points = {
        "console_scripts": ["imaplar=imaplar.shell:main"]
    }
)
