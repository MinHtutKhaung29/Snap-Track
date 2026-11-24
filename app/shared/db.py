from contextlib import contextmanager

import mysql.connector

from app.shared.config import settings


def connect():
    conn = mysql.connector.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        connection_timeout=10,
        autocommit=False,
    )
    cur = conn.cursor()
    cur.execute("SET time_zone = '+09:00'")
    cur.close()
    return conn


@contextmanager
def cursor(commit=False):
    conn = connect()
    cur = conn.cursor(dictionary=True)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def fetch_all(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql, params=()):
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=()):
    with cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.lastrowid


def health():
    row = fetch_one("SELECT VERSION() AS version, DATABASE() AS db")
    tables = fetch_all("SELECT table_name AS t FROM information_schema.tables WHERE table_schema = %s", (settings.db_name,))
    return {
        "version": row["version"],
        "db": row["db"],
        "tables": len(tables),
    }
