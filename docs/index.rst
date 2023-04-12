.. Jira-Select documentation master file, created by
   sphinx-quickstart on Fri Jul 17 22:36:19 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Jira-Select's documentation!
=======================================

.. image:: https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/jira-select/demo.3.gif

Jira-select is a command-line tool and library that helps you
generate the useful insights you need out of Jira.

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

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   quickstart.rst
   query.rst
   query_lifecycle.rst
   functions.rst
   parameters.rst
   how_to.rst
   examples.rst
   commands.rst
   extending.rst
   troubleshooting.rst
   appendix.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
