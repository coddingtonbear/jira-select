from unittest.mock import Mock

from dotmap import DotMap

from jira_select.types import QueryDefinition
from jira_select.query import Query

from .base import JiraSelectTestCase


class JiraList(list):
    pass


class TestQuery(JiraSelectTestCase):
    def setUp(self):
        super().setUp()

        self.JIRA_ISSUES = JiraList(
            [
                DotMap(
                    {
                        "key": "ALPHA-1",
                        "fields": {
                            "issuetype": "Issue",
                            "summary": "My Ticket",
                            "project": "ALPHA",
                            "story_points": 1,
                        },
                    }
                ),
                DotMap(
                    {
                        "key": "ALPHA-3",
                        "fields": {
                            "issuetype": "Bug",
                            "summary": "Another Ticket",
                            "project": "ALPHA",
                            "story_points": 10,
                        },
                    }
                ),
                DotMap(
                    {
                        "key": "ALPHA-2",
                        "fields": {
                            "issuetype": "Issue",
                            "summary": "My Ticket #2",
                            "project": "ALPHA",
                            "story_points": 1,
                        },
                    }
                ),
            ]
        )
        self.JIRA_ISSUES.total = len(self.JIRA_ISSUES)

        self.mock_jira = Mock(search_issues=Mock(return_value=self.JIRA_ISSUES))

    def test_simple(self):
        query: QueryDefinition = {
            "select": ["key"],
            "from": "issues",
        }

        query = Query(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {"key": "ALPHA-1",},
            {"key": "ALPHA-3",},
            {"key": "ALPHA-2",},
        ]

        assert expected_results == actual_results

    def test_sort_by(self):
        query: QueryDefinition = {
            "select": ["key"],
            "from": "issues",
            "sort_by": ["story_points desc", "key"],
        }

        query = Query(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {"key": "ALPHA-3",},
            {"key": "ALPHA-1",},
            {"key": "ALPHA-2",},
        ]

        assert expected_results == actual_results

    def test_group_by_aggregation(self):
        query: QueryDefinition = {
            "select": ["issuetype", "len(key)"],
            "from": "issues",
            "group_by": ["issuetype"],
            "sort_by": ["len(key)"],
        }

        query = Query(self.mock_jira, query)

        actual_results = list(query)
        expected_results = [
            {"issuetype": "Bug", "len(key)": 1,},
            {"issuetype": "Issue", "len(key)": 2,},
        ]

        assert expected_results == actual_results
