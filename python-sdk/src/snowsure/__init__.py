"""snowsure — Python SDK for SnowSure live ski & snow data (https://www.snowsure.ai)."""

from snowsure.client import DEFAULT_BASE_URL, SnowSureClient, SnowSureError

__version__ = "0.1.0"

__all__ = ["SnowSureClient", "SnowSureError", "DEFAULT_BASE_URL", "__version__"]
