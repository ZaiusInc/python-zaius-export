# -*- coding: utf-8 -*-
"""Base class for reports

Reports inherit from this base class and register themselves
using the register classmethod.
"""


class ReportSpec:
    """Base class for reports"""

    specs = []

    # pylint: disable=R0201
    def register_args(self, parser):
        """Implementations should add a subparser to parser that
        names the report and adds any report specific arguments."""

        raise ValueError("not implemented")

    # pylint: disable=R0201
    def execute(self, api, destination, args):
        """Implementations should evaluate the report and write
        the output to destination."""

        raise ValueError("not implemented")

    @classmethod
    def register(cls, report_spec):
        """Register an instance of a report so the CLI can access
        it."""

        cls.specs.append(report_spec)
