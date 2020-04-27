# -*- coding: utf-8 -*-
"""Email Metrics Report

Aggregates email metrics for specified campaign_schedule_run_ts period.
"""

import csv
import sys
import datetime
import json

from .spec import ReportSpec
from itertools import islice


class EmailMetrics(ReportSpec):
    """Email Metrics Report"""

    def register_args(self, parser):
        parser = parser.add_parser(
            "email-metrics",
            help="individual purchases attributed to the 3-day last touched campaign",
        )
        parser.add_argument("campaign_id", 
        help = "the ID of the campaign to get metrics for",
        default = '9097',)
        parser.add_argument("start_date", help="earlist date, YYYY-MM-DD, inclusive")
        parser.add_argument("end_date", help="latest date, YYYY-MM-DD, exclusive")
        parser.add_argument(
            "--attribution-days",
            help="maximum number of days after an engagement that a purchase can be attributed",
            default=3,
        )

        parser.set_defaults(func=self.execute)

    # pylint: disable=R0914
    def execute(self, api, destination, args):
        columns = [
            "total sends",
            "unique opens",
            "unique clicks",
            "unique unsubscribes",
            "unique spam reports",
            "open rate (%)",
            "click through rate (%)",
            "unsubscribe rate (%)"
        ]
        writer = csv.DictWriter(destination, columns)
        writer.writeheader()

        campaign_id = str(args.campaign_id)
        start_date = self._parse_date(args.start_date)
        end_date = self._parse_date(args.end_date)
        attribution_days = int(args.attribution_days)

        # build our query
        params = {
            "campaign_id_s": str(campaign_id),
            "start_date_s": int(start_date.timestamp()),
            "end_date_s": int(end_date.timestamp()),
        }
        stmt = """
        select
            zaius_id,
            action,
            event_type,
            campaign_schedule_run_ts,
            campaign_id
        from events
        where
          (
            event_type = 'email'
            and (
              action = 'open'
              or action = 'click'
              or action = 'sent'
              or action = 'spamreport'
            )
            and campaign_schedule_run_ts >= {start_date_s}
            and campaign_schedule_run_ts < {end_date_s}
            and campaign_id = {campaign_id_s}
          )
          or (
            event_type = 'list'
            and action = 'unsubscribe'
            and ts >= {start_date_s}
            and campaign_id= {campaign_id_s}
          )
        order by zaius_id, campaign_schedule_run_ts
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)
        all_rows = (row for row in rows)

        makeset = set()
        for row in all_rows:
            x = json.dumps(row)
            makeset.add(x)

        makelist = list(makeset)
        loadedlist = [(json.loads(i)) for i in makelist]

        rows = 0
        sends = 0
        opens = 0
        clicks = 0
        unsubs = 0
        spamreports = 0
        
        result = [{k:v} for k,v in enumerate(loadedlist)]

        for each in result:
            if (each.get(rows).get('action') == 'sent'):
                rows = rows + 1
                sends = sends + 1
            elif (each.get(rows).get('action') == 'open'):
                rows = rows + 1
                opens = opens + 1
            elif (each.get(rows).get('action') == 'click'):
                rows = rows + 1
                clicks = clicks + 1
            elif (each.get(rows).get('action') == 'unsubscribe'):
                rows = rows + 1
                unsubs = unsubs + 1
            elif (each.get(rows).get('action') == 'spamreport'):
                rows = rows + 1
                spamreports = spamreports + 1
            else:
                rows = rows + 1
        
        writer.writerow(
                    {
                        "total sends": sends,
                        "unique opens": opens,
                        "unique clicks": clicks,
                        "unique unsubscribes": unsubs,
                        "unique spam reports": spamreports,
                        "open rate (%)": opens / sends * 100,
                        "click through rate (%)": clicks / sends * 100,
                        "unsubscribe rate (%)": unsubs / sends * 100
                    }
                )


    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(EmailMetrics())