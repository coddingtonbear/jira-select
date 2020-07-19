# Jira-Select: Easily export issues from Jira to CSV

![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/jira-select/demo.2.gif)

Jira-select is a command-line tool and library that helps you
generate the useful insights you need out of Jira.

Jira has its own query language -- it's called JQL --
but there are many limitations in what is possible via JQL.
Some data is returned in arcane formats (e.g. sprint information),
data cannot be grouped (there's nothing like SQL's `GROUP BY` statement),
and because of that lack of grouping, there are no aggregation functions --
no `SUM`-ing story points or estimates for you,
and if you want to write a custom function for processing a field,
well, I'm not even sure where you'd begin.
Jira-select makes those things possible and easy.

If you've ever found yourself held back by the limitations of Jira's
built-in query language, this tool may make your life easier.
Using Jira-select you can perform a wide variety of SQL-like query
operations including grouping, aggregation, custom functions, and more.

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

The editor uses `vi` bindings by default; so once you're ready to submit
your query, press `Esc` followed by `Enter` and after a short wait (watch the progressbars), you'll be shown your results. Press `q` to exit your results.
