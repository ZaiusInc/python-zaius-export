# -*- coding: utf-8 -*-
"""Unit tests for SQL parser

This verifies the SQL parser accepts required input and produces
the data structure expected by the zaius export api.
"""

import unittest
import datetime

import parsy
from zaius.export.parser import QUERY_PARSER


class TestParser(unittest.TestCase):
    """Parser tests"""

    def test_queries_parse(self):
        # pylint: disable=C0330

        """Verify that valid queries parse and invalid queries
        do not parse"""

        # simplest valid query
        self.assert_valid(
            """
            select ts
            from events
        """
        )

        # field names can be nested
        self.assert_valid(
            """
            select customer.name
            from events
        """
        )

        # multiple fields are allowed
        self.assert_valid(
            """
            select user_id, customer.name
            from events
        """
        )

        # results can be ordered
        self.assert_valid(
            """
            select user_id
            from events
            order by ts
        """
        )

        # order can be controlled
        self.assert_valid(
            """
            select user_id
            from events
            order by ts desc
        """
        )

        # results can be filtered
        today_s = datetime.date.today().strftime("%s")
        self.assert_valid(
            """
            select user_id
            from events
            where ts > {}
        """.format(
                today_s
            )
        )

        # filters can be complex
        self.assert_valid(
            """
            select user_id
            from events
            where
                ts > {}
                and event_type = 'order'
                and action = 'purchase'
        """.format(
                today_s
            )
        )

        # invalid queries

        # fields must be explicit
        self.assert_invalid(
            """
            select *
            from events
        """
        )

        # only one table in the from clause
        self.assert_invalid(
            """
            select user_id
            from events, customers
        """
        )

        # query keywords can only appear once
        self.assert_invalid(
            """
            select user_id
            select customer.name
            from events
        """
        )

        # something must be selected
        self.assert_invalid(
            """
            select
            from events
        """
        )

    def test_parse_output(self):
        """Verify that the output of the parser represents the
        contents of the string that was parsed."""

        # sorts and filters only appear when used in the query
        result = self.assert_valid(
            """
            select user_id
            from events
        """
        )
        self.assertNotIn("sorts", result["select"])
        self.assertNotIn("filter", result["select"])

        result = self.assert_valid(
            """
            select user_id
            from events
            order by ts
        """
        )
        self.assertIn("sorts", result["select"])
        self.assertNotIn("filter", result["select"])

        result = self.assert_valid(
            """
            select user_id
            from events
            where ts > 0
        """
        )
        self.assertNotIn("sorts", result["select"])
        self.assertIn("filter", result["select"])

        # trivial filters work
        self.assert_match_like("ts > 0", [{"ts": 10}, {"ts": -10}], [True, False])

        # compound filters work
        self.assert_match_like(
            "ts > 0 and ts < 10",
            [{"ts": 0}, {"ts": 1}, {"ts": 9}, {"ts": 10}],
            [False, True, True, False],
        )

        self.assert_match_like(
            "ts > 0 and ts < 10 and color = 'blue'",
            [
                {"ts": 1, "color": "red"},
                {"ts": 3, "color": "blue"},
                {"ts": 5, "color": "blue"},
                {"ts": 10, "color": "blue"},
            ],
            [False, True, True, False],
        )

    # pylint: disable=R0201
    def assert_valid(self, stmt):
        """Ensure that a query is parseable"""

        return QUERY_PARSER.parse(stmt)

    def assert_invalid(self, stmt):
        """Ensure that a query is invalid"""

        with self.assertRaises(parsy.ParseError):
            QUERY_PARSER.parse(stmt)

    def assert_match_like(self, stmt, rows, target):
        """Ensure that rows match or do not match the filter
        defined by stmt according to target"""

        filter_fn = self._compile_statement(stmt)
        result = list(map(filter_fn, rows))
        self.assertEqual(result, target)

    def assert_match_all(self, stmt, rows):
        """Ensure that all rows match the filter defined by stmt"""

        return self.assert_match_like(stmt, rows, [True] * len(rows))

    def _compile_statement(self, stmt):
        parsed = self.assert_valid("select fake from fake where " + stmt)
        return self._compile_filter(parsed["select"]["filter"])

    # pylint: disable=R0201
    def _compile_filter(self, filter_struct):
        if "field" in filter_struct:
            return self._compile_filter_term(filter_struct)
        if "and" in filter_struct:
            parts = list([self._compile_filter(part) for part in filter_struct["and"]])
            return lambda row: all(map(lambda p: p(row), parts))
        if "or" in filter_struct:
            parts = list([self._compile_filter(part) for part in filter_struct["and"]])
            return lambda row: any(map(lambda p: p(row), parts))
        raise ValueError("cannot compile {}".format(filter_struct))

    def _compile_filter_term(self, filter_struct):
        field = filter_struct["field"]
        value = filter_struct["value"]

        return {
            "=": lambda row: row[field] == value,
            ">": lambda row: row[field] > value,
            ">=": lambda row: row[field] >= value,
            "<": lambda row: row[field] < value,
            "<=": lambda row: row[field] <= value,
            "!=": lambda row: row[field] != value,
        }[filter_struct["operator"]]
