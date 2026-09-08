import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test_feedify.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["FEEDIFY_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["FEEDIFY_PUBLIC_BASE_URL"] = "http://testserver"
