"""Deliberately incomplete fixture; no external service is contacted."""

import os

# TODO: add tests for greeting formatting.
# FIXME: document SERVICE_NAME in the environment template.
print(f"Hello from {os.getenv('SERVICE_NAME', 'demo')}")
