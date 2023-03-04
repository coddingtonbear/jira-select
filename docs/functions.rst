Query Functions
===============

Jira-select provides a long list of functions out-of-the-box, and you can
add your own if these are not enough.

Jira
----

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
           - {Story Points} as "Story Points"
         from: issues

   .. note::

      You will almost certainly want to provide the parameter named ``_``
      (an underscore) as the first argument to this function.
      Jira-select provides the raw row data to functions under this variable name.

   In Jira, custom fields are usually named something like ``customfield_10024``
   which is, for most people, somewhat difficult to remember.  You can use
   this function to get the field value for a field by its display name instead
   of its ID.

   Example:

   .. code-block:: yaml

      select
        - field_by_name(_, "Story Points") as "Story Points"
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
         - flatten_changelog(changelog)
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


Time Analysis
-------------

.. py:function:: workdays_in_state(changelog, state: str, start_hour: int = 9, end_hour: int = 17, timezone_name: str | None \ None, work_days: list[int] = [1, 2, 3, 4, 5], min_date: datetime.date = datetime.date(1, 1, 1), max_date: datetime.date = datetime.date(9999, 1, 1)) -> float

   Calculates how many "work days" your returned Jira issue was in a given state
   during the time period specified.

   As we all know, it's very difficult to get an actual understanding of how much
   time a given assignee has spent working on a given issue without asking them to
   track it directly, but this function intends to get us at least a reasonably
   good understanding of that by making some imperfect generalizations.

   .. note::

      A naive implementation of this function might use actual clock time, but
      consider the following two situations:

      - MYPROJECT-01 moves from "To Do" into "In Progress" at 4:55PM, just
        five minutes before the end of the day, then the next day moves
        from "In Progress" into "Done" at 9:05AM, five minutes after the
        beginning of the next day.
      - MYPROJECT-02 moves from "To Do" into "In Progress" at 10:00AM and
        in the same day from "In Progress" into "Done" at 4:00PM.

      Clearly, MYPROJECT-02 was being "worked on" for more time than
      MYPROJECT-01, but let's see how various algorithms might measure
      that time.

      If we use clock time:

      - MYPROJECT-01: 16.2h (81 times more than the actual working time)
      - MYPROJECT-02: 6h

      If we only measure time happening between 9A and 5P:

      - MYPROJECT-01: 0.2h (the actual working time)
      - MYPROJECT-02: 6h (the actual working time)

      Of course, this does introduce one inaccuracy that may, depending on
      how predicable your team's working hours are: time spent working on
      an issue outside of business hours isn't counted.

      If you would like to instead use clock time even knowing the
      distortions using that may create, you can do so by specifying
      a ``start_hour`` and ``end_hour`` of ``None``.

   .. note::

      You must use the ``expand`` option of ``changelog`` for Jira to
      return to you changelog information in your query; eg:

      .. code-block:: yaml

         select:
         - flatten_changelog(changelog)
         from: issues
         expand:
         - changelog

      If you do not provide the necessary ``expand`` option, this
      function will raise an error.

   Parameters:

   - ``state``: The name of the state you would like to count time for
     (e.g. "In Progress")
   - ``start_hour``: The work day starting hour.  Defaults to 9 (i.e. 9 AM)
   - ``end_hour``: The work day ending hour.  Defaults to 17 (i.e 5 PM)
   - ``timezone_name``: The timezone to interpret ``start_hour`` and
     ``end_hour`` in.
   - ``work_days``: The days of the week to count as work days; 0 = Sunday,
      1 = Monday... 6 = Saturday.
   - ``min_date``: The minmimum date to use when processing changelog entries.
     If an issue is in the relevant state at ``min_date`` at ``start_hour``,
     ``min_date`` and ``start_hour`` will be used for calculating the time range
     during which the issue was in the relevant state instead of using issue's
     actual time range in that state.
   - ``max_date``: The maximuim date to use when processing changelog entries.
     If an issue is in the relevant state at ``max_date`` at ``end_hour``,
     ``max_date`` and ``end_hour`` will be used for calculating the time range
     during which the issue was in the relevant state instead of using issue's
     actual time range in that state.

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

      select:
      - "*"
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
