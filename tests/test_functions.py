from __future__ import annotations

import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytz

from jira_select.functions.flatten_changelog import ChangelogEntry
from jira_select.functions.sprint_details import SprintInfo
from jira_select.plugin import get_installed_functions

from .base import JiraSelectTestCase


class JiraSelectFunctionTestCase(JiraSelectTestCase):
    def execute_function(self, name, *args, jira=None, **kwargs):
        if jira is None:
            jira = Mock()

        functions = get_installed_functions(jira)

        return functions[name](*args, **kwargs)


class TestSprintName(JiraSelectFunctionTestCase):
    def test_basic(self):
        sprint_string = "com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=MySprint,goal=Beep Boop,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436]"

        actual = self.execute_function("sprint_name", sprint_string)
        expected = "MySprint"

        assert expected == actual


class TestSprintDetails(JiraSelectFunctionTestCase):
    def test_basic(self):
        sprint_string = "com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=MySprint,goal=Beep Boop,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436]"

        expected = SprintInfo(
            id=436,
            rapidViewId=153,
            state="CLOSED",
            name="MySprint",
            goal="Beep Boop",
            startDate=datetime.datetime(2020, 3, 9, 21, 53, 7, 264000, tzinfo=pytz.UTC),
            endDate=datetime.datetime(2020, 3, 23, 20, 53, tzinfo=pytz.UTC),
            completeDate=datetime.datetime(
                2020, 3, 23, 21, 8, 29, 391000, tzinfo=pytz.UTC
            ),
            sequence=436,
        )
        actual = self.execute_function("sprint_details", sprint_string)

        assert expected == actual

    def test_extra_fields(self):
        sprint_string = "com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=MySprint,goal=Beep Boop,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436,someUnexpectedField=UhOh]"

        expected = SprintInfo(
            id=436,
            rapidViewId=153,
            state="CLOSED",
            name="MySprint",
            goal="Beep Boop",
            startDate=datetime.datetime(2020, 3, 9, 21, 53, 7, 264000, tzinfo=pytz.UTC),
            endDate=datetime.datetime(2020, 3, 23, 20, 53, tzinfo=pytz.UTC),
            completeDate=datetime.datetime(
                2020, 3, 23, 21, 8, 29, 391000, tzinfo=pytz.UTC
            ),
            sequence=436,
        )
        actual = self.execute_function("sprint_details", sprint_string)

        assert expected == actual

    def test_missing_fields(self):
        sprint_string = "com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[]"

        actual = self.execute_function("sprint_details", sprint_string)

        assert isinstance(actual, SprintInfo)


class TestGetSprint(JiraSelectFunctionTestCase):
    def test_basic(self):
        arbitrary_sprint_id = 10
        arbitrary_sprint_object = Mock(raw={})

        mock_jira = Mock(
            sprint=Mock(return_value=arbitrary_sprint_object),
            _options={"agile_rest_path": "/"},
        )

        self.execute_function("get_sprint_by_id", arbitrary_sprint_id, jira=mock_jira)

        assert mock_jira.sprint.called_with(arbitrary_sprint_id)


class TestFieldByName(JiraSelectFunctionTestCase):
    def test_basic(self):
        arbitrary_field_name = "customfield10000"
        arbitrary_human_name = "Sprint Name"
        arbitrary_value = "Beep Boop"

        mock_jira = Mock(
            fields=Mock(
                return_value=[
                    {"name": arbitrary_human_name, "key": arbitrary_field_name}
                ]
            )
        )

        my_row = SimpleNamespace(**{arbitrary_field_name: arbitrary_value})

        actual = self.execute_function(
            "field_by_name", my_row, arbitrary_human_name, jira=mock_jira
        )
        expected = arbitrary_value

        assert expected == actual


class TestEstimateToDays(JiraSelectFunctionTestCase):
    def test_basic(self):
        string_value = "1d 2h 3m"

        expected_value = 1.25625
        actual_value = self.execute_function("estimate_to_days", string_value)

        assert expected_value == actual_value

    def test_alternate_hour_day(self):
        string_value = "1d 2h 3m"

        expected_value = 1.5125
        actual_value = self.execute_function(
            "estimate_to_days", string_value, day_hour_count=4
        )

        assert expected_value == actual_value


