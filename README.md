zaius\_export: export api for custom reporting
=============================================

Using zaius\_export, you can build and automate custom reports.
Like this:
```python
import datetime
import zaius.export as export

# count the users who clicked this week
last_week = datetime.date.today() - datetime.timedelta(days=7)
last_week = datetime.datetime.fromordinal(last_week.toordinal()).replace(tzinfo=datetime.timezone.utc)

query = """
select zaius_id
from events
where
  event_type = 'email'
  and action = 'click'
  and ts > {}
""".format(int(last_week.timestamp()))
rows = export.API().query(query)
print(len(set([r['zaius_id'] for r in rows])))
```

Or, use pre-baked reports. Like this:
```sh
$ zaius-export product-attribution 2019-1-1 2019-1-31
```

Or This:
```sh
$ zaius-export lifecycle-progress 2018-1 2019-1
```
Or This:
```sh
$ zaius-export email-metrics 9097 2019-4-25 2020-4-25
```
Replace '9097' with the campaign ID you want to view metrics for. 
Replace '2019-4-25 2020-4-25' with the timerange of your choice. This timerange reflects the times assigned to the 'Scheduled Campaign Run Time' field of email send events. For each of the send events that meet that time range, any and all opens, clicks, and spamreports are counted if they happened, irregardless of when they happened.
This timerange also serves as the lower and upper bounds in which unsubscribe events happened.

You can specify the output file. This example creates an export.csv file in the Documents directory:
```sh
$ zaius-export --output ~/Documents/export.csv product-attribution 2019-1-1 2019-1-31
```


## Installation

Installation happens in the usual way:

```sh
$ pip install zaius_export
```

Now the `zaius-export` utility should be on your PATH.

## Authorization

API calls depend on having a set of credentials available to authenticate your request. By
default, all tools will look for these to be defined in $HOME/.zaius\_api. This file
should look like this:
``` {.sourceCode .ini}
[auth]
aws_access_key_id: ***
aws_secret_access_key: ***
zaius_secret_key: ***
```

You can find the appropriate values for this file by logging into Zaius. Click the gear icon
next to your business name at the top left of the screen, select "APIs" from the menu on the
left (under Data Management), and then find your zaius\_secret\_key under the Private tab.

Your AWS credentials can be found in the Integrations section (Gear Icon, Data Management,
Integrations) by opening the AWS integration.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/ZaiusInc/zaius-magento-2/tags). 


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

