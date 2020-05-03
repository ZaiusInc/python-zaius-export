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
        # attribution_days = int(args.attribution_days)

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
            and ts < {end_date_s}
            and campaign_id= {campaign_id_s}
          )
        order by zaius_id, campaign_schedule_run_ts, action
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        sends = 0
        opens = 0
        clicks = 0
        unsubs = 0
        spamreports = 0

        saw_open = False
        saw_send = False
        saw_clicks = False
        saw_unsub = False
        saw_spamreport = False

        last_user_id = None
        last_csrt = None
        last_action = None
        idx = 0

        for idx, row in enumerate(rows):
            if idx % 100000 == 0:
                sys.stderr.write("Read {} rows\n".format(idx))
            if (
                (last_user_id != row['zaius_id'] and last_csrt != row['campaign_schedule_run_ts'] and last_action != row['action'])
                or (last_user_id == row['zaius_id'] and last_csrt != row['campaign_schedule_run_ts'] and last_action != row['action'])
                or (last_user_id == row['zaius_id'] and last_csrt == row['campaign_schedule_run_ts'] and last_action != row['action'])
                or (last_user_id != row['zaius_id'] and last_csrt == row['campaign_schedule_run_ts'] and last_action != row['action'])
                or (last_user_id != row['zaius_id'] and last_csrt == row['campaign_schedule_run_ts'] and last_action == row['action'])
                or (last_user_id == row['zaius_id'] and last_csrt != row['campaign_schedule_run_ts'] and last_action == row['action'])
                or (last_user_id != row['zaius_id'] and last_csrt != row['campaign_schedule_run_ts'] and last_action == row['action'])
                ):
                last_user_id = row['zaius_id']
                last_csrt = row['campaign_schedule_run_ts']
                last_action = row['action']
                saw_open = False
                saw_send = False
                saw_clicks = False
                saw_unsub = False
                saw_spamreport = False
                
                
                if row['action'] == 'open':
                    saw_open = True
                if row['action'] == 'sent':
                    saw_send = True
                if row['action'] == 'click':
                    saw_clicks = True
                if row['action'] == 'unsubscribe':
                    saw_unsub = True
                if row['action'] == 'spamreport':
                    saw_spamreport = True
                if saw_open:
                    opens += 1
                if saw_send:
                    sends += 1
                if saw_clicks:
                    clicks += 1
                if saw_unsub:
                    unsubs +=1
                if saw_spamreport:
                    spamreports += 1
            elif (last_user_id == row['zaius_id'] and last_csrt == row['campaign_schedule_run_ts'] and last_action == row['action']):
                opens
                sends
                clicks
                unsubs
                spamreports
        
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
        sys.stderr.write("Read {} rows\n".format(idx))


    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(EmailMetrics())