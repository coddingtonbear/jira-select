from unittest import TestCase
from unittest.mock import Mock
from typing import List, Dict, Optional, Any

from dotmap import DotMap

from jira_select.types import QueryDefinition
from jira_select.query import Executor


class JiraSelectTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self._issue_counter = 0

    def get_query(self, issues: List[Dict], query: QueryDefinition):
        return Executor(Mock(search_issues=Mock(return_value=issues)), query)

    def get_jira_issue(self, fields: Optional[Dict[str, Any]] = None):
        self._issue_counter += 1

        if fields is None:
            fields = {
                "int_field": 1,
                "bool_field": True,
                "list_field": [1, 2, 3],
                "dict_field": {"a": 1, "b": 2},
            }

        return DotMap({"key": f"ALPHA-{self._issue_counter}", "fields": fields})
