Query Format
============

Jira-select queries are written in a YAML format,
but using section names inspired by SQL.

Here's a simple example that will return all Jira issues assigned to you:

.. code-block:: yaml

   select:
   - Issue Key: key
   - Issue Summary: summary
   from: issues
   where:
   - assignee = "your-email@your-company.net"

Here's a query that uses many more of the possible sections,
but know that in real life, you're very unlikely to use them all at once:

.. code-block:: yaml

   select:
     My Assignee: assignee
     Key Length: len(key)
   from: issues
   expand:
   - changelog
   where:
   - project = "MYPROJECT"
   order_by:
   - created
   filter:
   - customfield10010 == 140
   group_by:
   - assignee
   having:
   - len(key) > 5
   sort_by:
   - len(key) desc
   limit: 100
   cap: 10
   cache: 86400

Below, we'll go over what each of these sections are for in detail.

Query Structure Overview
------------------------

.. csv-table:: Jira-select Query Sections
   :file: evaluation_location.csv
   :header-rows: 1

What is a ``JqlString``
~~~~~~~~~~~~~~~~~~~~~~~

A ``JqlString`` is standard Jira JQL.
You can find more information about writing JQL
in `Jira's JQL documentation <https://www.atlassian.com/blog/jira-software/jql-the-most-flexible-way-to-search-jira-14>`_.

What is an ``Expression``
~~~~~~~~~~~~~~~~~~~~~~~~~

An ``Expression`` is an expression evaluated by Jira-select.
Expressions have access to all
functions documented in :ref:`Query Functions`.
The variables available for use in your expressions can be determined
by using ``jira-select schema [issues|boards|sprints]``.

Expressions are (with one caveat) valid Python expressions.
The single caveat is that you can use curly braces to quote
field names.
These curly-brace-quoted fields will be replaced with the actual
Jira field name before processing the expression in Python.

For example; if you have a custom field named ``customfield10010``
that has a human-readable name of ``Story Points``, you can create
an expression like::

   {Story Points} >= 5

this expression will be transformed into::

   customfield10010 >= 5

before evaluating the expression in Python.

Ubiquitous
----------

``select``
~~~~~~~~~~

This section defines what data you would like to include in your report.
It should be a dictionary mapping the column name with the expression
you would like to display in that column.
This section *can* use custom functions (see :ref:`Query Functions` for options).

For example:

.. code-block:: yaml

   select:
     My Field Name: somefunction(my_field)

.. note::

   This section supports a handful of formats
   in addition to the one discussed here
   that you may find in some documentation
   or in other examples including:

   You can specify columns as a list:

   .. code-block:: yaml

      select:
      - somefunction(my_field) as "My Field Name"

   You can specify a single column as a string:

   .. code-block:: yaml

      select: somefunction(my_field) as "My Field Name"

   The above formats will be supported for the foreseeable future,
   but the dictionary-based format discussed outside this box is the
   preferred format for writing queries.

As a shorthand, if you do not provide a value for your dictionary entry,
the dictionary entry's name will be used as the expression for your column:

.. code-block:: yaml

   select:
     issuetype:
     key:
     summary:
   from: issues

In the above example, the fields ``issuetype``, ``key``, and ``summary``
will be displayed in columns matching their field name.

If you would like to return *all* fields values,
use the expression ``*`` as a stirng value to your `select` statement:

.. code-block:: yaml

   select: "*"
   from: issues

.. important::

   Due to yaml parsing rules, the ``*`` expression must be quoted.

``from``
~~~~~~~~

This section defines what you would like to query.
The value should be a string.

There are two query sources currently implemented:

* ``issues``: Searches Jira issues.
* ``boards``: Searches Jira boards.
* ``sprints``: Searches Jira sprints.

Common
------

``where``
~~~~~~~~~

The ``where`` section varies depending upon what kind of data source
you are querying from.

``issues``
__________

This section is where you enter the JQL for your query.
This should be provided as a list of strings;
these strings will be ``AND``-ed together to generate the query sent to Jira.

.. code-block:: yaml

   where:
   - assignee = 'me@adamcoddington.net'

You *cannot* use custom functions in this section
given that it is evaluated on your Jira server instead of locally.

``boards``
__________

You can provide key-value pairs to limit the returned boards;
the following parameters are allowed:

- ``type``: The board type.  Known values include 'scrum', 'kanban',
  and 'simple'.
- ``name``: The board name.  Returned boards mustinclude the string
  you provided somewhere in their name.


.. code-block:: yaml

   where:
     name: 'My Board'

``sprints``
___________

You can provide key-value pairs to limit the returned boards;
the following parameters are allowed:

- ``state``: The sprint state.  Known values include 'future', 'active',
  or 'closed'.
- ``board_type``: The board type of the board to which this sprint belongs.
  Known values include 'scrum', 'kanban', and 'simple'.
- ``board_name``: The board name of the board to which this sprint belongs.
  Returned boards mustinclude the string you provided somewhere in their name.

.. code-block:: yaml

   where:
     state: 'active'

.. note::

   This type of query is slow
   due to the way Jira's API exposes this type of record.
   There is no endpoint allowing us to list sprints directly.
   Instead, we must collect a list of sprints
   by requesting a list of sprints for each board.

   You can improve performance substantially
   by using the ``board_type`` or ``board_name`` parameters
   to limit the number of boards we will need to request sprints for.

``order_by``
~~~~~~~~~~~~

This section is where you enter your JQL ordeirng instructions and should
be a list of strings.

