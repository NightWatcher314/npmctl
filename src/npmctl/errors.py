class NpmctlError(Exception):
    """Base error for npmctl."""

class ConfigError(NpmctlError):
    pass

class ApiError(NpmctlError):
    pass

class NotFoundError(NpmctlError):
    pass
