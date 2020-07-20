Command-Line
============

`jira-select shell [--editor-mode=MODE]`
----------------------------------------

Opens an interactive shell (a.k.a repl) allowing you to interact with Jira
and see your query results immediately afterward.

This is a lot like the "shell" you might have used for postgres, mysql
or sqlite. Except that this one syntax highlights your query and has
tab completion.

* ``--editor-mode=MODE``: Set the editor mode to use; options include
  ``vi`` and ``emacs``.  The default value for this can be set in your
  configuration file by setting ``shell.emacs_mode`` to ``True`` or
  ``False``.  See ``--help`` if you're not sure where your configuration
  file is.

.. _run subcommand:

`jira-select run FILENAME [--format=FORMAT] [--output=PATH] [--view]`
---------------------------------------------------------------------

Executes query specified in FILENAME and returns results in the specified format.

* ``--format=FORMAT``: Sets the output format; options include ``csv`` (default)
  and ``table``.
* ``--output=PATH``: Sets the output path.  If unspecified, the output
  will be written to stdout.
* ``--view``: Open the appropriate viewer to view your query results after
  the query has completed.

`jira-select build-query [--output=PATH]`
----------------------------------------------------

Allows you to interactively generate a query definition file.

* ``--output=PATH``: Sets the output path.  If unspecified, the output
  will be written to stdout.

`jira-select configure`
-----------------------

Allows you to interactively configure jira-select to connect
to your Jira instance.

`jira-select store-password USERNAME`
-------------------------------------

Allows you to store a password for USERNAME in your system keychain.

* ``USERNAME``: The username to store a password for.

.. _functions subcommand:

`jirafs-select functions [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
------------------------------------------------------------------------------

Displays functions available for use in a query.

* ``having=EXPRESSION``: A ``having`` expression to use for filtering displayed
  results.  The provided fields for filtering are ``name`` and ``description``.
* ``SEARCH_TERM``: A search term to use for filtering results.  The term
  is case-insensitive and must be present in either the function name or
  description to be displayed.

.. _schema subcommand:

`jira-select schema issues [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
--------------------------------------------------------------------------------

Displays issue fields available for query.

* ``having=EXPRESSION``: A ``having`` expression to use for filtering displayed
  results.  The provided fields for filtering are ``id``, ``type``,
  ``description``, and ``raw``.
* ``SEARCH_TERM``: A search term to use for filtering results.  The term
  is case-insensitive and must be present in either the function name or
  description to be displayed.
