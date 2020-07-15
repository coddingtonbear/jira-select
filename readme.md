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

See the built-in help (`--help`) for more options.

## Future Goals

- Interactive mode: field names are a little arcane in Jira for things
  like custom fields. It might be nice to be able to be handeld through
  the process of building a query using a PyInquirer-based UI, and either
  generating a yaml file for later execution or running that query
  immediately.
- Output formatting: Support for output formatting functions so you can
  do things like look up the name of a sprint instead of just showing the
  ID. This will probably take the form of a function call wrapping the
  field name that matches the name of an entrypoint in `jira_csv_functions`.
- Python filtering: Support for filtering rows to ones that meet specific
  conditions using python code. I'm imagining being represented in a
  `having:` section of the query yaml.
