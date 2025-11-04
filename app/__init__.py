"""TrustBridge FastAPI package initializer.

Adding an __init__.py makes the `app` directory an importable package which
avoids ModuleNotFoundError on some hosting environments that rely on regular
packages (for example, Render or some WSGI setups).
"""

__all__ = ["main"]
