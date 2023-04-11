Query Lifecycle
===============

.. mermaid::

   graph LR
     req([Request])
     req-->where
     subgraph Cacheable
       subgraph Remote
           where-->order_by
           order_by-->limit
       end
     end
     subgraph Local
       limit-->calculate
       calculate-->filt[filter]
       filt[filter]-->group_by
       group_by-->having
       having-->sort_by
       sort_by-->cap
       cap-->select
     end
     result([Display])
     select-->result

Jira-select queries are evaluated in many steps across two phases:

* Remote

  * JQL Query (``where``, ``order_by``, and ``limit``)

* Local

  * Calculating (``calculate``)
  * Filtering (``filter``)
  * Grouping (``group_by``)
  * Filtering (``having``)
  * Sorting (``sort_by``)
  * Capping count of results (``cap``)
  * Rendering results (``select``)

The steps in the "Remote" section are accomplished entirely by Jira
and thus are limited to the capabilities of JQL.
The result of this part of the query processor can be cached
by using the ``cache`` query parameter.

The steps in the "Local" section are accomplished on your local machine
by Jira-select, and thus can use custom functions.
