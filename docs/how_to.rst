How to
======

Use Functions
-------------

Your ``select``, ``having``, ``group_by``, and ``sort_by`` sections have access
to a wide range of functions as well as to the full breadth
of Python syntax. If the built-in functions aren't enough, you can
also just write your own and either register them at runtime or make
them persistently available via a setuptools entrypoint.

See :ref:`Query Functions` for a complete list of built-in functions.

Format data using functions
---------------------------

.. code-block:: yaml

   select:
     Status: status
     Summary: summary
     Story Points: "{Story Points}"
     Spring Count: len(customfield_10010)
     Sprint Name: sprint_name(customfield_10010[-1])
   from: issues

In the above example, two of the displayed columns are processed with
a function:

- `Sprint Count`: Will render the number of array elements in the field
  containing the list of sprints in which this issue was present.
- `Sprint Name`: Will show the name of the last sprint associated with
  the displayed issue.

Filter results using functions
------------------------------

.. code-block:: yaml

   select:
     Status: status
     Summary: summary
     Story Points: "{Story Points}"
   from: issues
   having:
     # The quoting below is required only because the first character of line
     # being a double-quote causes YAML parsers to parse the line differently
     - '"Sprint #19" in sprint_name(customfield_10010[-1])'

In the above example, the issues returned from Jira will be compared against
each constraint you've entered in the ``having`` section; in this case, all
returned issues not having the string "Sprint #19" in the name of the last
sprint associated with the displayed issue will not be written to your output.

.. note::

   ``having`` entries are processed locally instead of on the
   Jira server so filtering using `having` entries is slower than
   using standard Jql due to the amount of (potentially) unnecessary data
   transfer involved. It is recommended that you use ``having`` only when
   your logic cannot be expressed in standard Jql (i.e. in the ``where`` section).

Group results & calculate aggregates
------------------------------------

You can group and/or aggregate your returned rows by using ``group_by``:

.. code-block:: yaml

   select:
     Status: status
     Count: count(key)
   from: issues
   group_by:
     - status

You'll receive just a single result row for each status, and a count
of how many records shared that status in the second column.

Sort results using functions
----------------------------

You can order your entries using any expression, too:

.. code-block:: yaml

   select:
     Status: status
     Count: count(key)
   from: issues
   group_by:
     - status
   sort_by:
     - count(key) desc

This will sort all returned tickets, grouped by status, in descending order
from the status that has the most tickets to the one that has the
fewest.

.. note::

   The ``sort_by`` section is evaluated locally instead of by your Jira
   server.  In situations where your expression can be evaluated in Jql,
   you will have faster performance using the ``order_by`` section.

Limit the number of returned results
------------------------------------

You can limit the number of results returned by adding a ``limit`` to your query:

.. code-block:: yaml

   select:
     Key: key
     Status: status
     Summary: summary
   from: issues
   where:
     - assignee = "me@adamcoddington.net"
   limit: 10

Be aware that this limit is handled by Jira;
so only the first N records will be available for downstream steps
in the :ref:`Query Lifecycle`.

Expand Jira Issue Fields
------------------------

You can ask Jira to expand issue fields by adding an ``expand`` element to your query:

.. code-block:: yaml

   select:
     Key: key
     Status: status
     Summary: summary
   from: issues
   expand:
     - transitions

The meaning of these expansions is defined by Jira; you can find more information
in `Jira's documentation <https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/#expansion>`_.
