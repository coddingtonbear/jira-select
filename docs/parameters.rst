Query Parameters
================

When writing some queries that you'd like to reuse later,
you may find a reason to want to pass-in a parameter at query runtime
instead of altering the query directly.
You can use query parameters for that.

For a contrived example,
the below query will require that you specify
a query parameter ``project`` that will
be used when interpreting the query.

.. code-block:: yaml

   select:
     Issue Key: key
   from: issues
   where:
   - project = "{params.project}"
   - updated > "2023-01-01"

.. note::

   See the "Can use query parameters?" section
   of :ref:`Query Structure Overview`
   for information about where these may be used.

You can specify the parameters to use
via the ``--param`` command-line argument like so::

    jira-select run-query --param="project=MYPROJECT" my-query.yaml
