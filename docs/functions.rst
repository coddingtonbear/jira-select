Query Functions
===============

Jira-select provides a long list of functions out-of-the-box, and you can
add your own if these are not enough.

Jira
----

.. py:function:: get_issue(ticket_number: str) -> jira.resources.Issue

   Fetch a Jira issue by its issue key (e.g. ``MYPROJECT-1045``).

   This will return a ``jira.resources.Issue`` object; you can access
   most fields via its ``fields`` property, eg::

      get_issue(field_holding_issue_key).fields.summary

.. py:function:: get_issue_snapshot_on_date(issue: jira.resources.Issue) -> jira_select.types.IssueSnapshot:

   Reconstruct the state of an issue at a particular point in time
   using the issue's ``changelog``.

   You will want to pass the literal value ``issue`` as the first parameter of this function.
   Jira-select provides the ``jira.resources.Issue`` object itself under that name,
   and this function will use both that object and the changes recorded in the ``changelog`` field
   for getting an understanding of what the issue looked liked at a particular point in time.

   This function requires that you set the query ``expand`` option
   such that it includes ``changelog`` for this to work correctly --
   if you do not do that, this function will fail.

   .. code-block:: yaml

      select:
        snapshot: get_issue_snapshot_on_date(issue, parse_datetime('2022-01-01'))
      from: issues
      expand:
      - changelog

   The returned snapshot is *not* a ``jira.resources.Issue`` object,
   but instead a ``jira_select.types.IssueSnapshot`` object
   due to limitations around what kinds of data can be gathered
   from the snapshot information.
   The most important difference between a ``jira_select.types.IssueSnapshot`` and a ``jira.resources.Issue`` object is
   that the ``jira_select.types.IssueSnapshot`` object is
   a simple ``dict[str,str]`` object in which
   the value of the ``dict`` entries is always the ``str``-ified
   field value.

.. py:function:: sprint_name(sprint_blob: str) -> Optional[str]

   Shortcut for returning the name of a sprint via its ID.  Equivalent
   to calling ``sprint_details(sprint_blob).name``.

.. py:function:: sprint_details(sprint_blob: str) -> Optional[jira_select.functions.sprint_details.SprintInfo]

   Returns an object representing the passed-in sprint blob.

   Jira returns sprint information on an issue via strings looking something like::

      com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=MySprint,goal=Beep Boop,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436]

   This function will extract the information found in the above string
   into a ``jira_select.functions.sprint_details.SprintInfo`` object
   allowing you to access each of the following properties:

   * ``id``: Sprint ID number
   * ``state``: Sprint state
   * ``name``: Sprint name
   * ``startDate``: Sprint starting date (as datetime)
   * ``endDate``: Sprint ending date (as datetime)
   * ``completeDate``: Sprint completion date (as datetime)

.. py:function:: get_sprint_by_id(id: int) -> Optional[jira.resources.Sprint]

   This function will request the information for the sprint specified by
   ``id`` from your Jira server and return it as a ``jira.resources.Sprint``
   object.

.. py:function:: get_sprint_by_name(board_name_or_id: Union[str, int], sprint_name: str) -> Optional[jira.resources.Sprint]

   This function will request the information for the sprint matching
   the specified name and belonging to the specified board.  This will
   be returned as a ``jira.resources.Sprint`` resource.

.. _field_by_name function:

.. py:function:: field_by_name(row: Any, display_name: str) -> Optional[str]

   Returns value for field having the specified display name.

   .. note::

      You probably do not nee to use this function.
      We provide another, simpler, method for getting
      the value of a field by its human-readable name--
      just place the human-readable name in between
      curly braces in your query expression; eg:

      .. code-block::

         select
           Story Points: "{Story Points}"
         from: issues

   .. note::

      You will almost certainly want to provide the parameter named
      ``issue`` as the first argument to this function.
      Jira-select provides the raw row data to functions under this variable name.

   In Jira, custom fields are usually named something like ``customfield_10024``
   which is, for most people, somewhat difficult to remember.  You can use
   this function to get the field value for a field by its display name instead
   of its ID.

   Example:

   .. code-block:: yaml

      select
        - field_by_name(issue, "Story Points") as "Story Points"
      from: issues

.. py:function:: estimate_to_days(estimate_string: str, day_hour_count=8) -> Optional[float]

   Converts a string estimation (typically stored in ``timetracking.originalEstimate``)
   into an integer count of days.

   The ``timetracking.originalEstimate`` field contains values like ``1d 2h 3m``;
   using this function will transform such a value into ``1.25625``.

