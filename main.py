"""Entrypoint script to run the FastAPI app with a simple `python main.py` command.

This is useful for hosting platforms that expect a Python command rather than
an external uvicorn invocation. It uses `uvicorn.run()` programmatically and
reads `PORT` from the environment. In development you can still run
`uvicorn app.main:app --reload`.
"""
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    # In production, do not enable reload. Reloader can be used locally if desired.
    uvicorn.run('app.main:app', host=host, port=port, reload=False)
