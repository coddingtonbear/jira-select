Functions
=========

Jira-select provides a long list of functions out-of-the-box, and you can
add your own if these are not enough.

Jira
----

.. py:function:: sprint_name(sprint_id: int) -> Optional[str]

   Returns the name of the sprint matching the provided ID.

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