.. py:function:: flatten_changelog(changelog) -> List[jira_select.functions.flatten_changelog.ChangelogEntry]

   Converts changelog structure from your returned Jira issue into a
   flattened list of ``jira_select.functions.flatten_changelog.ChangelogEntry``
   instances.

   .. note::

      You must use the ``expand`` option of ``changelog`` for Jira to
      return to you changelog information in your query; eg:

      .. code-block:: yaml

         select:
           changelog: flatten_changelog(changelog)
         from: issues
         expand:
         - changelog

      If you do not provide the necessary ``expand`` option, this
      function will raise an error.

   Every member of the returned list has the following properties:

   * ``author`` (str): Author of the change
   * ``created`` (datetime.datetime): When the change took place
   * ``id`` (int): The ID of the changelog entry
   * ``field`` (str): The name of the field that was changed
   * ``fieldtype`` (str): The type of the field that was changed
   * ``fromValue`` (Optional[Any]): The original value of the field.  Note that
     the original Jira field name for this is ``from``.
   * ``fromString`` (Optional[str]): The original value of the field as a
     string.
   * ``toValue`` (Optional[Any]): The final value of the field.  Note that
     the original Jira field name for this is ``to`.
   * ``toString`` (Optional[str]): The final value of the field as a
     string.

   This returned list of records can be filtered with ``simple_filter``
   to either find particular entries or filter out rows that do not
   have an entry having particular characteristics.


Subquery
--------

.. py:function:: subquery(subquery_name, **params) -> Any:

   Runs a subquery by name with the provided parameters.

   For example: you can get the time intervals during which an issue
   and its associated subtasks were in the "In Progress" status with
   a query like so:

   .. code-block:: yaml

      select:
        self_and_child_intervals_in_progress: interval_matching(issue, status="In Progress") | union(subquery("children", key=issue.key))
      from: issues
      subqueries:
         children:
            select:
              in_progress_intervals: interval_matching(issue, status='In Progress')
            from: issues
            where:
            - parent = "{params.key}"
            expand:
            - changelog
      expand:
      - changelog

   Your specified ``**params`` will become available to the subquery via ``{params.*}``;
   in the above example, ``{params.key}`` will be set to the value of the outer query's
   ``issue.key``.

   Unless specifically specified,
   a subquery will use the same cache settings as the parent query.

   .. warning::

      If you would like your subquery's cache to be effective,
      only pass simple values in ``**params``.

      The string representation of an object is used for calculating cache
      keys, and many objects include information in their default
      string representations that vary between instantiations.
      If things like, for example, the memory address of an object appears in
      its string representation, the cache key will never match,
      and the cached value will not be used.

      A common way that this problem might occur is if you were to pass the
      entire ``issue`` object to the subquery.
      Instead of passing the entire ``issue`` object to the subquery,
      pass simple values from it as shown in the example above.

Time Analysis
-------------

.. py:function:: interval_matching(issue, **query_params: dict[str, Any]) -> portion.Interval

   See `simple_filter function` for information about how to specify ``query_params``.

   Will return an interval covering segments in which the provided issue
   matches the conditions specified by ``query_params``.

   .. note::

      Contrary to what you might guess,
      a single `portion.Interval` object
      can represnt multiple ranges of time.

   Note that `portion.Interval` objects can be used with logical operations like `|`, `&`, and `-`.

.. py:function:: interval_size(interval: portion.Interval) -> datetime.timedelta

   For a provided interval, return the total amount of time that the interval's
   segments span.

.. py:function:: interval_business_hours(min_date: datetime.date | None = None, max_date: datetime.date | None = None, start_hour: int = 9, end_hour: int = 17, timezone_name: str | None = None, work_days: Iterable[int] = (1, 2, 3, 4, 5)) -> portion.Interval:

   Returns an interval having segments that correspond with the "business hours"
   specified by your paramters.

   This is particularly useful when used in conjunction with `interval_matching`
   and `interval_size` above for determining the amount of time an issue was
   actively in a particular state, for example:

   .. code-block:: yaml

      select:
        total_time_in_progress: interval_size(interval_matching(issue, status="In Progress") & interval_business_hours(parse_date(created)))
      from: issues

   This will find all segments of time during which the relevant issue was
   in the "In Progress" status during business hours, then return the
   amount of time that those segments spanned.

   .. note::

      A naive implementation of this sort of time analysis might use actual,
      raw clock time, but consider the following two situations:

      - MYPROJECT-01 moves from "To Do" into "In Progress" at 4:55PM, just
        five minutes before the end of the day, then the next day moves
        from "In Progress" into "Done" at 9:05AM, five minutes after the
        beginning of the next day.
      - MYPROJECT-02 moves from "To Do" into "In Progress" at 10:00AM and
        in the same day from "In Progress" into "Done" at 4:00PM.

      Clearly, MYPROJECT-02 was being "worked on" for more time than
      MYPROJECT-01, but let's see how various algorithms might measure
      that time.

      If we use raw clock time:

      - MYPROJECT-01: 16.2h (81 times more than the actual working time)
      - MYPROJECT-02: 6h

      If we only measure time happening between 9A and 5P:

      - MYPROJECT-01: 0.2h (the actual working time)
      - MYPROJECT-02: 6h (the actual working time)

      Of course, this does introduce one inaccuracy that may,
      depending on how predicable your team's working hours are,
      make this behavior undesirable:
      time spent working on an issue outside of business hours isn't counted.
      Typically, though,
      the amount of time an issue might be worked on outside those hours
      will be much smaller
      than the amount of excess time
      using raw clock time directly would count.

   - ``min_date``: The minimum date to add the business hours of to your interval.
     By default, 365 days before now.
   - ``max_date``: The (exclusive) maximum date to add the business hours of to
     your interval.  By default: tomorrow.
   - ``start_hour``: The work day starting hour.  Defaults to 9 (i.e. 9 AM)
   - ``end_hour``: The work day ending hour.  Defaults to 17 (i.e 5 PM)
   - ``timezone_name``: The timezone to interpret ``start_hour`` and
     ``end_hour`` in.
   - ``work_days``: The days of the week to count as work days; 0 = Sunday,
      1 = Monday... 6 = Saturday.

Data Traversal
--------------

.. _extract function:

.. py:function:: extract(field: Iterable[Any], dotpath: str) -> Iterable[Any]

   For every member of ``field``, walk through dictionary keys or object
   attributes described by ``dotpath`` and return all non-null results as
   an array.

   .. note::

      Although this will work,
      it is not necessary to use this for traversing into properties of
      grouped rows.  If your selected field is an object having a value
      you'd like to select, you can simply use dotpath traversal to reach
      the value you'd like.

   This function works for both dictionaries and objects.

.. _flatten_list function:

.. py:function:: flatten_list(field: List[List[Any]]) -> List[Any]

   For a list containing a lists of items, create a single list of
   items from the internal lists.

   The above is a little bit difficult to read, but in principle
   what this function does is convert values like::

      [[1, 2, 3], [4, 5, 6]]

   into a single list of the shape::

      [1, 2, 3, 4, 5, 6]

Dates
-----

.. py:function:: parse_datetime(datetime_string: str, *args, **kwargs) -> datetime.datetime

   Parse a date string into a datetime object.

   This relies on `python-dateutil`; there are many additional options available
   that you can find documented `here <https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse>`_.

.. py:function:: parse_date(date_string: str, *args, **kwargs) -> datetime.date

   Parse a date string into a date object.

   This relies on `python-dateutil`; there are many additional options available
   that you can find documented `here <https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse>`_.

Intervals
---------

.. py:function:: empty_interval() -> portion.Interval

.. py:function:: closed_interval() -> portion.Interval

.. py:function:: open_interval() -> portion.Interval

.. py:function:: openclosed_interval() -> portion.Interval

.. py:function:: closedopen_interval() -> portion.Interval

Json
----

.. py:function:: json_loads(json: str) -> Union[Dict, List]

   Parse a JSON string.

.. py:function:: json_dumps(obj: Union[Dict, List]) -> str

   Encode a dictionary or list into a JSON string.

Math
----

Basic
~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: abs(value: float) -> str

.. py:function:: max(values: List[Any]) -> Any

.. py:function:: min(values: List[Any]) -> Any

.. py:function:: pow(base: float, exponent: float, mod: Optional[int]) -> float

.. py:function:: round(value: float, ndigits: int = 0) -> float

.. py:function:: sum(values: List[Any]) -> Any

Averages & measures of central location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/statistics.html>`_.

