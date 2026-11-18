"""Keep automated tests isolated from developer and production databases.
Never let tests silently insert demo users and events into PostgreSQL.
"""
import atexit
import os
import shutil
import tempfile
from pathlib import Path

# Set BEFORE pytest imports backend.fullstack, whose local database is initialized on import.
if not os.environ.get('LOGSCOPE_ALLOW_EXTERNAL_TEST_DB'):
    _TEMP_PATH=Path(tempfile.mkdtemp(prefix='logscope_pytest_'))
    os.environ['LOGSCOPE_DATABASE_URL']='sqlite:///'+str(_TEMP_PATH/'qa.sqlite3')
    os.environ['LOGSCOPE_DEMO_MODE']='1'
    os.environ['LOGSCOPE_DEMO_PASSWORD']='Demo2026!'
    atexit.register(shutil.rmtree,_TEMP_PATH,ignore_errors=True)
