Troubleshooting
===============

After running a query, I see a message reading ``FileNotFoundError: [WinError 2] The system cannot find the file specified``
----------------------------------------------------------------------------------------------------------------------------

It looks like you're running this on windows!
The default viewer used for viewing results requires certain things that don't *by default* exist on windows,
but you can still use Jira-select -- you just need to install the "Windows Subsystem for Linux".  See more information here: `Windows Subsystem for Linux Installation Guide for Windows 10 <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.

If that's not an option,
you can still use ``jira-select`` to run queries directly with the :ref:`run subcommand`,
opening the generated CSV file in an app of your choice.

Sometimes filtering using ``having`` (or sorting using ``sort_by``) on a value I see in the output doesn't work; why not?
-------------------------------------------------------------------------------------------------------------------------

Oftentimes the data returned from Jira for a particular field
is not a simple string or number
and is instead a complex object full of other information.
In those cases, we show the most reasonable string value was can obtain
from the object instead of showing you the whole object.

To use such objects in ``having`` or ``sort_by`` expressions,
you should convert them into a reasonable simple data type
using one of the functions in :ref:`Types`.

If you're curious about which fields we're transforming
into strings behind-the-scenes,
try wrapping your column in ``type``
to see the data's actual type.

If you want to see the data that is being hidden
by the above transformations
-- for example: for ``issuetype`` --
you can access the raw Jira object via the ``raw`` property
of the field; e.g.

.. code-block:: yaml

   select:
   - issuetype.raw
   from: issues

I can't connect because my Jira instance uses a self-signed certificate
-----------------------------------------------------------------------

Don't worry,
there are two command-line arguments you can use
for configuring certificate verification:

* ``--disable-certificate-verification``: For the brave.  This will entirely
  disable certificate verification for this instance when configuring it
  as well as for all future connections to it.
* ``--certificate=/path/to/certificate``: For the people who have a
  security team watching what they're doing.  This will ask jira-select
  to use a particular self-signed certificate.

These are overrides available for all commands (not just ``configure``)
so these arguments can only be used
between ``jira-select`` and the command you're running
(probably only ``configure``
as when you use them with ``configure``
those settings will be recorded in your configuration's settings
for the future)::

  jira-select --disable-certificate-verification configure

When attempting to use a field's human readable name in curly braces, I get a Parse Error
-----------------------------------------------------------------------------------------

YAML, the file format we use for queries in jira-select,
has some parsing rules that will make it interpret a line starting with a
quote, curly brace, bracket, or other reserved characters
differently from other lines.

In cases like those,
you should just wrap your whole query expression in quotes;
for example:

.. code-block:: yaml

   select:
   - '{Story Points}'
   from: issues
