Functions
=========

Jira-select provides a long list of functions out-of-the-box, and you can
add your own if these are not enough.

Jira
----

.. py:function:: sprint_name(sprint_blob: str) -> Optional[str]

   Shortcut for returning the name of a sprint via its ID.  Equivalent
   to calling ``sprint_details(sprint_blob).name``.

.. py:function:: sprint_details(sprint_blob: str) -> Optional[jira.resources.Sprint]

   Returns a Sprint object representing the passed-in sprint blob.

   Jira returns sprint information on an issue via strings looking something like::

      com.atlassian.greenhopper.service.sprint.Sprint@14b1c359[id=436,rapidViewId=153,state=CLOSED,name=MySprint,goal=Beep Boop,startDate=2020-03-09T21:53:07.264Z,endDate=2020-03-23T20:53:00.000Z,completeDate=2020-03-23T21:08:29.391Z,sequence=436

   This function will extract the sprint's ID number from the string and
   request the sprint's details from the Jira API, returning them to you
   as a ``jira.resources.Sprint`` object.

   Available properties include:

   * ``id``: Sprint ID number
   * ``self``: REST API URL
   * ``state``: Sprint state
   * ``name``: Sprint name
   * ``startDate``: Sprint starting date (as string)
   * ``endDate``: Sprint ending date (as string)
   * ``completeDate``: Sprint completion date (as string)
   * ``originBoardId``: The board to which this sprint belongs.


.. py:function:: field_by_name(row: Any, display_name: str) -> Optional[str]

   Returns value for field having the specified display name.

   .. note::

      You will almost certainly want to provide the parameter named ``_``
      as the first argument to this function.  Jira-select provides the
      raw row data under this variable name.

   In Jira, custom fields are usually named something like ``customfield_10024``
   which is, for most people, somewhat difficult to remember.  You can use
   this function to get the field value for a field by its display name instead
   of its ID.

   Example:

   .. code-block:: yaml

      select
        - field_by_name(_, "Story Points") as "Story Points"
      from: issues

Dates
-----

.. py:function:: parse_datetime(datetime_string: str) -> datetime.datetime

   Parse a date string into a datetime object.

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

.. py:function:: max(*values: Any) -> Any

.. py:function:: min(*values: Any) -> Any

.. py:function:: pow(base: float, exponent: float, mod: Optional[int]) -> float

.. py:function:: round(value: float, ndigits: int = 0) -> float

.. py:function:: sum(*values: Any) -> Any

Averages & measures of central location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/statistics.html>`_.

.. py:function:: mean(*values: Any) -> Any

.. py:function:: fmean(*values: Any) -> float

   Requires Python 3.8

.. py:function:: geometric_mean(*values: Any) -> float

   Requires Python 3.8

.. py:function:: harmonic_mean(*values: Any) -> Any

.. py:function:: median(*values: Any) -> Any

.. py:function:: median_low(*values: Any) -> Any

.. py:function:: median_high(*values: Any) -> Any

.. py:function:: median_grouped(*values: Any, interval: int = 1) -> Any

.. py:function:: mode(*values: Any) -> Any

.. py:function:: multimode(*values: Any) -> List[Any]

.. py:function:: quantiles(*values: Any, n=4, method=Literal["exclusive", "inclusive"]) -> Iterable[Iterable[Any]]

Measures of spread
~~~~~~~~~~~~~~~~~~

See more in information in `Python's Documentation <https://docs.python.org/3/library/statistics.html>`_.

.. py:function:: pstdev(*values: Any, mu=Optional[float]) -> Any

.. py:function:: pvariance(*values: Any, mu=Optional[float]) -> Any

.. py:function:: stdev(*values: Any, xbar=Optional[float]) -> Any

.. py:function:: variance(*values: Any, xbar=Optional[float]) -> Any


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


Logic Shortcuts
---------------

See more in information in `Python's Documentation <https://docs.python.org/3/library/functions.html>`_.

.. py:function:: all(iterable: List[Any]) -> bool

.. py:function:: any(iterable: List[Any]) -> bool

.. py:function:: len(iterable: List[Any]) -> int

   You might be tempted to use `count()` given how we share many
   patterns with SQL, but _this_ is what you actually want to use.

.. py:function:: range(stop: int) -> Iterable[int]
.. py:function:: range(start: int, stop: int) -> Iterable[int]
.. py:function:: range(start: int, stop: int, step: int) -> Iterable[int]

.. py:function:: reversed(iterable: List[Any]) -> Iterable[List[Any]]

.. py:function:: sorted(iterable: List[Any]) -> Iterable[List[Any]]