class TestFlattenChangelog(JiraSelectFunctionTestCase):
    def test_basic(self):
        changelog = SimpleNamespace(
            histories=[
                SimpleNamespace(
                    **{
                        "author": "me@adamcoddington.net",
                        "created": "2015-11-01T18:16:37.388+0000",
                        "id": "10500",
                        "items": [
                            SimpleNamespace(
                                **{
                                    "field": "description",
                                    "fieldtype": "jira",
                                    "from": None,
                                    "fromString": None,
                                    "to": None,
                                    "toString": "Testing ticket body.",
                                }
                            )
                        ],
                    }
                ),
                SimpleNamespace(
                    **{
                        "author": "me@adamcoddington.net",
                        "created": "2015-10-11T07:39:40.063+0000",
                        "id": "10403",
                        "items": [
                            SimpleNamespace(
                                **{
                                    "field": "status",
                                    "fieldtype": "jira",
                                    "from": "10000",
                                    "fromString": "To Do",
                                    "to": "10001",
                                    "toString": "Done",
                                }
                            ),
                            SimpleNamespace(
                                **{
                                    "field": "resolution",
                                    "fieldtype": "jira",
                                    "from": None,
                                    "fromString": None,
                                    "to": "1",
                                    "toString": "Fixed",
                                }
                            ),
                        ],
                    }
                ),
            ]
        )

        expected_results = [
            ChangelogEntry(
                author="me@adamcoddington.net",
                created=datetime.datetime(
                    2015, 11, 1, 18, 16, 37, 388000, tzinfo=pytz.UTC
                ),
                id=10500,
                field="description",
                fieldtype="jira",
                fromValue=None,
                fromString=None,
                toValue=None,
                toString="Testing ticket body.",
            ),
            ChangelogEntry(
                author="me@adamcoddington.net",
                created=datetime.datetime(
                    2015, 10, 11, 7, 39, 40, 63000, tzinfo=pytz.UTC
                ),
                id=10403,
                field="status",
                fieldtype="jira",
                fromValue="10000",
                fromString="To Do",
                toValue="10001",
                toString="Done",
            ),
            ChangelogEntry(
                author="me@adamcoddington.net",
                created=datetime.datetime(
                    2015, 10, 11, 7, 39, 40, 63000, tzinfo=pytz.UTC
                ),
                id=10403,
                field="resolution",
                fieldtype="jira",
                fromValue=None,
                fromString=None,
                toValue="1",
                toString="Fixed",
            ),
        ]
        actual_results = self.execute_function("flatten_changelog", changelog)

        assert expected_results == actual_results


class TestSimpleFilter(JiraSelectFunctionTestCase):
    def test_basic(self):
        rows = [
            {
                "value": 10,
            },
            {
                "value": 20,
            },
        ]

        expected_results = [
            {
                "value": 10,
            }
        ]
        actual_results = self.execute_function("simple_filter", rows, value__lte=10)

        assert expected_results == actual_results

    def test_basic_multiple(self):
        rows = [{"value": 10, "name": "OK"}, {"value": 20, "name": "Nope"}]

        expected_results = [{"value": 10, "name": "OK"}]
        actual_results = self.execute_function(
            "simple_filter", rows, value__lte=99, name__eq="OK"
        )

        assert expected_results == actual_results


class TestSimpleFilterAny(JiraSelectFunctionTestCase):
    def test_basic(self):
        rows = [
            {
                "value": 10,
            },
            {
                "value": 20,
            },
        ]

        expected_results = [
            {
                "value": 10,
            }
        ]
        actual_results = self.execute_function("simple_filter_any", rows, value__lte=10)

        assert expected_results == actual_results

    def test_basic_multiple(self):
        rows = [{"value": 10, "name": "OK"}, {"value": 20, "name": "Nope"}]

        expected_results = [{"value": 10, "name": "OK"}, {"value": 20, "name": "Nope"}]
        actual_results = self.execute_function(
            "simple_filter_any", rows, value__lte=99, name__eq="OK"
        )

        assert expected_results == actual_results
