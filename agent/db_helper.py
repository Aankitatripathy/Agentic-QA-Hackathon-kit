import getpass
import os
import shutil
import subprocess
from pathlib import Path


def query_db(sql, timeout=20):
    mac_psql = Path(
        "/Applications/Postgres.app/Contents/Versions/16/bin/psql"
    )

    psql = os.getenv("QA_PSQL_PATH") or shutil.which("psql")

    if not psql and mac_psql.exists():
        psql = str(mac_psql)

    if not psql:
        raise RuntimeError(
            "PostgreSQL psql was not found. Install the PostgreSQL "
            "client or set QA_PSQL_PATH."
        )

    result = subprocess.run(
        [
            psql,
            "-h", os.getenv("QA_DB_HOST", "localhost"),
            "-p", os.getenv("QA_DB_PORT", "5433"),
            "-U", os.getenv("QA_DB_USER", getpass.getuser()),
            "-d", os.getenv("QA_DB_NAME", "demobank"),
            "-t", "-A",
            "-c", sql,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )

    return result.stdout.strip()
