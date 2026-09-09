"""Read-only access to a SQLite file, with the limits enforced by SQLite.

The guarantee is not "we checked the SQL and it looked like a SELECT". It is
that the connection is opened read-only *and* an authorizer callback vetoes
every action that is not a read. Both are the database's own machinery, so a
query shape nobody anticipated is still refused, and there is no pattern to
outwit.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# The only actions a read-only server has any business permitting.
_READ_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }
)

# PRAGMA is one action covering everything from `table_info` to `journal_mode`,
# so it cannot be allowed wholesale. Only the introspection pragmas `schema`
# needs are named here; deny-by-default handles the rest.
_READ_PRAGMAS = frozenset({"table_info"})


class Refused(Exception):
    """A request the guards declined, carrying which guard produced it.

    CONVENTIONS rule 5: a non-obvious status says which probe produced it. A
    caller -- or a model -- can branch on `guard` without parsing prose.
    """

    def __init__(self, guard: str, reason: str) -> None:
        super().__init__(reason)
        self.guard = guard
        self.reason = reason


@dataclass(frozen=True, slots=True)
class QueryResult:
    """What a query returned, and what it cost to find out.

    `truncated` and `elapsed_ms` are the evidence half: a caller that cannot see
    the cap has no way to know its answer is partial, and a model that cannot
    see the cost has no way to economise.
    """

    columns: list[str]
    rows: list[tuple] = field(default_factory=list)
    truncated: bool = False
    row_limit: int = 0
    elapsed_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class Column:
    name: str
    type: str
    nullable: bool
    primary_key: bool


@dataclass(frozen=True, slots=True)
class Table:
    name: str
    columns: list[Column]


class ReadOnlyDatabase:
    """A SQLite file that can be read and cannot be written.

    `allowed_tables` narrows what is visible. Left as None, every table in the
    file is readable; given a list, anything else is refused by the authorizer
    before a row is touched.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        max_rows: int = 100,
        allowed_tables: Iterable[str] | None = None,
    ) -> None:
        self.path = Path(path)
        self.max_rows = max_rows
        self.allowed_tables = None if allowed_tables is None else frozenset(allowed_tables)

    # -- connection ---------------------------------------------------------

    def _connect(self) -> tuple[sqlite3.Connection, list[str]]:
        """Open read-only and install the authorizer.

        Returns the denials list alongside the connection: the authorizer can
        only answer OK or DENY, so it records *why* it said no and the caller
        turns that into the guard name.
        """
        denials: list[str] = []
        try:
            con = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        except sqlite3.OperationalError as exc:
            raise Refused(
                "unreadable-database", f"cannot open {self.path} read-only: {exc}"
            ) from exc
        con.set_authorizer(self._make_authorizer(denials))
        return con, denials

    def _make_authorizer(self, denials: list[str]):
        allowed = self.allowed_tables

        def authorize(action: int, arg1: str | None, *_rest: object) -> int:
            if action == sqlite3.SQLITE_PRAGMA:
                if arg1 in _READ_PRAGMAS:
                    return sqlite3.SQLITE_OK
                denials.append("not-read-only")
                return sqlite3.SQLITE_DENY
            if action not in _READ_ACTIONS:
                denials.append("not-read-only")
                return sqlite3.SQLITE_DENY
            # arg1 is the table being read. sqlite_master is how a client
            # discovers anything at all, so scoping must not hide it.
            if (
                action == sqlite3.SQLITE_READ
                and allowed is not None
                and arg1 is not None
                and arg1 not in allowed
                and not arg1.startswith("sqlite_")
            ):
                denials.append("table-not-allowed")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        return authorize

    @staticmethod
    def _guard_for(exc: sqlite3.DatabaseError, denials: list[str]) -> tuple[str, str]:
        if isinstance(exc, sqlite3.ProgrammingError) and "one statement" in str(exc):
            return "multiple-statements", (
                "only one statement may be sent at a time; a second statement cannot ride along"
            )
        if denials:
            # Last denial wins: it is the one that stopped execution.
            guard = denials[-1]
            reason = {
                "not-read-only": (
                    "this database is served read-only; the statement asked to change it"
                ),
                "table-not-allowed": "that table is outside the tables this server exposes",
            }[guard]
            return guard, reason
        return "rejected-by-database", f"the database refused this statement: {exc}"

    # -- reads --------------------------------------------------------------

    def query(self, sql: str) -> QueryResult:
        con, denials = self._connect()
        started = time.perf_counter()
        try:
            cur = con.execute(sql)
            # One row beyond the cap, so truncation is observed rather than guessed.
            rows = cur.fetchmany(self.max_rows + 1)
            columns = [d[0] for d in cur.description or []]
        except sqlite3.DatabaseError as exc:
            raise Refused(*self._guard_for(exc, denials)) from exc
        finally:
            con.close()

        return QueryResult(
            columns=columns,
            rows=rows[: self.max_rows],
            truncated=len(rows) > self.max_rows,
            row_limit=self.max_rows,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        )

    def schema(self) -> list[Table]:
        """Every table this server exposes, with its columns.

        Answered from SQLite's own metadata rather than from the data, which is
        the cheap half of most agent conversations and should stay cheap.
        """
        con, denials = self._connect()
        try:
            names = [
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            if self.allowed_tables is not None:
                names = [n for n in names if n in self.allowed_tables]
            tables = []
            for name in names:
                # PRAGMA takes no parameters, and `name` came from sqlite_master
                # rather than from a caller, so it cannot carry an injection.
                cols = [
                    Column(name=r[1], type=r[2] or "", nullable=not r[3], primary_key=bool(r[5]))
                    for r in con.execute(f"PRAGMA table_info('{name}')")
                ]
                tables.append(Table(name=name, columns=cols))
            return tables
        except sqlite3.DatabaseError as exc:
            raise Refused(*self._guard_for(exc, denials)) from exc
        finally:
            con.close()

    def sample(self, table: str, limit: int = 5) -> QueryResult:
        """A few rows from one table, for seeing shape rather than reading data.

        The table name is validated against the schema instead of interpolated,
        so this cannot become a second query path with weaker guards.
        """
        known = {t.name for t in self.schema()}
        if table not in known:
            raise Refused(
                "table-not-allowed",
                f"no table named {table!r} is exposed; call schema to see what is",
            )
        capped = max(1, min(limit, self.max_rows))
        return self.query(f'SELECT * FROM "{table}" LIMIT {capped}')
