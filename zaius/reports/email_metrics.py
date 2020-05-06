# -*- coding: utf-8 -*-
"""Email Metrics Report

Aggregates email metrics for specified campaign_schedule_run_ts period.
"""

import csv
import datetime

from .spec import ReportSpec

class EmailMetrics(ReportSpec):
    """Email Metrics Report"""

    def register_args(self, parser):
        parser = parser.add_parser(
            "email-metrics",
            help="individual purchases attributed to the 3-day last touched campaign"
        )
        parser.add_argument("campaign_id",
                            help="the ID of the campaign to get metrics for",
                            default='9097')
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

        last_user_id_csrt = None


        seen_actions = {}
        unique_counts = {}
        for row in rows:
            current_user_id_csrt = (row['zaius_id'], row['campaign_schedule_run_ts'])
            if current_user_id_csrt != last_user_id_csrt:
            # accumulate
                for action in seen_actions.keys():
                    unique_counts[action] = unique_counts.get(action, 0) + 1
            # reset
                seen_actions = {}
        # mark
            seen_actions[row['action']] = True
            last_user_id_csrt = current_user_id_csrt
        # final accumulate to catch whatever user we were processing last
        for action in seen_actions.keys():
            unique_counts[action] = unique_counts.get(action, 0) + 1

        # now index into unique counts by action to write the row
        writer.writerow(
            {
                "total sends": unique_counts['sent'],
                "unique opens": unique_counts['open'],
                "unique clicks": unique_counts['click'],
                "unique unsubscribes": unique_counts['unsubscribe'],
                "unique spam reports": unique_counts['spamreport'],
                "open rate (%)":
                    unique_counts['open'] / unique_counts['sent'] * 100,
                "click through rate (%)":
                    unique_counts['click'] / unique_counts['sent'] * 100,
                "unsubscribe rate (%)":
                    unique_counts['unsubscribe'] / unique_counts['sent'] * 100
            }
        )

    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(EmailMetrics())
