"""SQLite database layer for kgshred.

Provides schema management, CRUD operations, and FTS5 search.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy import typing as npt

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Current schema version
SCHEMA_VERSION = 4


class DatabaseError(Exception):
    """Raised when database operations fail."""

    pass


class DocumentExistsError(Exception):
    """Raised when attempting to insert a document that already exists."""

    def __init__(self, doc_id: str, sha256_match: bool) -> None:
        self.doc_id = doc_id
        self.sha256_match = sha256_match
        if sha256_match:
            msg = f"Document '{doc_id}' already exists with same content"
        else:
            msg = f"Document '{doc_id}' exists with different content. Use --force to replace."
        super().__init__(msg)


@dataclass
class Document:
    """Represents a document in the database."""

    doc_id: str
    source_path: str
    sha256: str
    created_at: int
    raw: bytes


@dataclass
class Node:
    """Represents a node in the knowledge graph."""

    node_pk: int | None  # None for new nodes
    short_id: str
    full_id: str
    doc_id: str
    kind: str
    level: int | None = None
    title: str | None = None
    start: int = 0
    end: int = 0
    parent_node_pk: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """Represents an edge between nodes."""

    src_node_pk: int
    dst_node_pk: int
    edge_type: str
    weight: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Embedding:
    """Represents a vector embedding for a node."""

    embedding_pk: int | None  # None for new embeddings
    full_id: str
    model: str
    dimensions: int
    vector: npt.NDArray[np.float32]  # Use numpy array for memory efficiency
    created_at: int


@dataclass
class Collection:
    """Represents a collection (project, knowledgebase, etc.)."""

    collection_id: str
    kind: str  # 'project', 'knowledgebase', 'workspace', etc.
    name: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionMember:
    """Links a collection to a document or node."""

    collection_id: str
    member_type: str  # 'document' or 'node'
    member_pk: str  # doc_id or full_id


@dataclass
class Topic:
    """Represents a reusable topic/tag."""

    topic_id: str
    name: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TopicLink:
    """Links a topic to a document or node."""

    topic_id: str
    target_type: str  # 'document' or 'node'
    target_pk: str  # doc_id or full_id
    weight: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectSettings:
    """Stores project-specific default settings."""

    collection_id: str
    defaults: dict[str, Any] = field(default_factory=dict)


class Database:
    """SQLite database manager for kgshred."""

    def __init__(self, db_path: Path) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._vec_available: bool = False  # True if sqlite-vec extension is loaded
        logger.debug("Initializing database: %s", db_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            logger.debug("Creating new database connection")
            self._conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self._conn.row_factory = sqlite3.Row
            self._configure_pragmas()
            self._ensure_schema()
            logger.debug("Database connection established")
        return self._conn

    def _configure_pragmas(self) -> None:
        """Configure SQLite performance settings."""
        conn = self._conn
        if conn is None:
            return
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        logger.debug("Configured database pragmas (WAL, NORMAL sync, MEMORY temp store)")

        # Load sqlite-vec extension if available for fast vector search
        self._vec_available = self._load_vec_extension(conn)

    def _load_vec_extension(self, conn: sqlite3.Connection) -> bool:
        """Load sqlite-vec extension if available.

        Args:
            conn: SQLite connection.

        Returns:
            True if sqlite-vec was successfully loaded, False otherwise.
        """
        try:
            import sqlite_vec  # type: ignore

            try:
                sqlite_vec.load(conn)
                logger.info("Loaded sqlite-vec extension for fast vector search")
                return True
            except Exception as e:
                # Extension load failed (missing .so file, incompatible version, etc.)
                logger.debug("sqlite-vec extension load failed: %s", e)
                return False
        except ImportError:
            # sqlite-vec not installed
            logger.debug("sqlite-vec not installed, vector search will use fallback")
            return False

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._conn
        if conn is None:
            return

        # Schema version table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at INTEGER NOT NULL
            )
        """)

        # Check current version
        cur = conn.execute("SELECT MAX(version) FROM schema_version")
        row = cur.fetchone()
        current_version = row[0] if row[0] is not None else 0

        logger.debug("Current schema version: %d, target: %d", current_version, SCHEMA_VERSION)
        if current_version < SCHEMA_VERSION:
            self._apply_migrations(current_version)

    def _apply_migrations(self, from_version: int) -> None:
        """Apply schema migrations."""
        conn = self._conn
        if conn is None:
            return

        logger.info(
            "Applying schema migrations from version %d to %d", from_version, SCHEMA_VERSION
        )

        if from_version < 1:
            # Initial schema
            conn.executescript("""
                -- Documents table
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    raw BLOB NOT NULL
                );

                -- Nodes table
                CREATE TABLE IF NOT EXISTS nodes (
                    node_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_id TEXT UNIQUE NOT NULL,
                    full_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
                    kind TEXT NOT NULL,
                    level INTEGER,
                    title TEXT,
                    start INTEGER NOT NULL,
                    end INTEGER NOT NULL,
                    parent_node_pk INTEGER REFERENCES nodes(node_pk),
                    meta_json TEXT
                );

                -- Edges table
                CREATE TABLE IF NOT EXISTS edges (
                    src_node_pk INTEGER NOT NULL REFERENCES nodes(node_pk),
                    dst_node_pk INTEGER NOT NULL REFERENCES nodes(node_pk),
                    type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    meta_json TEXT,
                    PRIMARY KEY (src_node_pk, dst_node_pk, type)
                );

                -- FTS5 virtual table for full-text search (external content)
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_nodes USING fts5(
                    title,
                    text,
                    short_id UNINDEXED
                );

                -- Indexes
                CREATE INDEX IF NOT EXISTS idx_nodes_doc_id ON nodes(doc_id);
                CREATE INDEX IF NOT EXISTS idx_nodes_short_id ON nodes(short_id);
                CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_node_pk);
                CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_node_pk);
                CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
            """)

            # Record migration
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (1, int(time.time())),
            )
            conn.commit()
            logger.info("Schema migration to version 1 completed (initial schema)")

        if from_version < 2:
            # Add embeddings table for semantic search
            conn.executescript("""
                -- Embeddings table for vector storage
                CREATE TABLE IF NOT EXISTS embeddings (
                    embedding_pk INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    vector BLOB NOT NULL,
                    created_at INTEGER NOT NULL,
                    UNIQUE(full_id, model)
                );

                -- Indexes for embedding lookups
                CREATE INDEX IF NOT EXISTS idx_embeddings_full_id ON embeddings(full_id);
                CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);
            """)

            # Record migration
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (2, int(time.time())),
            )
            conn.commit()
            logger.info("Schema migration to version 2 completed (embeddings)")

        if from_version < 3:
            # Add collections, topics, and project settings tables
            conn.executescript("""
                -- Collections table (projects, knowledgebases, workspaces)
                CREATE TABLE IF NOT EXISTS collections (
                    collection_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL UNIQUE,
                    meta_json TEXT
                );

                -- Collection members (links collections to docs/nodes)
                CREATE TABLE IF NOT EXISTS collection_members (
                    collection_id TEXT NOT NULL REFERENCES collections(collection_id),
                    member_type TEXT NOT NULL,
                    member_pk TEXT NOT NULL,
                    PRIMARY KEY (collection_id, member_type, member_pk)
                );

                -- Topics table (reusable tags)
                CREATE TABLE IF NOT EXISTS topics (
                    topic_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    meta_json TEXT
                );

                -- Topic links (links topics to docs/nodes)
                CREATE TABLE IF NOT EXISTS topic_links (
                    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
                    target_type TEXT NOT NULL,
                    target_pk TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    meta_json TEXT,
                    PRIMARY KEY (topic_id, target_type, target_pk)
                );

                -- Project settings (per-collection defaults)
                CREATE TABLE IF NOT EXISTS project_settings (
                    collection_id TEXT PRIMARY KEY REFERENCES collections(collection_id),
                    defaults_json TEXT
                );

                -- Indexes
                CREATE INDEX IF NOT EXISTS idx_collections_kind
                    ON collections(kind);
                CREATE INDEX IF NOT EXISTS idx_collection_members_collection
                    ON collection_members(collection_id);
                CREATE INDEX IF NOT EXISTS idx_collection_members_member
                    ON collection_members(member_type, member_pk);
                CREATE INDEX IF NOT EXISTS idx_topic_links_topic
                    ON topic_links(topic_id);
                CREATE INDEX IF NOT EXISTS idx_topic_links_target
                    ON topic_links(target_type, target_pk);
            """)

            # Record migration
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (3, int(time.time())),
            )
            conn.commit()
            logger.info(
                "Schema migration to version 3 completed (collections, topics, project settings)"
            )

        if from_version < 4:
            # Add composite index on edges for type-optimized queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_edges_type_src_dst
                ON edges(type, src_node_pk, dst_node_pk)
                """
            )

            # Record migration
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (4, int(time.time())),
            )
            conn.commit()
            logger.info("Schema migration to version 4 completed (composite index on edges type)")

        logger.info("Schema migrations completed, current version: %d", SCHEMA_VERSION)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database transactions.

        Commits on success, rolls back on exception.

        Yields:
            Database connection.
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning("Transaction rolled back due to error: %s", e)
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            logger.debug("Closing database connection")
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Database:
        """Context manager entry.

        Returns:
            self
        """
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit - ensures connection is closed.

        Args:
            exc_type: Exception type if any
            exc_val: Exception value if any
            exc_tb: Exception traceback if any
        """
        self.close()

    def __del__(self) -> None:
        """Destructor - ensure connection is closed on garbage collection.

        This is a safety net but should not be relied upon.
        Always use close() explicitly or use as a context manager.
        """
        try:
            self.close()
        except Exception:  # noqa: S110
            # Ignore errors during cleanup in destructor
            # Logging here could cause issues during garbage collection
            pass

    # Document operations

    def insert_document(
        self,
        doc_id: str,
        source_path: str,
        raw: bytes,
        created_at: int | None = None,
    ) -> Document:
        """Insert a new document.

        Args:
            doc_id: Unique document identifier.
            source_path: Original file path.
            raw: Raw document content as bytes.
            created_at: Unix timestamp (defaults to now).

        Returns:
            The created Document.

        Raises:
            sqlite3.IntegrityError: If doc_id already exists.
        """
        if created_at is None:
            created_at = int(time.time())

        sha256 = hashlib.sha256(raw).hexdigest()

        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO documents (doc_id, source_path, sha256, created_at, raw)
                VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id, source_path, sha256, created_at, raw),
            )

        return Document(
            doc_id=doc_id,
            source_path=source_path,
            sha256=sha256,
            created_at=created_at,
            raw=raw,
        )

    def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID.

        Args:
            doc_id: Document identifier.

        Returns:
            Document if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT doc_id, source_path, sha256, created_at, raw FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return Document(
            doc_id=row["doc_id"],
            source_path=row["source_path"],
            sha256=row["sha256"],
            created_at=row["created_at"],
            raw=row["raw"],
        )

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its nodes, edges, and FTS entries.

        Args:
            doc_id: Document identifier.

        Returns:
            True if document was deleted, False if not found.
        """
        existing = self.get_document(doc_id)
        if existing is None:
            return False

        with self.transaction() as conn:
            # Get all node PKs for this document
            cur = conn.execute(
                "SELECT node_pk FROM nodes WHERE doc_id = ?",
                (doc_id,),
            )
            node_pks = [row["node_pk"] for row in cur.fetchall()]

            # Delete FTS entries
            for pk in node_pks:
                conn.execute("DELETE FROM fts_nodes WHERE rowid = ?", (pk,))

            # Delete edges (both directions)
            for pk in node_pks:
                conn.execute(
                    "DELETE FROM edges WHERE src_node_pk = ? OR dst_node_pk = ?",
                    (pk, pk),
                )

            # Delete nodes
            conn.execute("DELETE FROM nodes WHERE doc_id = ?", (doc_id,))

            # Delete document
            conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))

        return True

    def list_documents(self) -> list[Document]:
        """List all documents in the database.

        Returns:
            List of all Document objects.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT doc_id, source_path, sha256, created_at, raw FROM documents ORDER BY created_at"
        )
        return [
            Document(
                doc_id=row["doc_id"],
                source_path=row["source_path"],
                sha256=row["sha256"],
                created_at=row["created_at"],
                raw=row["raw"],
            )
            for row in cur.fetchall()
        ]

    def get_stats(self) -> dict[str, int | dict[str, int]]:
        """Get database statistics.

        Returns:
            Dictionary with counts: documents, nodes, edges, nodes_by_kind.
        """
        conn = self._get_connection()

        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        node_count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

        # Nodes by kind
        cur = conn.execute("SELECT kind, COUNT(*) as cnt FROM nodes GROUP BY kind ORDER BY kind")
        nodes_by_kind = {row["kind"]: row["cnt"] for row in cur.fetchall()}

        return {
            "documents": doc_count,
            "nodes": node_count,
            "edges": edge_count,
            "nodes_by_kind": nodes_by_kind,
        }

    # Node operations

    def insert_node(self, node: Node) -> Node:
        """Insert a new node.

        Args:
            node: Node to insert (node_pk should be None).

        Returns:
            Node with assigned node_pk.

        Raises:
            sqlite3.IntegrityError: If short_id or full_id already exists.
        """
        meta_json = json.dumps(node.meta) if node.meta else None

        with self.transaction() as conn:
            cur = conn.execute(
                """
                INSERT INTO nodes 
                (short_id, full_id, doc_id, kind, level, title, start, end, parent_node_pk, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.short_id,
                    node.full_id,
                    node.doc_id,
                    node.kind,
                    node.level,
                    node.title,
                    node.start,
                    node.end,
                    node.parent_node_pk,
                    meta_json,
                ),
            )
            node_pk = cur.lastrowid

        return Node(
            node_pk=node_pk,
            short_id=node.short_id,
            full_id=node.full_id,
            doc_id=node.doc_id,
            kind=node.kind,
            level=node.level,
            title=node.title,
            start=node.start,
            end=node.end,
            parent_node_pk=node.parent_node_pk,
            meta=node.meta,
        )

    def insert_nodes_batch(self, nodes: Sequence[Node]) -> list[Node]:
        """Insert multiple nodes in a single transaction.

        Args:
            nodes: Sequence of nodes to insert.

        Returns:
            List of nodes with assigned node_pks.
        """
        result: list[Node] = []

        with self.transaction() as conn:
            for node in nodes:
                meta_json = json.dumps(node.meta) if node.meta else None
                cur = conn.execute(
                    """
                    INSERT INTO nodes 
                    (short_id, full_id, doc_id, kind, level, title, start, end, parent_node_pk, meta_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node.short_id,
                        node.full_id,
                        node.doc_id,
                        node.kind,
                        node.level,
                        node.title,
                        node.start,
                        node.end,
                        node.parent_node_pk,
                        meta_json,
                    ),
                )
                result.append(
                    Node(
                        node_pk=cur.lastrowid,
                        short_id=node.short_id,
                        full_id=node.full_id,
                        doc_id=node.doc_id,
                        kind=node.kind,
                        level=node.level,
                        title=node.title,
                        start=node.start,
                        end=node.end,
                        parent_node_pk=node.parent_node_pk,
                        meta=node.meta,
                    )
                )

        return result

    def get_node_by_short_id(self, short_id: str) -> Node | None:
        """Get a node by short_id.

        Args:
            short_id: 4-character short ID.

        Returns:
            Node if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT node_pk, short_id, full_id, doc_id, kind, level, title, 
                   start, end, parent_node_pk, meta_json
            FROM nodes WHERE short_id = ?
            """,
            (short_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return self._row_to_node(row)

    def get_node_by_full_id(self, full_id: str) -> Node | None:
        """Get a node by full_id.

        Args:
            full_id: Full node ID (doc_id::short_id format).

        Returns:
            Node if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT node_pk, short_id, full_id, doc_id, kind, level, title, 
                   start, end, parent_node_pk, meta_json
            FROM nodes WHERE full_id = ?
            """,
            (full_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return self._row_to_node(row)

    def get_node_by_pk(self, node_pk: int) -> Node | None:
        """Get a node by primary key.

        Args:
            node_pk: Node primary key.

        Returns:
            Node if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT node_pk, short_id, full_id, doc_id, kind, level, title,
                   start, end, parent_node_pk, meta_json
            FROM nodes WHERE node_pk = ?
            """,
            (node_pk,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return self._row_to_node(row)

    def update_node_parent(self, node_pk: int, parent_node_pk: int) -> None:
        """Update a node's parent_node_pk.

        Args:
            node_pk: Node primary key.
            parent_node_pk: Parent node primary key.
        """
        with self.transaction() as conn:
            conn.execute(
                "UPDATE nodes SET parent_node_pk = ? WHERE node_pk = ?",
                (parent_node_pk, node_pk),
            )

    def get_nodes_by_doc_id(self, doc_id: str) -> list[Node]:
        """Get all nodes for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            List of nodes.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT node_pk, short_id, full_id, doc_id, kind, level, title,
                   start, end, parent_node_pk, meta_json
            FROM nodes WHERE doc_id = ? ORDER BY start
            """,
            (doc_id,),
        )
        return [self._row_to_node(row) for row in cur.fetchall()]

    def _row_to_node(self, row: sqlite3.Row) -> Node:
        """Convert a database row to a Node."""
        meta = json.loads(row["meta_json"]) if row["meta_json"] else {}
        return Node(
            node_pk=row["node_pk"],
            short_id=row["short_id"],
            full_id=row["full_id"],
            doc_id=row["doc_id"],
            kind=row["kind"],
            level=row["level"],
            title=row["title"],
            start=row["start"],
            end=row["end"],
            parent_node_pk=row["parent_node_pk"],
            meta=meta,
        )

    # Edge operations

    def insert_edge(self, edge: Edge) -> Edge:
        """Insert a new edge.

        Args:
            edge: Edge to insert.

        Returns:
            The inserted edge.
        """
        meta_json = json.dumps(edge.meta) if edge.meta else None

        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO edges (src_node_pk, dst_node_pk, type, weight, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (edge.src_node_pk, edge.dst_node_pk, edge.edge_type, edge.weight, meta_json),
            )

        return edge

    def get_edges_by_type(self, edge_type: str) -> list[Edge]:
        """Get all edges of a given type.

        Args:
            edge_type: Edge type (contains, next, ref).

        Returns:
            List of edges.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT src_node_pk, dst_node_pk, type, weight, meta_json
            FROM edges WHERE type = ?
            """,
            (edge_type,),
        )
        return [self._row_to_edge(row) for row in cur.fetchall()]

    def get_children(self, node_pk: int) -> list[Node]:
        """Get child nodes (connected by 'contains' edges).

        Args:
            node_pk: Parent node primary key.

        Returns:
            List of child nodes.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT n.node_pk, n.short_id, n.full_id, n.doc_id, n.kind, n.level,
                   n.title, n.start, n.end, n.parent_node_pk, n.meta_json
            FROM nodes n
            JOIN edges e ON e.dst_node_pk = n.node_pk
            WHERE e.src_node_pk = ? AND e.type = 'contains'
            ORDER BY n.start
            """,
            (node_pk,),
        )
        return [self._row_to_node(row) for row in cur.fetchall()]

    def get_siblings(self, node_pk: int) -> list[Node]:
        """Get sibling nodes (connected by 'next' edges).

        Args:
            node_pk: Starting node primary key.

        Returns:
            List of following sibling nodes.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT n.node_pk, n.short_id, n.full_id, n.doc_id, n.kind, n.level,
                   n.title, n.start, n.end, n.parent_node_pk, n.meta_json
            FROM nodes n
            JOIN edges e ON e.dst_node_pk = n.node_pk
            WHERE e.src_node_pk = ? AND e.type = 'next'
            """,
            (node_pk,),
        )
        return [self._row_to_node(row) for row in cur.fetchall()]

    def _row_to_edge(self, row: sqlite3.Row) -> Edge:
        """Convert a database row to an Edge."""
        meta = json.loads(row["meta_json"]) if row["meta_json"] else {}
        return Edge(
            src_node_pk=row["src_node_pk"],
            dst_node_pk=row["dst_node_pk"],
            edge_type=row["type"],
            weight=row["weight"],
            meta=meta,
        )

    # FTS operations

    def fts_index_node(self, node_pk: int, title: str | None, text: str, short_id: str) -> None:
        """Add a node to the FTS index.

        Args:
            node_pk: Node primary key.
            title: Node title (may be None).
            text: Node text content.
            short_id: Node short ID.
        """
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO fts_nodes (rowid, title, text, short_id)
                VALUES (?, ?, ?, ?)
                """,
                (node_pk, title or "", text, short_id),
            )

    def fts_search(self, query: str, limit: int = 20) -> list[tuple[Node, float]]:
        """Search nodes using FTS5.

        Args:
            query: Search query.
            limit: Maximum results to return.

        Returns:
            List of (Node, score) tuples, sorted by relevance.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT n.node_pk, n.short_id, n.full_id, n.doc_id, n.kind, n.level,
                   n.title, n.start, n.end, n.parent_node_pk, n.meta_json,
                   bm25(fts_nodes) as score
            FROM fts_nodes f
            JOIN nodes n ON f.rowid = n.node_pk
            WHERE fts_nodes MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (query, limit),
        )

        results: list[tuple[Node, float]] = []
        for row in cur.fetchall():
            node = self._row_to_node(row)
            score = row["score"]
            results.append((node, score))

        return results

    # Embedding operations

    def store_embedding(
        self,
        full_id: str,
        model: str,
        vector: list[float] | npt.NDArray[np.float32],
        created_at: int | None = None,
    ) -> Embedding:
        """Store or update an embedding for a node.

        Args:
            full_id: Node full_id to associate embedding with.
            model: Embedding model name.
            vector: Embedding vector (list[float] or numpy array).
            created_at: Unix timestamp (defaults to now).

        Returns:
            The created/updated Embedding.
        """
        if created_at is None:
            created_at = int(time.time())

        # Convert to numpy array if list
        if isinstance(vector, list):
            vector_array = np.array(vector, dtype=np.float32)
        else:
            vector_array = vector

        dimensions = len(vector_array)
        # Pack as little-endian floats for efficient storage
        vector_blob = vector_array.tobytes()

        with self.transaction() as conn:
            # Use INSERT OR REPLACE for upsert
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings
                    (full_id, model, dimensions, vector, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_id, model, dimensions, vector_blob, created_at),
            )

            # Get the pk
            cur = conn.execute(
                "SELECT embedding_pk FROM embeddings WHERE full_id = ? AND model = ?",
                (full_id, model),
            )
            row = cur.fetchone()
            embedding_pk = row[0] if row else None

        return Embedding(
            embedding_pk=embedding_pk,
            full_id=full_id,
            model=model,
            dimensions=dimensions,
            vector=vector_array,
            created_at=created_at,
        )

    def get_embedding(self, full_id: str, model: str) -> Embedding | None:
        """Get embedding for a node and model.

        Args:
            full_id: Node full_id.
            model: Embedding model name.

        Returns:
            Embedding if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT embedding_pk, full_id, model, dimensions, vector, created_at
            FROM embeddings
            WHERE full_id = ? AND model = ?
            """,
            (full_id, model),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return self._row_to_embedding(row)

    def get_all_embeddings_for_model(self, model: str, limit: int = 10000) -> list[Embedding]:
        """Get all embeddings for a specific model with safety limit.

        Warning: For large datasets (>10k embeddings), use
        stream_embeddings_for_model() instead to avoid OOM crashes.

        Args:
            model: Embedding model name.
            limit: Maximum number of embeddings to load (default: 10000).
                   Set to 0 for unlimited (not recommended for production).

        Returns:
            List of up to limit Embeddings for the model.

        Raises:
            ValueError: If limit is negative.
        """
        if limit < 0:
            raise ValueError("limit must be non-negative")

        conn = self._get_connection()
        if limit > 0:
            cur = conn.execute(
                """
                SELECT embedding_pk, full_id, model, dimensions, vector, created_at
                FROM embeddings
                WHERE model = ?
                LIMIT ?
                """,
                (model, limit),
            )
        else:
            logger.warning(
                "Loading unlimited embeddings for model=%s - may cause OOM",
                model,
            )
            cur = conn.execute(
                """
                SELECT embedding_pk, full_id, model, dimensions, vector, created_at
                FROM embeddings
                WHERE model = ?
                """,
                (model,),
            )

        return [self._row_to_embedding(row) for row in cur.fetchall()]

    def get_embeddings_for_model_batched(
        self, model: str, batch_size: int = 1000, offset: int = 0
    ) -> list[Embedding]:
        """Get embeddings for a model in batches to bound memory usage.

        This method allows streaming processing of large embedding collections
        by loading embeddings in fixed-size batches.

        Args:
            model: Embedding model name.
            batch_size: Maximum number of embeddings to return.
            offset: Number of embeddings to skip.

        Returns:
            List of up to batch_size Embeddings for the model.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT embedding_pk, full_id, model, dimensions, vector, created_at
            FROM embeddings
            WHERE model = ?
            ORDER BY embedding_pk
            LIMIT ? OFFSET ?
            """,
            (model, batch_size, offset),
        )

        return [self._row_to_embedding(row) for row in cur.fetchall()]

    def stream_embeddings_for_model(
        self, model: str, batch_size: int = 1000
    ) -> Iterator[list[Embedding]]:
        """Stream embeddings for a model in batches.

        This generator yields batches of embeddings, allowing memory-efficient
        processing of large embedding collections.

        Args:
            model: Embedding model name.
            batch_size: Number of embeddings per batch.

        Yields:
            Lists of Embedding objects, each containing up to batch_size items.
            The final batch may contain fewer items.
        """
        offset = 0
        while True:
            batch = self.get_embeddings_for_model_batched(model, batch_size, offset)
            if not batch:
                break
            yield batch
            offset += len(batch)
            # If we got fewer than batch_size, we're done
            if len(batch) < batch_size:
                break

    def _row_to_embedding(self, row: sqlite3.Row) -> Embedding:
        """Convert a database row to an Embedding object."""
        dimensions = row["dimensions"]
        vector_blob = row["vector"]
        # Use numpy frombuffer for memory efficiency (4 bytes per float vs ~24 for Python float)
        vector = np.frombuffer(vector_blob, dtype=np.float32)

        return Embedding(
            embedding_pk=row["embedding_pk"],
            full_id=row["full_id"],
            model=row["model"],
            dimensions=dimensions,
            vector=vector,
            created_at=row["created_at"],
        )

    @property
    def vec_available(self) -> bool:
        """Check if sqlite-vec extension is available for fast vector search.

        Returns:
            True if sqlite-vec extension was successfully loaded.
        """
        # Ensure connection is initialized to check extension status
        _ = self._get_connection()
        return self._vec_available

    def vec_search(
        self,
        model: str,
        query_vector: list[float],
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Perform fast vector similarity search using sqlite-vec.

        Creates a vec0 virtual table on-demand for the specified model
        and performs approximate nearest neighbor search.

        Args:
            model: Embedding model name (determines which embeddings to search).
            query_vector: Query vector for similarity search.
            k: Maximum number of results to return.

        Returns:
            List of (full_id, score) tuples, sorted by similarity (descending).

        Raises:
            RuntimeError: If sqlite-vec extension is not available.
            ValueError: If no embeddings found for the model.
        """
        if not self.vec_available:
            raise RuntimeError("sqlite-vec extension not available")

        conn = self._get_connection()

        # Get dimensions from one embedding for this model
        cur = conn.execute(
            "SELECT dimensions FROM embeddings WHERE model = ? LIMIT 1",
            (model,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"No embeddings found for model: {model}")
        dimensions = row[0]

        if len(query_vector) != dimensions:
            raise ValueError(
                f"Query vector dimension mismatch: expected {dimensions}, got {len(query_vector)}"
            )

        # Create a unique table name for this model
        # Sanitize model name to be SQL-safe for table names
        safe_model = model.replace("-", "_").replace(".", "_")
        if not safe_model.replace("_", "").isalnum():
            raise ValueError(f"Invalid model name for table creation: {model}")
        vec_table_name = f"vec_{safe_model}"

        # Create vec0 virtual table if it doesn't exist
        try:
            conn.execute(  # noqa: S608
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {vec_table_name} "
                f"USING vec0(embedding_float32({dimensions}))"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create vec0 table: {e}") from e

        # Populate vec0 table with current embeddings (upsert to handle duplicates)
        conn.execute(
            f"INSERT OR REPLACE INTO {vec_table_name}(rowid, vector) "  # noqa: S608
            f"SELECT embedding_pk, vector FROM embeddings WHERE model = ?",
            (model,),
        )

        # Convert query vector to sqlite-vec format
        vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        # Perform similarity search
        cur = conn.execute(
            f"SELECT e.full_id, distance "  # noqa: S608
            f"FROM {vec_table_name} v "
            f"JOIN embeddings e ON v.rowid = e.embedding_pk "
            f"WHERE v.vector MATCH ? AND k = ? "
            f"ORDER BY distance ASC",
            (vector_str, k),
        )

        # Convert distance to cosine similarity (distance = 1 - similarity)
        results = [(row["full_id"], 1.0 - row["distance"]) for row in cur.fetchall()]

        return results

    # Schema versioning

    def get_schema_version(self) -> int:
        """Get current schema version.

        Returns:
            Current schema version number.
        """
        conn = self._get_connection()
        cur = conn.execute("SELECT MAX(version) FROM schema_version")
        row = cur.fetchone()
        return row[0] if row[0] is not None else 0

    def get_pragma(self, pragma: str) -> str:
        """Get a PRAGMA value.

        Args:
            pragma: PRAGMA name (e.g., 'journal_mode').

        Returns:
            PRAGMA value as string.
        """
        conn = self._get_connection()
        cur = conn.execute(f"PRAGMA {pragma}")
        row = cur.fetchone()
        return str(row[0]) if row else ""

    # Collection operations

    def create_collection(
        self,
        collection_id: str,
        kind: str,
        name: str,
        meta: dict[str, Any] | None = None,
    ) -> Collection:
        """Create a new collection.

        Args:
            collection_id: Unique collection identifier.
            kind: Collection type (project, knowledgebase, etc.).
            name: Human-readable unique name.
            meta: Optional metadata dictionary.

        Returns:
            The created Collection.

        Raises:
            sqlite3.IntegrityError: If name already exists.
        """
        meta = meta or {}
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT INTO collections (collection_id, kind, name, meta_json)
                VALUES (?, ?, ?, ?)
                """,
                (collection_id, kind, name, json.dumps(meta)),
            )
        return Collection(collection_id=collection_id, kind=kind, name=name, meta=meta)

    def get_collection(self, collection_id: str) -> Collection | None:
        """Get a collection by ID.

        Args:
            collection_id: Collection identifier.

        Returns:
            Collection if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT collection_id, kind, name, meta_json FROM collections WHERE collection_id = ?",
            (collection_id,),
        )
        row = cur.fetchone()
        return self._row_to_collection(row) if row else None

    def get_collection_by_name(self, name: str) -> Collection | None:
        """Get a collection by name.

        Args:
            name: Collection name.

        Returns:
            Collection if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT collection_id, kind, name, meta_json FROM collections WHERE name = ?",
            (name,),
        )
        row = cur.fetchone()
        return self._row_to_collection(row) if row else None

    def list_collections(self, kind: str | None = None) -> list[Collection]:
        """List all collections, optionally filtered by kind.

        Args:
            kind: Optional filter by collection type.

        Returns:
            List of collections.
        """
        conn = self._get_connection()
        if kind:
            cur = conn.execute(
                "SELECT collection_id, kind, name, meta_json FROM collections "
                "WHERE kind = ? ORDER BY name",
                (kind,),
            )
        else:
            cur = conn.execute(
                "SELECT collection_id, kind, name, meta_json FROM collections ORDER BY name"
            )
        return [self._row_to_collection(row) for row in cur.fetchall()]

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection and its members.

        Args:
            collection_id: Collection identifier.

        Returns:
            True if deleted, False if not found.
        """
        with self.transaction() as conn:
            # Delete project settings
            conn.execute(
                "DELETE FROM project_settings WHERE collection_id = ?",
                (collection_id,),
            )
            # Delete members
            conn.execute(
                "DELETE FROM collection_members WHERE collection_id = ?",
                (collection_id,),
            )
            # Delete collection
            cur = conn.execute(
                "DELETE FROM collections WHERE collection_id = ?",
                (collection_id,),
            )
            return cur.rowcount > 0

    def _row_to_collection(self, row: sqlite3.Row) -> Collection:
        """Convert a database row to a Collection object."""
        meta_json = row["meta_json"]
        meta = json.loads(meta_json) if meta_json else {}
        return Collection(
            collection_id=row["collection_id"],
            kind=row["kind"],
            name=row["name"],
            meta=meta,
        )

    # Collection member operations

    def add_member_to_collection(
        self,
        collection_id: str,
        member_type: str,
        member_pk: str,
    ) -> CollectionMember:
        """Add a document or node to a collection.

        Args:
            collection_id: Collection identifier.
            member_type: 'document' or 'node'.
            member_pk: doc_id or full_id of the member.

        Returns:
            The created CollectionMember.
        """
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO collection_members
                (collection_id, member_type, member_pk)
                VALUES (?, ?, ?)
                """,
                (collection_id, member_type, member_pk),
            )
        return CollectionMember(
            collection_id=collection_id,
            member_type=member_type,
            member_pk=member_pk,
        )

    def remove_member_from_collection(
        self,
        collection_id: str,
        member_type: str,
        member_pk: str,
    ) -> bool:
        """Remove a member from a collection.

        Args:
            collection_id: Collection identifier.
            member_type: 'document' or 'node'.
            member_pk: doc_id or full_id.

        Returns:
            True if removed, False if not found.
        """
        with self.transaction() as conn:
            cur = conn.execute(
                """
                DELETE FROM collection_members
                WHERE collection_id = ? AND member_type = ? AND member_pk = ?
                """,
                (collection_id, member_type, member_pk),
            )
            return cur.rowcount > 0

    def list_collection_members(
        self,
        collection_id: str,
        member_type: str | None = None,
    ) -> list[CollectionMember]:
        """List members of a collection.

        Args:
            collection_id: Collection identifier.
            member_type: Optional filter by type.

        Returns:
            List of collection members.
        """
        conn = self._get_connection()
        if member_type:
            cur = conn.execute(
                """
                SELECT collection_id, member_type, member_pk
                FROM collection_members
                WHERE collection_id = ? AND member_type = ?
                """,
                (collection_id, member_type),
            )
        else:
            cur = conn.execute(
                """
                SELECT collection_id, member_type, member_pk
                FROM collection_members
                WHERE collection_id = ?
                """,
                (collection_id,),
            )
        return [
            CollectionMember(
                collection_id=row["collection_id"],
                member_type=row["member_type"],
                member_pk=row["member_pk"],
            )
            for row in cur.fetchall()
        ]

    def get_collections_for_member(
        self,
        member_type: str,
        member_pk: str,
    ) -> list[Collection]:
        """Get all collections containing a member.

        Args:
            member_type: 'document' or 'node'.
            member_pk: doc_id or full_id.

        Returns:
            List of collections containing the member.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT c.collection_id, c.kind, c.name, c.meta_json
            FROM collections c
            JOIN collection_members cm ON c.collection_id = cm.collection_id
            WHERE cm.member_type = ? AND cm.member_pk = ?
            ORDER BY c.name
            """,
            (member_type, member_pk),
        )
        return [self._row_to_collection(row) for row in cur.fetchall()]

    # Topic operations

    def create_topic(
        self,
        topic_id: str,
        name: str,
        meta: dict[str, Any] | None = None,
    ) -> Topic:
        """Create a new topic.

        Args:
            topic_id: Unique topic identifier.
            name: Human-readable unique name.
            meta: Optional metadata dictionary.

        Returns:
            The created Topic.

        Raises:
            sqlite3.IntegrityError: If name already exists.
        """
        meta = meta or {}
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO topics (topic_id, name, meta_json) VALUES (?, ?, ?)",
                (topic_id, name, json.dumps(meta)),
            )
        return Topic(topic_id=topic_id, name=name, meta=meta)

    def get_topic(self, topic_id: str) -> Topic | None:
        """Get a topic by ID.

        Args:
            topic_id: Topic identifier.

        Returns:
            Topic if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT topic_id, name, meta_json FROM topics WHERE topic_id = ?",
            (topic_id,),
        )
        row = cur.fetchone()
        return self._row_to_topic(row) if row else None

    def get_topic_by_name(self, name: str) -> Topic | None:
        """Get a topic by name.

        Args:
            name: Topic name.

        Returns:
            Topic if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT topic_id, name, meta_json FROM topics WHERE name = ?",
            (name,),
        )
        row = cur.fetchone()
        return self._row_to_topic(row) if row else None

    def list_topics(self) -> list[Topic]:
        """List all topics.

        Returns:
            List of all topics.
        """
        conn = self._get_connection()
        cur = conn.execute("SELECT topic_id, name, meta_json FROM topics ORDER BY name")
        return [self._row_to_topic(row) for row in cur.fetchall()]

    def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic and its links.

        Args:
            topic_id: Topic identifier.

        Returns:
            True if deleted, False if not found.
        """
        with self.transaction() as conn:
            # Delete links
            conn.execute("DELETE FROM topic_links WHERE topic_id = ?", (topic_id,))
            # Delete topic
            cur = conn.execute("DELETE FROM topics WHERE topic_id = ?", (topic_id,))
            return cur.rowcount > 0

    def _row_to_topic(self, row: sqlite3.Row) -> Topic:
        """Convert a database row to a Topic object."""
        meta_json = row["meta_json"]
        meta = json.loads(meta_json) if meta_json else {}
        return Topic(topic_id=row["topic_id"], name=row["name"], meta=meta)

    # Topic link operations

    def tag_with_topic(
        self,
        topic_id: str,
        target_type: str,
        target_pk: str,
        weight: float = 1.0,
        meta: dict[str, Any] | None = None,
    ) -> TopicLink:
        """Link a topic to a document or node.

        Args:
            topic_id: Topic identifier.
            target_type: 'document' or 'node'.
            target_pk: doc_id or full_id.
            weight: Optional relevance weight.
            meta: Optional metadata.

        Returns:
            The created TopicLink.
        """
        meta = meta or {}
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO topic_links
                (topic_id, target_type, target_pk, weight, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (topic_id, target_type, target_pk, weight, json.dumps(meta)),
            )
        return TopicLink(
            topic_id=topic_id,
            target_type=target_type,
            target_pk=target_pk,
            weight=weight,
            meta=meta,
        )

    def untag_topic(
        self,
        topic_id: str,
        target_type: str,
        target_pk: str,
    ) -> bool:
        """Remove a topic link.

        Args:
            topic_id: Topic identifier.
            target_type: 'document' or 'node'.
            target_pk: doc_id or full_id.

        Returns:
            True if removed, False if not found.
        """
        with self.transaction() as conn:
            cur = conn.execute(
                """
                DELETE FROM topic_links
                WHERE topic_id = ? AND target_type = ? AND target_pk = ?
                """,
                (topic_id, target_type, target_pk),
            )
            return cur.rowcount > 0

    def list_topics_for_target(
        self,
        target_type: str,
        target_pk: str,
    ) -> list[tuple[Topic, float]]:
        """List topics linked to a target.

        Args:
            target_type: 'document' or 'node'.
            target_pk: doc_id or full_id.

        Returns:
            List of (Topic, weight) tuples.
        """
        conn = self._get_connection()
        cur = conn.execute(
            """
            SELECT t.topic_id, t.name, t.meta_json, tl.weight
            FROM topics t
            JOIN topic_links tl ON t.topic_id = tl.topic_id
            WHERE tl.target_type = ? AND tl.target_pk = ?
            ORDER BY tl.weight DESC, t.name
            """,
            (target_type, target_pk),
        )
        return [(self._row_to_topic(row), row["weight"]) for row in cur.fetchall()]

    def list_targets_for_topic(
        self,
        topic_id: str,
        target_type: str | None = None,
    ) -> list[TopicLink]:
        """List all targets linked to a topic.

        Args:
            topic_id: Topic identifier.
            target_type: Optional filter by type.

        Returns:
            List of TopicLinks.
        """
        conn = self._get_connection()
        if target_type:
            cur = conn.execute(
                """
                SELECT topic_id, target_type, target_pk, weight, meta_json
                FROM topic_links
                WHERE topic_id = ? AND target_type = ?
                ORDER BY weight DESC
                """,
                (topic_id, target_type),
            )
        else:
            cur = conn.execute(
                """
                SELECT topic_id, target_type, target_pk, weight, meta_json
                FROM topic_links
                WHERE topic_id = ?
                ORDER BY weight DESC
                """,
                (topic_id,),
            )
        return [self._row_to_topic_link(row) for row in cur.fetchall()]

    def _row_to_topic_link(self, row: sqlite3.Row) -> TopicLink:
        """Convert a database row to a TopicLink object."""
        meta_json = row["meta_json"]
        meta = json.loads(meta_json) if meta_json else {}
        return TopicLink(
            topic_id=row["topic_id"],
            target_type=row["target_type"],
            target_pk=row["target_pk"],
            weight=row["weight"],
            meta=meta,
        )

    # Project settings operations

    def set_project_settings(
        self,
        collection_id: str,
        defaults: dict[str, Any],
    ) -> ProjectSettings:
        """Set project default settings.

        Args:
            collection_id: Collection identifier (must be kind='project').
            defaults: Settings dictionary.

        Returns:
            The ProjectSettings object.
        """
        with self.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO project_settings
                (collection_id, defaults_json)
                VALUES (?, ?)
                """,
                (collection_id, json.dumps(defaults)),
            )
        return ProjectSettings(collection_id=collection_id, defaults=defaults)

    def get_project_settings(self, collection_id: str) -> ProjectSettings | None:
        """Get project settings.

        Args:
            collection_id: Collection identifier.

        Returns:
            ProjectSettings if found, None otherwise.
        """
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT collection_id, defaults_json FROM project_settings WHERE collection_id = ?",
            (collection_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        defaults_json = row["defaults_json"]
        defaults = json.loads(defaults_json) if defaults_json else {}
        return ProjectSettings(collection_id=row["collection_id"], defaults=defaults)
