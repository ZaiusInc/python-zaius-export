zaius\_export: export api for custom reporting
=============================================

Using zaius\_export, you can build and automate aweseome reports.
Like this:
``` {.sourceCode .python}
import datetime
import zaius.export as export

# count the users who clicked this week
last_week = datetime.date.today() - datetime.timedelta(days=7)
query = """
select user_id
from events
where
  event_type = 'email'
  and action = 'click'
  and ts > {}
""".format(last_week.strftime('%s')
rows = export.API().query(query)
print(len(set([r['user_id'] for r in rows])))
```

Or, use pre-baked reports. Like this:
``` {.sourceCode .bash}
$ zaius-export --auth zaius-api.ini product-attribution 2019-1-1 2019-1-31
```

Or This:
```
$ zaius-export --auth zaius-api.ini lifecycle-progress 2018-1 2019-1
```


## Installation

zaius\_export only exists in pypi testing currently. This means that to install it you need
to pass an extra argument to pip:

```
pip install --extra-index-url https://test.pypi.org/simple/ zaius_export
```

Now the `zaius-export` utility should be on your PATH.

## Authorization

API calls depend on having a set of credentials available to authenticate your request. By
default, all tools will look for these to be defined in $HOME/.zaius\_api.ini. This file
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

