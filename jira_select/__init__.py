import pkg_resources

try:
    __version__ = pkg_resources.require("jira-select")[0].version
except Exception:
    __version__ = "unknown"
