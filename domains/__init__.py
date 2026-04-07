"""Auto-import all domain plugins to trigger DomainRegistry.register() calls.

Importing this package ensures all three domains are registered:
  - email_triage
  - traffic_control
  - customer_support
"""

from . import email_triage        # noqa: F401
from . import traffic_control     # noqa: F401
from . import customer_support    # noqa: F401
