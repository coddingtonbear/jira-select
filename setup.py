import os
from setuptools import setup

from jira_select import __version__ as version_string


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
    packages=["jira_select"],
    include_package_data=True,
    entry_points={
        "console_scripts": ["jira-select = jira_select.cmdline:main"],
        "jira_select_commands": [
            "configure = jira_select.commands.configure:Command",
            "store-password = jira_select.commands.store_password:Command",
            "build-query = jira_select.commands.build_query:Command",
            "run-query = jira_select.commands.run:Command",
        ],
    },
)
