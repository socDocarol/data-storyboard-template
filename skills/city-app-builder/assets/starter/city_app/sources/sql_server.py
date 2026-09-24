"""Optional Windows-authenticated reads from an existing SQL table or view."""

from __future__ import annotations

import re
from datetime import date

from .common import MAX_ROWS, SourceError, calendar_date, row_limit, validate_mapping

DRIVERS = ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server")
CONFIG_KEYS = {
    "kind",
    "server",
    "database",
    "table",
    "driver",
    "columns",
    "source",
    "date_from",
    "date_before",
    "date_format",
    "value_mode",
    "max_rows",
    "refresh_seconds",
}

# These are fixed SELECTs against metadata for this connection and one target.
# User configuration cannot supply statements, hooks, or additional predicates.
TARGET_CHECK = """SELECT CASE WHEN DB_ID(?) = DB_ID() THEN 1 ELSE 0 END, RTRIM(o.type),
IS_SRVROLEMEMBER('sysadmin'), IS_ROLEMEMBER('db_owner')
FROM sys.objects AS o
INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
WHERE s.name = ? AND o.name = ? AND o.is_ms_shipped = 0"""
PERMISSION_CHECK = """SELECT 'SERVER', permission_name FROM sys.fn_my_permissions(NULL, 'SERVER')
UNION ALL SELECT 'DATABASE', permission_name FROM sys.fn_my_permissions(NULL, 'DATABASE')
UNION ALL SELECT 'SCHEMA', permission_name FROM sys.fn_my_permissions(?, 'SCHEMA')
UNION ALL SELECT 'OBJECT', permission_name FROM sys.fn_my_permissions(?, 'OBJECT')"""
COLUMN_CHECK = """SELECT c.name,
HAS_PERMS_BY_NAME(?, 'OBJECT', 'SELECT', c.name, 'COLUMN'),
HAS_PERMS_BY_NAME(?, 'OBJECT', 'UPDATE', c.name, 'COLUMN')
FROM sys.columns AS c WHERE c.object_id = OBJECT_ID(?)"""
READ_PERMISSIONS = {
    "SERVER": {
        "CONNECT SQL",
        "CONNECT ANY DATABASE",
        "SELECT ALL USER SECURABLES",
        "VIEW ANY DATABASE",
        "VIEW ANY DEFINITION",
        "VIEW SERVER STATE",
        "VIEW SERVER PERFORMANCE STATE",
        "VIEW SERVER SECURITY STATE",
        "VIEW ANY SECURITY DEFINITION",
        "VIEW ANY PERFORMANCE DEFINITION",
    },
    "DATABASE": {
        "CONNECT",
        "SELECT",
        "VIEW DEFINITION",
        "VIEW DATABASE STATE",
        "VIEW DATABASE PERFORMANCE STATE",
        "VIEW DATABASE SECURITY STATE",
        "VIEW SECURITY DEFINITION",
        "VIEW PERFORMANCE DEFINITION",
        "VIEW ANY COLUMN ENCRYPTION KEY DEFINITION",
        "VIEW ANY COLUMN MASTER KEY DEFINITION",
    },
    "SCHEMA": {
        "SELECT",
        "VIEW DEFINITION",
        "VIEW SECURITY DEFINITION",
        "VIEW PERFORMANCE DEFINITION",
    },
    "OBJECT": {
        "SELECT",
        "VIEW DEFINITION",
        "VIEW SECURITY DEFINITION",
        "VIEW PERFORMANCE DEFINITION",
    },
}
SQL_NAME = r"\[[A-Za-z_][A-Za-z0-9_]{0,127}\]"
DATA_SELECT = re.compile(
    rf"SELECT TOP \((?P<limit>[1-9][0-9]{{0,4}})\) {SQL_NAME}(?:, {SQL_NAME})* "
    rf"FROM {SQL_NAME}\.{SQL_NAME}(?: WHERE {SQL_NAME} (?:>=|<) \?(?: AND {SQL_NAME} < \?)?)? "
    rf"ORDER BY {SQL_NAME}"
)


class ReadOnlyViolation(SourceError):
    """A SQL safety check refused access, including an unverifiable result."""


