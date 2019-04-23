# -*- coding: utf-8 -*-
"""Product Purchase Attribution Report

Attribute product purchases to the last email engagement (open or click)
that happened within a 3-day window of the purchase.
"""

import csv
import sys
import datetime

from .spec import ReportSpec


class LifecycleProgress(ReportSpec):
    """Product Attribution Report"""

    def register_args(self, parser):
        parser = parser.add_parser(
            "lifecycle-progress",
            help="track how your mix of customers by lifecycle stage has evolved over time",
        )

        parser.add_argument("start_month", help="earlist date, YYYY-MM, inclusive")
        parser.add_argument("end_month", help="latest date, YYYY-MM, exclusive")
        parser.set_defaults(func=self.execute)

    # pylint: disable=R0914
    def execute(self, api, destination, args):
        writer = csv.DictWriter(
            destination,
            ["month", "no_purchase", "one_purchase", "repeat_purchase", "loyal"],
        )
        writer.writeheader()

        start_date = self._parse_month(args.start_month)
        end_date = self._parse_month(args.end_month)

        # build our query
        params = {"end_date_s": end_date.strftime("%s")}
        stmt = """
        select
            ts,
            user_id,
            event_type,
            order_id
        from events
        where
            ts < {end_date_s}
            and (
                (
                    event_type = 'order'
                    and action = 'purchase'
                    and order.status <> 'canceled'
                )
                or event_type = 'customer_discovered'
            )
        order by user_id, ts
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        # our result
        month_counts = []
        for idx in range(self._months_between(start_date, end_date)):
            month_counts.append(
                {
                    "month": str(self._month_add(start_date, idx)),
                    "no_purchase": 0,
                    "one_purchase": 0,
                    "repeat_purchase": 0,
                    "loyal": 0,
                }
            )

        def _stage(count):
            if count == 0:
                return "no_purchase"
            if count == 1:
                return "one_purchase"
            if count == 2:
                return "repeat_purchase"
            return "loyal"

        # our result comes back ordered by user_id, ts so we can know
        # that we'll see all of one user before we see then next
        current_user = None
        current_month = None
        purchase_count = set()

        def _finish_pending(month):
            if current_user is not None:
                for idx in range(current_month, month):
                    month_counts[idx][_stage(len(purchase_count))] += 1

        for idx, row in enumerate(rows):
            if idx % 100000 == 0:
                sys.stderr.write("Read {} rows\n".format(idx))

            if row["user_id"] != current_user:
                _finish_pending(len(month_counts))
                current_user = row["user_id"]
                current_month = None
                purchase_count = set()

            ts_s = datetime.datetime.utcfromtimestamp(int(row["ts"]))
            month = self._months_between(start_date, ts_s)
            if current_month is None:
                current_month = max(0, month)
            if row["event_type"] == "order":
                # record the purchase
                _finish_pending(month)
                current_month = max(0, month)
                purchase_count.add(row['order_id'])

        _finish_pending(len(month_counts))
        sys.stderr.write("Read {} rows\n".format(idx))

        for month_count in month_counts:
            writer.writerow(month_count)

    # pylint: disable=R0201
    def _parse_month(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m").date()

    # pylint: disable=R0201
    def _months_between(self, begin, end):
        return end.year * 12 + end.month - (begin.year * 12 + begin.month)

    def _month_add(self, begin, step):
        year_inc = (begin.month - 1 + step) // 12
        month = ((begin.month - 1 + step) % 12) + 1
        return datetime.date(begin.year + year_inc, month, 1)


ReportSpec.register(LifecycleProgress())
