import os
from setuptools import setup

from jira_csv import __version__ as version_string


requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt",)
requirements = []
with open(requirements_path, "r") as in_:
    requirements = [
        req.strip()
        for req in in_.readlines()
        if not req.startswith("-") and not req.startswith("#")
    ]


setup(
    name="jira-csv",
    version=version_string,
    url="https://github.com/coddingtonbear/jira-csv",
    description="Easily generate CSV exports of Jira issues",
    author="Adam Coddington",
    author_email="me@adamcoddington.net",
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    install_requires=requirements,
    packages=["jira_csv"],
    include_package_data=True,
    entry_points={
        "console_scripts": ["jira-csv = jira_csv.cmdline:main"],
        "jira_csv_commands": [
            "configure = jira_csv.commands.configure:Command",
            "store-password = jira_csv.commands.store_password:Command",
            "build-query = jira_csv.commands.build_query:Command",
            "run-query = jira_csv.commands.run:Command",
        ],
    },
)
