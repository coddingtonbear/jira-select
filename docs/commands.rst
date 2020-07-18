Command-Line
============

`jira-select run FILENAME [--format=csv] [--output=/path/result.csv] [--view]`
-------------------------------------------------------------------------------

Executes query specified in FILENAME and returns results in the specified format.

If no output path is specified and the ``--view`` option not provided, the
output will be written to stdout.

Specifying the ``--view`` option will open the query results in your
configured CSV viewer (by default `Visidata <https://www.visidata.org/>`_ via `vd`).

`jira-select build-query [--output=/path/query.yml]`
----------------------------------------------------

Allows you to interactively generate a query definition file.

`jira-select configure`
-----------------------

Allows you to interactively configure jira-select to connect
to your Jira instance.

`jira-select store-password USERNAME`
-------------------------------------

Allows you to store a password for USERNAME in your system keychain.

`jirafs-select functions [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
------------------------------------------------------------------------------

Displays functions available for use in a query.

May be filtered using ``--having=EXPRESSION``.  The provided expression
should can access the following fields:

* `name`
* `description`

Provided search terms must each match either the name or description to be displayed.

`jira-select schema issues [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
--------------------------------------------------------------------------------

Displays issue fields available for query.

May be filtered using ``--having=EXPRESSION``.  The provided expression
should can access the following fields:

* `key`
* `type`
* `description`
* `raw`

Provided search terms must each match either the name or description to be displayed.
