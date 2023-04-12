Troubleshooting
===============

After running a query in jira-select's ``shell`` subcommand, the output results are printed directly to the screen instead of opening in a spreadsheet viewer
-------------------------------------------------------------------------------------------------------------------------------------------------------------

The viewer you see being used on in the demo gif is called `Visidata <https://www.visidata.org/>`_, and unfortunately it isn't available on all platforms.  You do have a few options, though:

1. You could use the ``--format=table`` command-line argument to tell jira-select to print your output to the screen in a fancy table mode.
2. You could ask jira-select to open the query results in your system's defualt viewer using the ``--launch-default-viewer`` command-line argument.  On Windows, you will also need to specify an output path explicitly to make this work by using ``--output=/some/path/to/write/output/to.csv``.
3. If you're running on Windows, you could install this under "Windows Subsystem for Linux" so that you can use the default viewer (visidata). See more information here: `Windows Subsystem for Linux Installation Guide for Windows 10 <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.
4. You could use the ``run-query`` subcommand instead of ``shell``.  This particular subcommand is a lot less fancy than ``shell``, though.

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
     Raw Issue Data: issuetype.raw
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
     Story Points: '{Story Points}'
   from: issues
