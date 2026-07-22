"""
ASGI entry point for the AstroPitch Prediction API.

The service lives in 24_api.py, but a module name can't start with a digit, so
uvicorn/gunicorn can't import it as `24_api:app`. This shim loads it by path and
re-exports `app`, so deployment targets can use the standard `app:app` string:

    uvicorn app:app --host 0.0.0.0 --port $PORT
"""
import os
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
# engine .pkl files are loaded by 24_api.py with relative paths, so run from here
os.chdir(_HERE)

_spec = importlib.util.spec_from_file_location("astropitch_api",
                                               os.path.join(_HERE, "24_api.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

app = _m.app