def _settings(config: dict) -> None:
    if not isinstance(config, dict) or set(config) - CONFIG_KEYS:
        raise ReadOnlyViolation(
            "SQL uses your Windows account and accepts only documented source settings. Raw SQL, credentials, connection overrides, hooks, and safety bypass options are not allowed."
        )
    if config.get("driver") is not None and config["driver"] not in DRIVERS:
        raise SourceError(
            "Choose an installed Microsoft ODBC Driver 18 or 17 for SQL Server."
        )
    for key in ("server", "database"):
        value = config.get(key, "")
        if (
            not isinstance(value, str)
            or len(value) > 255
            or any(ord(char) < 32 or char in ";{}=" for char in value)
        ):
            raise ReadOnlyViolation(
                f"SQL {key} must be a plain name, not connection-string options."
            )


def _driver(config: dict, available: list[str]) -> str | None:
    requested = config.get("driver")
    return next(
        (
            name
            for name in DRIVERS
            if name in available and (requested is None or requested == name)
        ),
        None,
    )


def connection_string(config: dict, available: list[str]) -> str:
    """Build trusted authentication; source text cannot add ODBC options."""
    _settings(config)
    if any(not config.get(key, "").strip() for key in ("server", "database")):
        raise SourceError(
            "Set server and database in the private SQL configuration. Your Windows account supplies authentication."
        )
    driver = _driver(config, available)
    if driver is None:
        raise SourceError(
            "No supported SQL ODBC driver is available to this Python environment. Ask IT about an approved Driver 18 or 17; the app does not install system drivers."
        )

    def quoted(value):
        return "{" + value.strip().replace("}", "}}") + "}"

    return (
        f"Driver={quoted(driver)};Server={quoted(config['server'])};Database={quoted(config['database'])};"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;ApplicationIntent=ReadOnly;"
    )


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]{0,127}", value
    ):
        raise ReadOnlyViolation(
            "Use plain SQL identifiers for the view and column mapping, not SQL expressions."
        )
    return f"[{value}]"


def select_query(config: dict) -> tuple[str, tuple]:
    _settings(config)
    validate_mapping(config)
    table = config.get("table", "")
    if not isinstance(table, str):
        raise ReadOnlyViolation("table must name one existing local table or view.")
    parts = table.split(".")
    if len(parts) != 2:
        raise ReadOnlyViolation(
            "table must name an existing approved schema.table or schema.view."
        )
    view = ".".join(_identifier(part) for part in parts)
    columns = config["columns"]
    selected = ", ".join(
        _identifier(column)
        for column in dict.fromkeys(columns.values())
        if column is not None
    )
    clauses, parameters = [], []
    for key, operator in (("date_from", ">="), ("date_before", "<")):
        if config.get(key):
            try:
                parameters.append(calendar_date(config[key]))
            except (ValueError, TypeError) as error:
                raise SourceError("SQL date bounds must be ISO dates.") from error
            clauses.append(f"{_identifier(columns['date'])} {operator} ?")
    query = f"SELECT TOP ({row_limit(config) + 1}) {selected} FROM {view}"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY " + _identifier(columns["record_id"])
    return query, tuple(parameters)


def _execute_read(cursor, query: str, parameters: tuple) -> None:
    """The sole execution path: fixed metadata reads or the exact data grammar."""
    if query in (TARGET_CHECK, PERMISSION_CHECK, COLUMN_CHECK):
        if len(parameters) != query.count("?") or any(
            not isinstance(value, str) for value in parameters
        ):
            raise ReadOnlyViolation("The SQL safety check received invalid parameters.")
    else:
        match = DATA_SELECT.fullmatch(query)
        if (
            not match
            or int(match["limit"]) > MAX_ROWS + 1
            or len(parameters) != query.count("?")
            or any(type(value) is not date for value in parameters)
        ):
            raise ReadOnlyViolation(
                "SQL execution refused: only the generated single-table SELECT is allowed."
            )
    cursor.execute(query, parameters)


