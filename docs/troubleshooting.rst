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
