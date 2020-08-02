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

`jira-select schema [issues|boards|sprints] [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
-------------------------------------------------------------------------------------------------

Displays fields available for querying a given data source.

* ``having=EXPRESSION``: A ``having`` expression to use for filtering displayed
  results.  The provided fields for filtering are ``id``, ``type``,
  ``description``, and ``raw``.
* ``SEARCH_TERM``: A search term to use for filtering results.  The term
  is case-insensitive and must be present in either the function name or
  description to be displayed.

`jira-select run-script FILENAME [ARGS...]`
-------------------------------------------

Executes the ``main(**kwargs)`` function in the specified filename,
passing it two keyword arguments:

* ``args``: An array of extra arguments.
* ``cmd``: The command class (via which you can access configuration,
  your jira instance, and other utilities).

This function is intended for use in ad-hoc scripting needs.
If you are the sort of person to be running complex queries
against your Jira instance,
you're also likely to be the sort of person who
will occasionally write an import script
for ingesting issues into Jira.
This utility function allows you to do that more easily
by letting you lean on the Jira settings
you've already configured jira-select to use.

.. important::

   If you want to future-proof your script, be sure that the signature
   of your ``main`` function accepts ``**kwargs`` even if your signature
   already captures ``args`` and ``cmd`` explicitly.  New keyword
   arguments may be added at any time.

Example contenst of a user script named ``my_file.py``:

.. code-block:: python

   def main(args, cmd, **kwargs):
      print(f"Extra args: {args}")
      print(cmd.jira)

Running this file with::

   jira-select run-script my_file.py --extra --args

Will print::

   Extra args: ['--extra', '--args']
   <jira.client.JIRA object at 0x7fc0a47e7e80>
