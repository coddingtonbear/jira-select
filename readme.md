![](https://github.com/coddingtonbear/jira-select/workflows/Run%20Tests/badge.svg) [![Join the chat at https://gitter.im/coddingtonbear/jira-select](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/coddingtonbear/jira-select?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Jira-Select: Get the data you want to see out of Jira

![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/jira-select/demo.3.gif)

Jira-select is a command-line tool and library that lets you run SQL-like
queries against your Jira instance that are far beyond what Jira's built-in
query language can provide.

Jira has its own query language
but there are many limitations around what JQL is capable of.
Some data is returned in arcane formats
(e.g. sprint names are returned as a string looking something like
``com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436...``),
data cannot be grouped (there's nothing like SQL's `GROUP BY` statement),
and because of that lack of grouping, there are no aggregation functions --
no `SUM`-ing story points or estimates per-assignee for you.
And if you want to write a custom function for processing a field,
well, I'm not even sure where you'd begin.
Jira-select makes those things easy.

If you've ever found yourself held back by the limitations of Jira's
built-in query language, this tool may make your life easier.
Using Jira-select you can perform a wide variety of SQL-like query
operations including grouping, aggregation, custom functions, and more.

## Supported Platforms

- Linux
- Windows
- OSX

## Installation

You can either install from pip:

```
pip install jira-select
```

_or_ you can download the latest packaged release here:

https://github.com/coddingtonbear/jira-select/releases

_or_ you can build from source:

```
git clone https://github.com/coddingtonbear/jira-select.git
cd jira-select
pip install -e .
```

## Quickstart

First, you need to configure `jira-select` to connect to your jira instance:

```
jira-select configure
```

Then, you can open up your shell:

```
jira-select shell
```

Now, you can type out your query -- the below will find issues assigned
to you:

```yaml
select:
 Issue Key: key
 Issue Summary: summary
from: issues
where:
  - assignee = "your-email@somecompany.com"
  - resolution is null
```

The editor uses `vi` bindings by default; so once you're ready to submit
your query, press `Esc` followed by `Enter` and after a short wait (watch the progressbars), you'll be shown your results. Press `q` to exit your results.

---

- Documentation for Jira-select is available on [ReadTheDocs](http://jira-select.readthedocs.org/).
- Please post issues on [Github](http://github.com/coddingtonbear/jira-select/issues).
- Questions? Ask them on [Gitter](https://gitter.im/coddingtonbear/jira-select).
