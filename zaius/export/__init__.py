# -*- coding: utf-8 -*-
"""Export API

This module interfaces with the Zaius Export API and exposes data
via a subset of SQL.

Example:
    Count all users who have clicked on an email this week:
        import datetime
        import pyzaius.export as export

        last_week = datetime.date.today() - datetime.timedelta(days=7)
        query = '''
        select user_id
        from events where
            (event_type = 'email')
            and (action = 'click')
            and (ts > {})
        '''.format(last_week.strftime('%s'))
        rows = export.API().query(query)
        len(set([r['user_id'] for r in rows]))

SQL:
    This supports a SQL like syntax. The current limitations are:
    * No aggregations
    * All filters must be of the form "field op value" (e.g. foo = 1 but not foo = bar)
    * No explicit joins

    As an enhancement, this syntax supports implicit joins through all of the declared relations
    in your schema. For example:

        select
            customer.name
        from events

    Will implicitly join to the customers dimension so that it can return the customer name.

Authentication:
    This API requires an auth_struct such as those produced by pyzaius.auth. By
    default it will attempt to read what it needs out of $HOME/.zaius_api
"""

from .api import *
