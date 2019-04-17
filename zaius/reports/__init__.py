# -*- coding: utf-8 -*-
"""Pre-baked reports

Set of reports that can be called from code or executed using
the zaius-export command line utility.

    Example:
        zaius-export demo

"""
from .spec import ReportSpec
from . import demo
from . import product_attribution
from . import lifecycle_progress

SPECS = ReportSpec.specs
