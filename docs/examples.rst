Examples
========

Finding all issues assigned to a particular user
------------------------------------------------

.. code-block:: yaml

   select: "*"
   from: issues
   where:
   - assignee = "some-user@some-company.com"


Summing the number of story points assigned in a particular sprint
------------------------------------------------------------------

.. code-block:: yaml

   select:
     Total Story Points: sum({Story Points})
   from: issues
   where:
   - project = "MYPROJECT"
   group_by:
   - True
   having:
   - '"My Sprint Name" in sprint_name({Sprint}[-1])'

In Jira, your "Story Points" and "Sprint" fields may have any number of names
since they're "Custom Fields"
-- their real names are things like
``customfield10024`` and ``customfield10428``,
but may vary instance to instance.
You can use the field name directly in your query,
but if you know only the "human-readable" name
for your field, you can provide it in brackets
as shown above with -- `{Story Points}` and `{Sprint}`.

The ``where`` limitation here is used solely for reducing the number of records needing to be downloaded,
and can be omitted if you are willing to wait.

The ``group_by`` expression here is to make all of your rows be grouped together
so the ``sum`` operation in your ``select`` block will operate over all of the returned rows.
``True`` is used because that expression will evaluate to the same value for every row.

In the ``having`` section, you can see a fairly complicated expression
that takes the last sprint associated with each returned issue,
looks up that sprint's name and compares it with the sprint name you are looking for.
We're using the ``in`` python expression here because I can't remember the full name,
but I can remember part of it.
You'll notice that the line is quoted;
that's necessary only because the yaml parser interprets
a line starting with a double-quote
a little differently from one that does not.
Try running the query without quoting the string to see what I mean.

Summing the total estimated size of issues per-person for a given sprint
------------------------------------------------------------------------

.. code-block:: yaml

   select:
     Assignee: assignee
     Total Size: sum(map(estimate_to_days, timeestimate.originalEstimate))
   from: issues
   where:
   - project = "MYPROJECT"
   group_by:
   - assignee
   having:
   - '"My Sprint Name" in sprint_name({Sprint}[-1])'

See :ref:`Summing the number of story points assigned in a particular sprint` for
an explanation of the ``having`` section here.

In Jira, estimations are stored in the ``timeestimate.originalEstimate`` field,
but since we've grouped our rows by assignee,
``timeestimate`` represents an array of objects
instead of a single object holding the ``originalEstimate`` we want.

If we were to stop here, we would receive an array of strings
looking something like::

   ["1d", "4h", "2d", "30m"]

but, we want to be able to sum these estimates,
so we'll ``map`` each of those through the ``estimate_to_days`` function.
This will create an array like this::

   [1, 0.5, 2, 0.625]

An array isn't quite what we want
-- we want the total number of days --
so we use the ``sum`` function to get that.

See :ref:`Query Functions` for more information.

Summing story points of issues resolved during a particular sprint
------------------------------------------------------------------

.. code-block:: yaml

   select:
     Assignee: assignee
     Story Points: sum({Story Points})
   from: issues
   where:
   - project = 'My Project'
   filter:
   - simple_filter(
       flatten_changelog(changelog),
       created__gt=parse_datetime(get_sprint_by_name("Board Name", "Sprint Name").startDate),
       created__lt=parse_datetime(get_sprint_by_name("Board Name", "Sprint Name").endDate),
       field__eq="resolution",
       fromValue__eq=None,
       toValue__ne=None
     )
   group_by:
   - assignee
   expand:
   - changelog

The most important section in the above is in ``filter``;
here you'll see that we're using the ``simple_filter`` function
for filtering the (flattened) list of changelog entries
to those changelog enttries that were created during the sprint
and indicate that the field ``resolution`` was changed from ``None``
to something that is not ``None``.

For a row to be returned from ``filter``,
each expression should return a truthy value.
So rows that do not have a corresponding changelog entry
matching the above requirements
will be omitted from results.

Summing worklog entries
-----------------------

.. code-block:: yaml

   select:
     Total Seconds: sum(extract(flatten_list(worklogs.worklogs), "timespentSeconds"))
   from: issues
   group_by:
   - True

Worklog entries on issues are shaped like this for every row
(unnecessary fields omitted)::

   {
      "total": 1,
      "worklogs": [
         {"timespentSeconds": 60},
         {"timespentSeconds": 100},
      ]
   }

So, if we were to just select ``worklogs.worklogs`` we'd receive an array of results in this shape::

   [
      [
         {"timespentSeconds": 60},
         {"timespentSeconds": 100},
      ],
      [
         {"timespentSeconds": 50},
      ]
   ]

The value we need is nested deeply in there, so we should first try to
flatten the list of lists using ``flatten_list``; if we do that, our list
will become::

   [
      {"timespentSeconds": 60},
      {"timespentSeconds": 100},
      {"timespentSeconds": 50},
   ]

We're still not quite there -- the value under ``timespentSeconds``
still needs to be ``extract``ed
from the inner objects using ``extract``;
if we do that we receive::

   [
      60,
      100,
      50
   ]

We finally have something summable & can wrap that set of calls with ``sum``
giving us an answer of ``210``.

The ``group_by`` expression here is to make all of your rows be grouped together
so the ``sum`` operation in your ``select`` block will operate over all of the returned rows.
``True`` is used because that expression will evaluate to the same value for every row.
