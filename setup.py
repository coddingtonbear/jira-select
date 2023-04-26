#!/usr/bin/env python

import io
import os
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

requirements_path = os.path.join(
    os.path.dirname(__file__),
    "requirements.txt",
)
requirements = []
with open(requirements_path, "r") as in_:
    requirements = [
        req.strip()
        for req in in_.readlines()
        if not req.startswith("-") and not req.startswith("#")
    ]


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="jira-select",
    version="3.0.1",
    license="MIT",
    description=(
        "Easily run complex SQL-like queries far beyond what "
        "Jira's standard JQL query language can provide."
    ),
    long_description_content_type="text/markdown",
    long_description=read("readme.md"),
    author="Adam Coddington",
    author_email="me@adamcoddington.net",
    url="https://github.com/coddingtonbear/jira-select",
    packages=find_packages(),
    py_modules=[splitext(basename(path))[0] for path in glob("jira-select/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/coddingtonbear/jira-select/issues",
    },
    keywords=[
        "jira",
        "csv",
        "sql",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    extras_require={},
    entry_points={
        "console_scripts": ["jira-select = jira_select.cmdline:main"],
        "jira_select.commands": [
            "configure = jira_select.commands.configure:Command",
            "store-password = jira_select.commands.store_password:Command",
            "build-query = jira_select.commands.build_query:Command",
            "run-query = jira_select.commands.run:Command",
            "schema = jira_select.commands.schema:Command",
            "functions = jira_select.commands.functions:Command",
            "shell = jira_select.commands.shell:Command",
            "run-script = jira_select.commands.run_script:Command",
            "show-instances = jira_select.commands.show_instances:Command",
            "setup-instance = jira_select.commands.setup_instance:Command",
            "remove-instance = jira_select.commands.remove_instance:Command",
            "install-user-script = jira_select.commands.install_user_script:Command",
        ],
        "jira_select.formatters": [
            "csv = jira_select.formatters.csv:Formatter",
            "tsv = jira_select.formatters.tsv:Formatter",
            "html = jira_select.formatters.html:Formatter",
            "json = jira_select.formatters.json:Formatter",
            "table = jira_select.formatters.table:Formatter",
            "raw = jira_select.formatters.raw:Formatter",
        ],
        "jira_select.functions": [
            "sprint_details = jira_select.functions.sprint_details:Function",
            "sprint_name = jira_select.functions.sprint_name:Function",
            "get_sprint_by_id = jira_select.functions.get_sprint_by_id:Function",
            "get_sprint_by_name = jira_select.functions.get_sprint_by_name:Function",
            "field_by_name = jira_select.functions.field_by_name:Function",
            "estimate_to_days = jira_select.functions.estimate_to_days:Function",
            "extract = jira_select.functions.extract:Function",
            "flatten_list = jira_select.functions.flatten_list:Function",
            "flatten_changelog = jira_select.functions.flatten_changelog:Function",
            "simple_filter = jira_select.functions.simple_filter:Function",
            "simple_filter_any = jira_select.functions.simple_filter_any:Function",
            "parse_datetime = jira_select.functions.parse_datetime:Function",
            "parse_date = jira_select.functions.parse_date:Function",
            "json_dumps = jira_select.functions.json_dumps:Function",
            "get_issue = jira_select.functions.get_issue:Function",
            "workdays_in_state = jira_select.functions.workdays_in_state:Function",
            "get_issue_snapshot_on_date = jira_select.functions.get_issue_snapshot_on_date:Function",
            "interval_business_hours = jira_select.functions.interval_business_hours:Function",
            "interval_matching = jira_select.functions.interval_matching:Function",
            "interval_size = jira_select.functions.interval_size:Function",
            "subquery = jira_select.functions.subquery:Function",
            "union = jira_select.functions.union:Function",
        ],
        "jira_select.sources": [
            "issues = jira_select.sources.issues:Source",
            "boards = jira_select.sources.boards:Source",
            "sprints = jira_select.sources.sprints:Source",
        ],
    },
)
