class JiraSelectError(Exception):
    pass


class ConfigurationError(JiraSelectError):
    pass


class UserError(JiraSelectError):
    pass