You *cannot* use custom functions in this section
given that it is evaluated on your Jira server instead of locally.

``group_by``
~~~~~~~~~~~~

This section is where you can define how you would like your rows to be grouped.
This behaves similarly to SQL's ``GROUP BY`` statement in that rows sharing
the same result in your ``group_by`` expression will be grouped togehter.

For example; to count the number of issues by type that are assigned to you
you could run the following query:

.. code-block:: yaml

   select:
     Issue Type: issuetype
     Key Length: len(key)
   from: issues
   where:
   - assignee = "your-email@your-company.net"
   group_by:
   - issuetype

.. Note::

   When executing an SQL query that uses a ``GROUP BY`` statement,
   you will always see just a single value for each column
   even if that column represents multiple rows' values.

   Unlike standard SQL,
   in Jira-select column values will always contain arrays of values
   when your column definition does not use a value entered in your ``group_by`` section.
   If you are surprised about a particular field showing an array holding values that are all the same,
   try adding that column to your ``group_by`` statement, too.

If you would like to perform an aggregation across all returned values,
you can provide ``True`` in your ``group_by`` statement.
This works because, for every row, ``True`` will evaluate to the same result
causing all rows to be grouped together:

.. code-block:: yaml

   select:
     Key Length: len(key)
   from: issues
   where:
   - assignee = "your-email@your-company.net"
   group_by:
   - True

You **can** use custom functions in this section.

``having``
~~~~~~~~~~

This section is where you can provide filtering instructions that Jql cannot handle
because they either require local functions or operate on grouped data.

You **can** use custom functions in this section.

``calculate``
~~~~~~~~~~~~~

Perhaps you have an expression you'd like to calculate once
and use multiple times across your query
(e.g. multiple times across ``select`` columns,
or in both ``select`` and ``filter`` at the same time).
You can use the ``calculate`` section for performing those calculations
once and then referencing their result in other expressions; for example:

.. code-block:: yaml

   select:
     Hours in Progress: round(in_progress_seconds / 3600)
   calculate:
     in_progress_seconds: interval_size(interval_matching(issue, status="In Progress") & interval_business_hours(parse_date(created))).total_seconds() / 28800
   from: issues
   filter:
   - in_progress_seconds > 60
   expand:
   - changelog

The above example will calculate the total amount of time issues were in progress
in hours while excluding results where they were in progress for fewer than sixty seconds.

``sort_by``
~~~~~~~~~~~

This section is where you can provide sorting instructions that Jql cannot handle
because they either require local functions or operate on grouped data.

You **can** use custom functions in this section.

``limit``
~~~~~~~~~

This sets a limit on how many rows will be returned from Jira.
See :ref:`Query Lifecycle` to understand where this fits in the query lifecycle.

If you would like to limit the count of rows *after* ``group_by`` and
``having`` have reduced the count of rows, use ``cap`` instead.

.. note::

   ``limit`` is handled by Jira itself, so if you would like to
   instead limit the number of rows returned after ``having``
   and ``grouping`` expressions have reduced the row count,
   use ``cap`` instead.

``cache``
~~~~~~~~~

This will cache the results returned by Jira
for up to the specified number of seconds.
This can be very helpful if you are iterating on changes
to your ``group_by`` or ``having`` sections
in that you can make minor changes
and avoid the slow process of requesting records
from jira after every change.

Note that the cache parameter can be in one of two forms:

.. code-block:: yaml

   cache: 86400

In this case, we will cache the results for up to 86400 seconds
and will also accept an already-stored cached value
that is up to that number of seconds old.

.. code-block:: yaml

   cache: [300, 86400]

In this case, we will cache the results for up to 86400 seconds,
but will only accept a cached value that is 300 seconds old or newer.

You can also pass ``null`` as the second parameter to allow
reading from the cache, but disallow writing a new cached value,
or pass ``null`` as the first parameter to disallow using an existing cache,
but allowing storing a new value.

Note that to take full advantage of caching,
you may also want to use the ``filter`` feature described below.
Using it can let you take better advantage of your cached values.

Unusual
-------

``expand``
~~~~~~~~~~

Jira has a concept of "field expansion",
and although by default Jira-select will fetch "all" data,
that won't actually return quite all of the data.
You can find more information about what data this will return
by reading `the Jira documentation covering
"Search for issues using JQL (GET)" <https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get>`_.


``filter``
~~~~~~~~~~

In most cases, using ``where`` (pre-grouping/having, processed by Jira)
and ``having`` (post-grouping) are sufficient.
But there are scenarios where you might want to filter rows
between these two steps.  For example:

* Jql doesn't provide the functionality you need for filtering your resultset,
  but you'll be using a ``group_by`` statement, too, and thus can't just use
  ``having``; because by that point, the field you need to filter on will
  have been grouped with others.
* You are using a long cache interval to quickly iterate on your query and
  do not want to have to update your ``where`` expression since changing that
  will cause us to not use the cached results.

In these cases, you can enter the same sorts of expressions
you'd use in a ``having`` statement in your ``filter`` statement
as a sort of local-side equivalent of ``where``.

You **can** use custom functions in this section.

``cap``
~~~~~~~

This sets a limit on how many rows will be returned,
but unlike ``limit`` is evaluated locally.

This can be used if you want your ``having`` or ``group_by``
statements to have access to as much data as possible
(and thus do not want to use ``limit``
to reduce the number of rows returned from Jira),
but still want to limit the number of rows in your final document.
