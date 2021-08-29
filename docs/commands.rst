Command-Line
============

`jira-select shell [--editor-mode=MODE] [--disable-progressbars] [--output=PATH] [--format=FORMAT] [--launch-default-viewer]`
-----------------------------------------------------------------------------------------------------------------------------

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
* ``--disable-progressbars``: By defualt, a pretty progressbar is displayed to
  provide an indication of how long you might have to wait for results.  Using
  this option will disable this progressbar.
* ``--output=PATH``: Instead of writing output to a temporary file, write output
  to the specified file path.  This is useful if you're using the
  ``--launch-default-viewer`` option to work around OS-level security limits
  around what processes can read temporary files.
* ``--format=FORMAT``: By default, the output is generated in ``json`` format,
  but you can select a different output format by setting ``FORMAT`` to
  ``csv``, ``html``, ``table`` or ``json``.
* ``--launch-default-viewer``: Display the generated output in your system's default
  viewer for the relevant filetype.  You may need to use this argument if you are
  running on an operating system in which Visidata is not available
  (e.g. Windows when not running under Windows Subsystem for Linux).

.. _run subcommand:

`jira-select run FILENAME [--format=FORMAT] [--output=PATH] [--view] [--launch-default-viewer]`
-----------------------------------------------------------------------------------------------

Executes query specified in FILENAME and returns results in the specified format.

* ``--format=FORMAT``: Sets the output format; options include ``json`` (default)
  ``csv``, ``html` and ``table``.
* ``--output=PATH``: Sets the output path.  If unspecified, the output
  will be written to stdout.
* ``--view``: Open the appropriate viewer to view your query results after
  the query has completed.
* ``--launch-default-viewer``: Display the generated output in your system's default
  viewer for the relevant filetype.

`jira-select install-user-script SCRIPT [--overwrite] [--name]`
---------------------------------------------------------------

Installs a python script into your user scripts directory.
User scripts can be used to extend the functionality of jira-select
by letting you write functions that can be available during your
query operation.  See :ref:`Direct Registration` for more information
about how to use this.

* ``SCRIPT``: Path to the python script (or ``-`` to import from stdin)
  to add to your user scripts directory.
* ``--overwrite``: By default, an error will be returned if your query
  script matches the name of an existing script.  Use this command-line
  argument if you would like to overwrite a script having the same name.
* ``--name``: By default, the name will match the incoming filename
  (if it's available).  Use this to override that behavior.

`jira-select build-query [--output=PATH]`
----------------------------------------------------

Allows you to interactively generate a query definition file.

* ``--output=PATH``: Sets the output path.  If unspecified, the output
  will be written to stdout.

`jira-select configure`
-----------------------

Allows you to interactively configure jira-select to connect
to your Jira instance.

`jira-select setup-instance`
----------------------------

Configures an instance via the standard command-line arguments.
See ``--help`` for more information.
This is intended to be used programmatically;
if you are a human, you probably want to use ``configure`` instead.

`jira-select --instance-name=NAME remove-instance`
--------------------------------------------------

Removes configuration for the instance having the specified name.

`jira-select show-instances [--json]`
-------------------------------------

Displays for you which instances are currently configured for use with jira-select.

* ``--json``: Instead of displaying results in a pretty-printed table,
  export the results as json.

`jira-select store-password USERNAME`
-------------------------------------

Allows you to store a password for USERNAME in your system keychain.

* ``USERNAME``: The username to store a password for.

.. _functions subcommand:

`jirafs-select functions [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]]`
------------------------------------------------------------------------------

Displays functions available for use in a query.

* ``--having=EXPRESSION``: A ``having`` expression to use for filtering displayed
  results.  The provided fields for filtering are ``name`` and ``description``.
* ``SEARCH_TERM``: A search term to use for filtering results.  The term
  is case-insensitive and must be present in either the function name or
  description to be displayed.

.. _schema subcommand:

`jira-select schema [issues|boards|sprints] [--having=EXPRESSION] [SEARCH_TERM [SEARCH_TERM...]] [--json]`
----------------------------------------------------------------------------------------------------------

Displays fields available for querying a given data source.

* ``--having=EXPRESSION``: A ``having`` expression to use for filtering displayed
  results.  The provided fields for filtering are ``id``, ``type``,
  ``description``, and ``raw``.
* ``SEARCH_TERM``: A search term to use for filtering results.  The term
  is case-insensitive and must be present in either the function name or
  description to be displayed.
* ``--json``: Instead of displaying results in a pretty-printed table,
  export the results as json.

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
