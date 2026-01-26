# UNTRUSTED CLI CODE
# Configuration and versioning for Vigil CLI

import os
from importlib.metadata import version, PackageNotFoundError

# Get version from package metadata (modern Python 3.10+ approach)
# Falls back to hardcoded version if package not installed
try:
    VERSION = version("vigil-cli")
except PackageNotFoundError:
    # Fallback for development or when package is not installed
    VERSION = "0.1.0"

# Service endpoint configuration
# Users can override with VIGIL_ENDPOINT environment variable
DEFAULT_ENDPOINT = "http://localhost:5000"
VIGIL_ENDPOINT = os.getenv("VIGIL_ENDPOINT", DEFAULT_ENDPOINT)

# Project ID (optional)
VIGIL_PROJECT_ID = os.getenv("VIGIL_PROJECT_ID", None)
