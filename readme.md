# Jira-CSV: Easily export issues from Jira to a CSV file

## Quickstart

First, you need to configure `jira-csv` to connect to your jira instance:

```
jira-csv configure
```

Then, you'll need to create a yaml file describing your query and save it
somewhere; example:

```yaml
select:
  - key
  - summary
  - timetracking.originalEstimate as "Hours Estimate"
  - customfield_10048 as "My Important Field"
from: issues
where:
  - labels = "frontend"
  - assignee = "me@adamcoddington.net"
  - resolution is null
```

Now you can run your query:

```
jira-csv run /path/to/query.yaml
```

& it'll hand you back a CSV document with the fields you've selected.
