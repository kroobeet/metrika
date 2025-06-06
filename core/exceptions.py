class MetrikaError(Exception):
    """Base exception class for Metrika related errors."""
    pass


class MetrikaApiError(MetrikaError):
    """Exception for API related errors."""
    pass


class ConfigError(MetrikaError):
    """Exception for configuration related errors."""
    pass


class DataProcessingError(MetrikaError):
    """Exception for data processing related errors."""
    pass


class ExcelExportError(MetrikaError):
    """Exception for Excel export related errors."""
    pass
