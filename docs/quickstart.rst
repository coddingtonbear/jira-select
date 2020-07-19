Quickstart
==========

First, you need to configure `jira-csv` to connect to your jira instance::

   jira-csv configure

Follow the displayed instructions, then, you can open up your shell::

   jira-csv shell

From here, you can type out a jira-select query (See :ref:`Query Format` for details).
The format is inspired by SQL, but isn't quite the same.
The following example will return to you a table showing you which issues are assigned to you.

.. code-block:: yaml

    select:
    - key
    - summary
    from: issues
    where:
    - assignee = "your-email@somecompany.com"
    - resolution is null

The editor uses `vi` bindings by default; so once you're ready to submit
your query, press `Esc` followed by `Enter` and after a short wait (watch the progressbars), you'll be shown your results. Press `q` to exit your results.

See the built-in help (`--help`) for more options.