def _verify_read_access(cursor, config: dict) -> None:
    schema, table = config["table"].split(".")
    _execute_read(cursor, TARGET_CHECK, (config["database"].strip(), schema, table))
    target = cursor.fetchmany(2)
    if len(target) != 1 or tuple(target[0]) not in ((1, "U", 0, 0), (1, "V", 0, 0)):
        raise ReadOnlyViolation(
            "Cannot verify a non-admin connection to the configured database and local user table/view. Owners/admins, synonyms, procedures, system objects, and cross-database targets are not allowed."
        )
    _execute_read(cursor, PERMISSION_CHECK, (schema, config["table"]))
    permissions = cursor.fetchmany(4097)
    if not permissions or len(permissions) > 4096:
        raise ReadOnlyViolation(
            "SQL read-only permissions could not be verified completely. No source rows were read."
        )
    seen = set()
    for row in permissions:
        if (
            len(row) != 2
            or row[0] not in READ_PERMISSIONS
            or row[1] not in READ_PERMISSIONS[row[0]]
        ):
            raise ReadOnlyViolation(
                "SQL access refused: the current Windows account has write, execute, administrative, or unrecognized permissions in the checked scopes. Ask IT to confirm read-only access for this source; the app will not change permissions."
            )
        seen.add(tuple(row))
    if (
        not {("SERVER", "CONNECT SQL"), ("DATABASE", "CONNECT"), ("OBJECT", "SELECT")}
        <= seen
    ):
        raise ReadOnlyViolation(
            "SQL connect and SELECT permissions could not be verified. No source rows were read."
        )
    # Column grants can override a table-level DENY in SQL Server. Inspect the
    # current target only, and never infer column safety from table permissions.
    _execute_read(cursor, COLUMN_CHECK, (config["table"],) * 3)
    columns = cursor.fetchmany(4097)
    names = set()
    selected = {name for name in config["columns"].values() if name is not None}
    if not columns or len(columns) > 4096:
        raise ReadOnlyViolation(
            "SQL column permissions could not be verified completely."
        )
    for row in columns:
        if (
            len(row) != 3
            or not isinstance(row[0], str)
            or row[0] in names
            or row[1] not in (0, 1)
            or row[2] != 0
        ):
            raise ReadOnlyViolation(
                "SQL access refused: target column permissions are writable or could not be verified."
            )
        names.add(row[0])
        if row[0] in selected and row[1] != 1:
            raise ReadOnlyViolation(
                "SQL SELECT access is required for every mapped column."
            )
    if not selected <= names:
        raise ReadOnlyViolation(
            "SQL mapped columns could not be verified against the configured table/view."
        )


def doctor(config: dict) -> dict:
    """Check local prerequisites only. Never opens a database connection."""
    select_query(config)
    _settings(config)
    installed = True
    try:
        import pyodbc

        drivers = pyodbc.drivers()
    except ImportError:
        installed = False
        drivers = []
    return {
        "connection_attempted": False,
        "authentication": "Windows account running the app",
        "pyodbc_installed": installed,
        "selected_driver": _driver(config, drivers),
        "server_configured": bool(config.get("server", "").strip()),
        "database_configured": bool(config.get("database", "").strip()),
        "read_only_permissions_verified": False,
        "permission_check": "Required on every database fetch. Write/admin/execute or unknown permissions block the data query; there is no bypass option.",
        "remaining": "Reuse an installed ODBC Driver 18 or 17. Install requirements-sql.txt only in the app environment if needed; ask IT if no supported system driver is available. Set server, database, and an existing table/view your Windows account can read, then run connect.py check. No password or new database objects are required.",
    }


def read_rows(config: dict) -> list[dict]:
    query, parameters = select_query(config)
    _settings(config)
    try:
        import pyodbc
    except ImportError as error:
        raise SourceError(
            "Install requirements-sql.txt in the app's Python environment first, then run connect.py doctor. No system changes are made by the app."
        ) from error
    connection = None
    try:
        connection = pyodbc.connect(
            connection_string(config, pyodbc.drivers()),
            timeout=15,
            readonly=True,
            autocommit=False,
        )
        connection.timeout = 15
        cursor = connection.cursor()
        try:
            try:
                _verify_read_access(cursor, config)
            except pyodbc.Error as error:
                raise ReadOnlyViolation(
                    "SQL read-only permissions could not be verified. No source rows were read; ask IT to check the source and Windows account."
                ) from error
            _execute_read(cursor, query, parameters)
            headers = [column[0] for column in cursor.description]
            rows = cursor.fetchmany(row_limit(config) + 1)
            if len(rows) > row_limit(config):
                raise SourceError(
                    "The SQL source exceeds max_rows. Narrow the date range or choose a smaller existing source."
                )
            return [dict(zip(headers, row)) for row in rows]
        finally:
            try:
                cursor.close()
            except pyodbc.Error as error:
                raise ReadOnlyViolation(
                    "SQL cursor cleanup could not be confirmed. The read was refused."
                ) from error
    except SourceError:
        raise
    except pyodbc.Error as error:
        raise SourceError(
            "SQL Server could not be read. Check the work network/VPN, driver, trusted certificate, and your Windows account's existing read access to the table/view."
        ) from error
    finally:
        if connection is not None:
            try:
                try:
                    connection.rollback()
                finally:
                    connection.close()
            except pyodbc.Error as error:
                raise ReadOnlyViolation(
                    "SQL rollback/connection cleanup could not be confirmed. The read was refused."
                ) from error
