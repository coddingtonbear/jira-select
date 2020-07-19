# Jira-Select: Easily export issues from Jira to CSV

## Quickstart

First, you need to configure `jira-csv` to connect to your jira instance:

```
jira-csv configure
```

Then, you can open up your shell:

```
jira-csv shell
```

Now, you can type out your query -- the below will find issues assigned
to you:

```yaml
select:
  - key
  - summary
from: issues
where:
  - assignee = "your-email@somecompany.com"
  - resolution is null
```

After you're ready to submit your query, press `Esc` followed by `Enter`,
and after a short wait (watch the progressbars), you'll be shown your
results. Press `q` to exit your results.

See the built-in help (`--help`) for more options.

## Advanced Usage

### Functions

Your `select`, `having`, `group_by`, and `sort_by` sections have access
to a wide range of functions as well as to the full breadth
of Python syntax. If the built-in functions aren't enough, you can
also just write your own and either register them at runtime or make
them persistently available via a setuptools entrypoint.

#### Formatting rows

```yaml
select:
  - status
  - summary
  - customfield_10069 as "Story Points"
  - len(customfield_10010) as "Sprint Count"
  - sprint_name(customfield_10010[-1]) as "Sprint Name"
from: issues
```

In the above example, two of the displayed columns are processed with
a function:

- `Sprint Count`: Will render the number of array elements in the field
  containing the list of sprints in which this issue was present.
- `Sprint Name`: Will show the name of the last sprint associated with
  the displayed issue.

#### Omitting rows

```yaml
select:
  - status as "Status"
  - summary as "Summary"
  - customfield_10069 as "Story Points"
from: issues
having:
  # The quoting below is required only because the first character of line
  # being a double-quote causes YAML parsers to parse the line differently
  - '"Sprint #19" in sprint_name(customfield_10010[-1])'
```

In the above example, the issues returned from Jira will be compared against
each constraint you've entered in the `having` section; in this case, all
returned issues not having the string "Sprint #19" in the name of the last
sprint associated with the displayed issue will not be written to your output.

Note that `having` entries are processed locally instead of on the
Jira server so filtering using `having` entries is much slower than
using standard Jql due to the amount of (potentially) unnecessary data
transfer involved. It is recommended that you use `having` only when
your logic cannot be expressed in standard Jql (i.e. in the "where" section).

### Grouping & Aggregation

You can group and/or aggregate your returned rows by using `group_by`:

```yaml
select:
  - status
  - count(key)
from: issues
group_by:
  - status
```

You'll receive just a single result row for each status, and a count
of how many records shared that status in the second column.

### Sorting

You can order your entries using any expression, too:

```yaml
select:
  - status
  - count(key)
from: issues
group_by:
  - status
sort_by:
  - count(key) desc
```

This will sort all returned tickets, grouped by status, in descending order
from the status that has the most tickets to the one that has the
fewest.

### Limiting the number of results

You can limit the number of results returned by adding a `limit` to your query:

```yaml
select:
  - key
  - status
  - summary
from: issues
where:
  - assignee = "me@adamcoddington.net"
limit: 10
```

### Expanding Jira fields

You can ask Jira to expand issue fields by adding an `expand` element to your query:

```yaml
select:
  - key
  - status
  - summary
from: issues
expand:
  - transitions
```

The meaning of these expansions is defined by Jira; you can find more information
in [Jira's documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#expansion).
