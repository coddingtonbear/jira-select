class JiraSelectError(Exception):
    pass


class ConfigurationError(JiraSelectError):
    pass


class UserError(JiraSelectError):
    pass


class QueryError(UserError):
    pass


class FieldNameError(QueryError):
    pass
