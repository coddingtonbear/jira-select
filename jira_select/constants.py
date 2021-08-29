from typing import Dict
from typing import Optional

APP_NAME = "jira-select"


ENTRYPOINT_PREFIX = "jira_select"

COMMAND_ENTRYPOINT = f"{ENTRYPOINT_PREFIX}.commands"
SOURCE_ENTRYPOINT = f"{ENTRYPOINT_PREFIX}.sources"
FORMATTER_ENTRYPOINT = f"{ENTRYPOINT_PREFIX}.formatters"
FUNCTION_ENTRYPOINT = f"{ENTRYPOINT_PREFIX}.functions"


DEFAULT_INLINE_VIEWERS: Dict[str, Optional[str]] = {
    "csv": "vd",
    "json": "vd",
    "table": None,
}
