Writing your own plugins
========================

Jira-select relies on setuptools entrypoints for determining what functions, commands, and formatters are available.
This makes it easy to write your own as long as you're familiar with python packaging,
and if you're not, you can also register functions at runtime.


Commands
--------

To write your own commands, you need to:

1. Create a class that is a subclass of ``jira_select.plugin.BaseCommand``.
   This command:

   - Must implement a ``handle`` function.

2. Register that class via a setuptools entrypoint.

   - Your entrypoint should be in the ``jira_select.commands`` section.
   - The name of your entrypoint will become the command's name.

.. autoclass:: jira_select.plugin.BaseCommand

   .. autoproperty:: config

   .. automethod:: save_config

   .. autoproperty:: options

   .. autoproperty:: console

   .. autoproperty:: jira

   .. automethod:: get_help

   .. automethod:: add_arguments

   .. automethod:: handle

Functions
---------

For functions, you have two choices:

1. You can create and install a user script into your user functions
   and within that script register a function using
   the method described in `Direct Registration` below.
3. If you plan to distribute your function on PyPI or would like for
   it to be installable generally, you can create an entrypoint;
   see `Entrypoint` below for details.

Direct Registration
~~~~~~~~~~~~~~~~~~~~

1. Create a function in a python file somewhere.
2. Wrapping that function in ``jira_select.plugin.register_function``.
3. Install that user script using the `install-user-script` command.

For example, if you have a file named ``my_user_function.py`` in your current directory with the following contents:

.. code-block:: python

   from jira_select.plugin import register_function


   @register_function
   def my_important_function(value):
      """Returns length of `value`

      This function isn't doing anything useful, really, but
      you could of course make it useful if you were to write
      your own.

      """
      return len(value)

you could install it with::

   jira-select install-user-function my_user_function.py

and after that, you will have access to ``my_important_function`` in a query like:

.. code-block:: yaml

   select:
   - my_important_function(key)
   from: issues

Entrypoint
~~~~~~~~~~

1. Create a class that is a subclass of ``jira_select.plugin.Function``.
   This command:

   - Must implement a ``__call__`` function.

2. Register that class via a setuptools entrypoint.

   - Your entrypoint should be in the ``jira_select.functions`` section.

.. autoclass:: jira_select.plugin.BaseFunction

   .. autoproperty:: jira

   .. automethod:: __call__

Formatters
----------

To write your own formatter, you need to:

1. Create a class that is a subclass of ``jira_select.plugin.BaseFormatter``.
   This command:

   - Must implement a ``writerow`` function.
   - Must implement a ``get_file_extension`` classmethod returning your
     format's file extension.
   - May implement an ``open`` method for any setup functionality.
   - May implement an ``close`` method for any teardown functionality.

2. Register that class via a setuptools entrypoint.

   - Your entrypoint should be in the ``jira_select.formatters`` section.

.. autoclass:: jira_select.plugin.BaseFormatter

   .. automethod:: get_file_extension

   .. autoproperty:: executor

   .. autoproperty:: stream

   .. automethod:: open

   .. automethod:: close

   .. automethod:: writerow
