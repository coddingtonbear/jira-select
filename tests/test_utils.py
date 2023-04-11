from __future__ import annotations

import copy
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

import simpleeval

from jira_select import query
from jira_select import utils
from jira_select.types import SelectFieldDefinition

from .base import JiraSelectTestCase


class TestParseSelectDefinition(JiraSelectTestCase):
    def test_returns_select_field_definition_directly(self):
        field_definition = SelectFieldDefinition.parse_obj(
            {
                "expression": "arbitrary",
                "column": "whatever",
            }
        )

        expected_result = copy.deepcopy(field_definition)
        actual_result = utils.parse_select_definition(field_definition)

        assert actual_result == expected_result

    def test_returns_name_if_no_as_expression(self):
        field_definition = "my_field_name"

        expected_result = SelectFieldDefinition.parse_obj(
            {
                "expression": field_definition,
                "column": field_definition,
            }
        )
        actual_result = utils.parse_select_definition(field_definition)

        assert expected_result == actual_result

    def test_returns_name_and_field_if_as_expression(self):
        field_definition = 'my_field_name as "My Field"'

        expected_result = SelectFieldDefinition.parse_obj(
            {
                "expression": "my_field_name",
                "column": "My Field",
            }
        )
        actual_result = utils.parse_select_definition(field_definition)

        assert expected_result == actual_result


class TestParseOrderByDefintition(JiraSelectTestCase):
    def test_handles_nonreversed(self):
        ordering = "somefield"

        expected_ordering = ordering, False
        actual_ordering = utils.parse_sort_by_definition(ordering)

        assert actual_ordering == expected_ordering

    def test_handles_reversed(self):
        ordering = "somefield desc"

        expected_ordering = "somefield", True
        actual_ordering = utils.parse_sort_by_definition(ordering)

        assert actual_ordering == expected_ordering

    def test_handles_reversed_casing(self):
        ordering = "somefield DESC"

        expected_ordering = "somefield", True
        actual_ordering = utils.parse_sort_by_definition(ordering)

        assert actual_ordering == expected_ordering

    def test_handles_nonreversed_casing(self):
        ordering = "somefield ASC"

        expected_ordering = "somefield", False
        actual_ordering = utils.parse_sort_by_definition(ordering)

        assert actual_ordering == expected_ordering


class TestCalculateResultHash(JiraSelectTestCase):
    def test_simple(self):
        issue = self.get_jira_issue()

        row = query.SingleResult(issue)
        assert isinstance(utils.calculate_result_hash(row, ["key"], {}), int)


class TestGetRowDict(JiraSelectTestCase):
    def test_copies_field_data(self):
        field_data = {
            "one": 1,
        }

        expected = {
            "key": ANY,
            "one": 1,
        }
        actual = utils.get_row_dict(self.get_jira_issue(field_data))

        assert actual == expected

    def test_copies_top_level_extra_keys(self):
        field_data = {
            "one": 1,
        }
        issue = self.get_jira_issue(field_data)
        issue.update(
            {
                "str_field": "ok",
                "float_field": 1.0,
                "int_field": 10,
                "list_field": [1, 2, 3],
                "dict_field": {"ok": True},
                "bool_field": False,
            }
        )

        expected = {
            "key": ANY,
            "str_field": "ok",
            "float_field": 1.0,
            "int_field": 10,
            "list_field": [1, 2, 3],
            "dict_field": {"ok": True},
            "bool_field": False,
            "one": 1,
        }
        actual = utils.get_row_dict(issue)

        assert actual == expected

    def test_does_not_copy_top_level_underscored(self):
        field_data = {
            "one": 1,
        }
        issue = self.get_jira_issue(field_data)
        issue.update({"_nope": 1})

        expected = {
            "key": ANY,
            "one": 1,
        }
        actual = utils.get_row_dict(issue)

        assert actual == expected


class TestEvaluateExpression(JiraSelectTestCase):
    def test_simple(self):
        expression = "my_field"
        names = {"my_field": "beep"}
        functions = {}

        expected_result = "beep"
        actual_result = utils.evaluate_expression(expression, names, functions)

        assert expected_result == actual_result

    def test_function(self):
        expression = "len(my_field)"
        names = {"my_field": "beep"}
        functions = {"len": len}

        expected_result = 4
        actual_result = utils.evaluate_expression(expression, names, functions)

        assert expected_result == actual_result

    def test_field_interpolations(self):
        arbitrary_interpolated_value = "boop"
        expression = "'{field name}'"
        names = {}
        interpolations = {"field name": arbitrary_interpolated_value}

        expected_result = arbitrary_interpolated_value
        actual_result = utils.evaluate_expression(
            expression, interpolations=interpolations, names=names
        )

        assert actual_result == expected_result


class TestGetFieldData(JiraSelectTestCase):
    def test_simple(self):
        mock_row = Mock(as_dict=Mock(return_value={"field": "OK"}))

        actual = utils.get_field_data(mock_row, "field")
        expected = "OK"

        assert actual == expected

    @patch("simpleeval.simple_eval")
    def test_none_for_dne(self, simple_eval):
        simple_eval.side_effect = simpleeval.AttributeDoesNotExist(None, None)

        mock_row = Mock(as_dict=Mock(return_value={"field": "OK"}))

        result = utils.get_field_data(mock_row, "arbitrary")
        assert result is None

    @patch("simpleeval.simple_eval")
    def test_none_for_keyerror(self, simple_eval):
        simple_eval.side_effect = KeyError()

        mock_row = Mock(as_dict=Mock(return_value={"field": "OK"}))

        result = utils.get_field_data(mock_row, "arbitrary")
        assert result is None

    @patch("simpleeval.simple_eval")
    def test_none_for_indexerror(self, simple_eval):
        simple_eval.side_effect = IndexError()

        mock_row = Mock(as_dict=Mock(return_value={"field": "OK"}))

        result = utils.get_field_data(mock_row, "arbitrary")
        assert result is None

    @patch("simpleeval.simple_eval")
    def test_none_for_typerror(self, simple_eval):
        simple_eval.side_effect = TypeError()

        mock_row = Mock(as_dict=Mock(return_value={"field": "OK"}))

        result = utils.get_field_data(mock_row, "arbitrary")
        assert result is None
