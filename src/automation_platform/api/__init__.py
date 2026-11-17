"""HTTP API for the automation platform."""

from .health import create_app

__all__ = ["create_app"]
