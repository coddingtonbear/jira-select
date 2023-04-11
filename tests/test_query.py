from __future__ import annotations

import uuid
from unittest.mock import Mock

import pytest
from dotmap import DotMap
from jira import Issue
from jira.resources import Resource

from jira_select.exceptions import ExpressionParameterMissing
from jira_select.query import Executor
from jira_select.types import QueryDefinition

from .base import JiraSelectTestCase


class JiraList(list):
    pass


class MyResource(Resource):
    def __init__(self, raw):
        super().__init__(None, None, None)
        self.raw = raw


class NonResource:
    def __str__(self):
        return "<NonResource>"


class TestQuery(JiraSelectTestCase):
    def setUp(self):
        super().setUp()

        self.JIRA_ISSUES = [
            {
                "key": "ALPHA-1",
                "fields": {
                    "issuetype": "Issue",
                    "summary": "My Ticket",
                    "project": "ALPHA",
                    "story_points": 1,
                    "customfield10010": 50,
                    "customfield10011": "Ivanovna",
                    "customfield10012": MyResource({"ok": "yes"}),
                    "customfield10013": NonResource(),
                    "worklogs": DotMap(
                        {"total": 1, "worklogs": [{"timespentSeconds": 60}]}
                    ),
                    "transactions": DotMap(
                        {"byCurrency": {"usd": 100, "cad": 105, "cop": 200}}
                    ),
                },
            },
            {
                "key": "ALPHA-3",
                "fields": {
                    "issuetype": "Bug",
                    "summary": "Another Ticket",
                    "project": "ALPHA",
                    "story_points": 10,
                    "customfield10010": 55,
                    "customfield10011": "Jackson",
                    "customfield10012": MyResource({"ok": "no"}),
                    "customfield10013": NonResource(),
                    "worklogs": DotMap(
                        {
                            "total": 2,
                            "worklogs": [
                                {"timespentSeconds": 30},
                                {"timespentSeconds": 15},
                            ],
                        }
                    ),
                    "transactions": DotMap({"byCurrency": {"cad": 124, "cop": 843}}),
                },
            },
            {
                "key": "ALPHA-2",
                "fields": {
                    "issuetype": "Issue",
                    "summary": "My Ticket #2",
                    "project": "ALPHA",
                    "story_points": 1,
                    "customfield10010": 56,
                    "customfield10011": "Chartreuse",
                    "customfield10012": MyResource({"ok": "maybe"}),
                    "customfield10013": NonResource(),
                    "transactions": DotMap({"byCurrency": {"usd": 10, "rur": 33}}),
                },
            },
        ]
        issues = JiraList([Issue(None, None, issue) for issue in self.JIRA_ISSUES])
        issues.total = len(self.JIRA_ISSUES)

        self.mock_jira = Mock(
            search_issues=Mock(return_value=issues), fields=Mock(return_value=[])
        )

    def test_simple(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
            }
        )

        query = Executor(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {
                "key": "ALPHA-1",
            },
            {
                "key": "ALPHA-3",
            },
            {
                "key": "ALPHA-2",
            },
        ]

        assert expected_results == actual_results

    def test_sort_by(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
                "sort_by": ["story_points desc", "key"],
            }
        )

        query = Executor(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {
                "key": "ALPHA-3",
            },
            {
                "key": "ALPHA-1",
            },
            {
                "key": "ALPHA-2",
            },
        ]

        assert expected_results == actual_results

    def test_filter(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
                "filter": ["summary != 'My Ticket #2'"],
            }
        )

        query = Executor(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {
                "key": "ALPHA-1",
            },
            {
                "key": "ALPHA-3",
            },
        ]

        assert expected_results == actual_results

    def test_group_by_aggregation(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["issuetype", "len(key)"],
                "from": "issues",
                "group_by": ["issuetype"],
                "sort_by": ["len(key)"],
            }
        )

        query = Executor(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {
                "issuetype": "Bug",
                "len(key)": 1,
            },
            {
                "issuetype": "Issue",
                "len(key)": 2,
            },
        ]

        assert expected_results == actual_results

    def test_cap(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
                "cap": 1,
            }
        )

        query = Executor(self.mock_jira, query)

        actual_results = list(query)
        assert len(actual_results) == 1

    def test_simple_wprogress(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
            }
        )

        query = Executor(self.mock_jira, query, True)

        actual_results = list(query)
        expected_results = [
            {
                "key": "ALPHA-1",
            },
            {
                "key": "ALPHA-3",
            },
            {
                "key": "ALPHA-2",
            },
        ]

        assert expected_results == actual_results

    def test_field_name_map(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ["key"],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Story Points", "id": "customfield10010"},
                {"name": "Sprint", "id": "customfield10011"},
            ]
        )
        query = Executor(self.mock_jira, arbitrary_query, True)

        expected_result = {
            "Story Points": "customfield10010",
            "Sprint": "customfield10011",
            "params": DotMap(),
        }
        actual_result = query.field_name_map

        assert expected_result == actual_result

    def test_interpolated_value_nonspecial(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ['{customfield10011} as "mn"'],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Maiden Name", "id": "customfield10011"},
            ]
        )

        query = Executor(self.mock_jira, arbitrary_query, True)

        actual_results = list(query)
        expected_results = [
            {"mn": "Ivanovna"},
            {"mn": "Jackson"},
            {"mn": "Chartreuse"},
        ]

        assert expected_results == actual_results

    def test_interpolated_value_nonstring(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ['{Jellybean Guess} as "jb"'],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Jellybean Guess", "id": "customfield10010"},
            ]
        )

        query = Executor(self.mock_jira, arbitrary_query, True)

        actual_results = list(query)
        expected_results = [
            {"jb": 50},
            {"jb": 55},
            {"jb": 56},
        ]

        assert expected_results == actual_results

    def test_interpolated_value_string(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ['{Maiden Name} as "mn"'],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Maiden Name", "id": "customfield10011"},
            ]
        )

        query = Executor(self.mock_jira, arbitrary_query, True)

        actual_results = list(query)
        expected_results = [
            {"mn": "Ivanovna"},
            {"mn": "Jackson"},
            {"mn": "Chartreuse"},
        ]

        assert expected_results == actual_results

    def test_interpolated_value_resource(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ['{Result Object}.ok as "ro"'],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Result Object", "id": "customfield10012"},
            ]
        )

        query = Executor(self.mock_jira, arbitrary_query, True)

        actual_results = list(query)
        expected_results = [
            {"ro": "yes"},
            {"ro": "no"},
            {"ro": "maybe"},
        ]

        assert expected_results == actual_results

    def test_interpolated_value_nonresource(self):
        arbitrary_query = QueryDefinition.parse_obj(
            {
                "select": ['{Beep Boop} as "bb"'],
                "from": "issues",
            }
        )
        self.mock_jira.fields = Mock(
            return_value=[
                {"name": "Beep Boop", "id": "customfield10013"},
            ]
        )

        query = Executor(self.mock_jira, arbitrary_query, True)

        actual_results = list(query)
        for result in actual_results:
            assert isinstance(result["bb"], NonResource)

    def test_autoextract_sum(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ['sum(transactions.byCurrency.usd) as "value"'],
                "from": "issues",
                "group_by": ["True"],
            }
        )
        query = Executor(self.mock_jira, query)

        actual_results = list(query)[0]["value"]
        expected_results = 110

        assert expected_results == actual_results

    def test_autoextract_internal_array(self):
        query = QueryDefinition.parse_obj(
            {
                "select": [
                    'sum(extract(flatten_list(worklogs.worklogs), "timespentSeconds")) as "value"'
                ],
                "from": "issues",
                "group_by": ["True"],
            }
        )
        query = Executor(self.mock_jira, query)

        actual_results = list(query)[0]["value"]
        expected_results = 105

        assert expected_results == actual_results

    def test_param_expression_specified(self):
        arbitrary_value = str(uuid.uuid4())

        query = QueryDefinition.parse_obj(
            {
                "select": ["'{params.ok}' as \"value\""],
                "from": "issues",
                "cap": 1,
            }
        )

        query = Executor(self.mock_jira, query, parameters={"ok": arbitrary_value})
        results = list(query)

        assert results[0]["value"] == arbitrary_value

    def test_param_expression_unspecified_select(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["'{params.ok}'"],
                "from": "issues",
                "cap": 1,
            }
        )

        query = Executor(self.mock_jira, query)

        with pytest.raises(ExpressionParameterMissing):
            list(query)

    def test_param_expression_unspecified_where(self):
        query = QueryDefinition.parse_obj(
            {
                "select": ["True"],
                "from": "issues",
                "where": [
                    "'{params.ok}'",
                ],
                "cap": 1,
            }
        )

        query = Executor(self.mock_jira, query)

        with pytest.raises(ExpressionParameterMissing):
            list(query)

    def test_param_jql_specified(self):
        arbitrary_value = str(uuid.uuid4())

        query = QueryDefinition.parse_obj(
            {
                "select": ["'{params.ok}' as \"value\""],
                "from": "issues",
                "where": [
                    '"{params.ok}"',
                ],
                "cap": 1,
            }
        )

        query = list(
            Executor(self.mock_jira, query, parameters={"ok": arbitrary_value})
        )

        args, _ = self.mock_jira.search_issues.call_args

        assert arbitrary_value in args[0]
