import datetime
from unittest.mock import Mock

from dotmap import DotMap
import pytz

from jira_select.plugin import get_installed_functions
from jira_select.functions.sprint_details import SprintInfo

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
        arbitrary_sprint_object = object()

        mock_jira = Mock(sprint=Mock(return_value=arbitrary_sprint_object))

        actual = self.execute_function(
            "get_sprint", arbitrary_sprint_id, jira=mock_jira
        )

        assert actual is arbitrary_sprint_object
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

        my_row = DotMap({arbitrary_field_name: arbitrary_value})

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