.. py:function:: mean(values: List[Any]) -> Any

.. py:function:: fmean(values: List[Any]) -> float

   Requires Python 3.8

.. py:function:: geometric_mean(values: List[Any]) -> float

   Requires Python 3.8

.. py:function:: harmonic_mean(values: List[Any]) -> Any

.. py:function:: median(values: List[Any]) -> Any

.. py:function:: median_low(values: List[Any]) -> Any

.. py:function:: median_high(values: List[Any]) -> Any

.. py:function:: median_grouped(values: List[Any], interval: int = 1) -> Any

.. py:function:: mode(values: List[Any]) -> Any

.. py:function:: multimode(values: List[Any]) -> List[Any]

   Requires Python 3.8

.. py:function:: quantiles(values: List[Any], n=4, method=Literal["exclusive", "inclusive"]) -> Iterable[Iterable[Any]]

   Requires Python 3.8

Measures of spread
~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/statistics.html>`_.

.. py:function:: pstdev(values: List[Any], mu=Optional[float]) -> Any

.. py:function:: pvariance(values: List[Any], mu=Optional[float]) -> Any

.. py:function:: stdev(values: List[Any], xbar=Optional[float]) -> Any

.. py:function:: variance(values: List[Any], xbar=Optional[float]) -> Any


Numeric Representation
~~~~~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: bin(value: int) -> str

.. py:function:: hex(value: int) -> str

.. py:function:: oct(value: int) -> str

.. py:function:: ord(value: str) -> int

List Operations
---------------

.. py:function:: union(iterable: Iterable[X]) -> X

Types
-----

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: bool(value: Any) -> bool

.. py:function:: int(value: Any) -> int

.. py:function:: set(value: Any) -> set

.. py:function:: str(value: Any) -> str

.. py:function:: tuple(value: Any) -> tuple

.. py:function:: type(value: Any) -> str


Sorting
-------

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: reversed(iterable: List[Any]) -> Iterable[List[Any]]

.. py:function:: sorted(iterable: List[Any]) -> Iterable[List[Any]]

Filtering & Mapping
-------------------

.. _simple_filter function:

.. py:function:: simple_filter(iterable: Iterable[Any], **query_params: Dict[str, Any]) -> Iterable[Any]
.. py:function:: simple_filter_any(iterable: Iterable[Any], **query_params: Dict[str, Any]) -> Iterable[Any]

   These functions provide you with a simple way of filtering lists using
   a syntax reminiscent of Django's ORM query filter parameters.

   * ``simple_filter``: All provided ``query_params`` must match for the row
     to be returned.
   * ``simple_filter_any``: At least one provided param in ``query_params``
     must match for the row to be returned.

   For example; to find issues having become resolved between two dates,
   you could run a query like the following:

   .. code-block:: yaml

      select: "*"
      from: issues
      filter:
      - simple_filter(
            flatten_changelog(changelog),
            field__eq="resolution",
            toValue__ne=None,
            created__lt=parse_datetime("2020-02-02"),
            created__gt=parse_datetime("2020-02-01"),
        )
      expand:
      - changelog

   Consult the `documentation for QueryableList <https://github.com/kata198/QueryableList#user-content-operations>`_
   for information about the full scope of parameters available.

Python Builtin Functions
~~~~~~~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: filter(callable: Callable, Iterable[Any]) -> Iterable[Any]

.. py:function:: map(callable: Callable, Iterable[Any]) -> Iterable[Any]

Logic Shortcuts
---------------

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: all(iterable: List[Any]) -> bool

.. py:function:: any(iterable: List[Any]) -> bool

Counting
--------

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: len(iterable: List[Any]) -> int

   You might be tempted to use ``count()`` given how we share many
   patterns with SQL, but *this* is what you actually want to use.

Ranges
------

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: range(stop: int) -> Iterable[int]
.. py:function:: range(start: int, stop: int) -> Iterable[int]
.. py:function:: range(start: int, stop: int, step: int) -> Iterable[int]

Random
------

See more in information in `Python's Documentation <https://docs.python.org/3/library/random.html>`_.

.. py:function:: random() -> float

.. py:function:: randrange(stop: int) -> int
.. py:function:: randrange(start: int, stop: int) -> int
.. py:function:: randrange(start: int, stop: int, step: int) -> int

.. py:function:: randint(low: int, high: int) -> int

.. py:function:: choice(Sequence[Any]) -> Any
