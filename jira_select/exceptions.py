class JiraCSVError(Exception):
    pass


class ConfigurationError(JiraCSVError):
    pass


class UserError(JiraCSVError):
    pass
