Query Lifecycle
===============

.. mermaid::

   graph LR
        req([Request])
        req-->where
        subgraph Remote
            where-->order_by
        end
        subgraph Local
            order_by-->group_by
            group_by-->having
            having-->sort_by
            sort_by-->select
        end
        result([Display])
        select-->result

Jira-select queries are evaluated in many steps across two phases:

* Remote

  * JQL Query (``where`` and ``order_by``)

* Local

  * Grouping (``group_by``)
  * Filtering (``having``)
  * Sorting (``sort_by``)
  * Rendering results (``select``)

The steps in the "Remote" section are accomplished entirely by Jira
and thus are limited to the capabilities of JQL.

The steps in the "Local" section are accomplished on your local machine
by Jira-select, and thus can use custom functions.
