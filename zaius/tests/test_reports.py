# -*- coding: utf-8 -*-
"""Unit tests for Reports

This pokes helper methods found on reports to make sure they work
as expected.
"""

import unittest
import datetime

from zaius.reports.lifecycle_progress import LifecycleProgress

# pylint: disable=W0212
class TestReports(unittest.TestCase):
    """Report tests"""

    def test_lifecycle_progress(self):
        """Verify helpers for lifecycle progress report"""

        report = LifecycleProgress()
        jan2018 = datetime.date(2018, 1, 1)
        jan2019 = datetime.date(2019, 1, 1)
        feb2019 = datetime.date(2019, 2, 1)

        self.assertEqual(report._parse_month("2018-1"), jan2018)
        self.assertEqual(report._months_between(jan2018, jan2019), 12)
        self.assertEqual(report._months_between(jan2019, jan2018), -12)
        self.assertEqual(report._month_add(jan2019, 1), feb2019)
        self.assertEqual(report._month_add(jan2018, 13), feb2019)
