"""
Nexus AI – Shared Extension Instances
======================================
Centralised initialisation of Flask extensions to avoid circular imports.
Extensions are created here and bound to the app inside the factory.
"""

import logging

from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

logger = logging.getLogger(__name__)

# ── SQL Alchemy (MS SQL Server / SQLite) ────────────────────────
db = SQLAlchemy()

# ── JWT Authentication ──────────────────────────────────────────
jwt = JWTManager()

# ── CORS ────────────────────────────────────────────────────────
cors = CORS()

# ── MongoDB (initialised lazily in app factory) ─────────────────
mongo_client = None
mongo_db = None
_using_fallback_auth = False


def init_mongo(app):
    """
    Initialise the MongoDB connection from app config.
    Falls back to an in-memory dict-based store if MongoDB
    is unavailable (for local dev without Mongo installed).
    """
    global mongo_client, mongo_db, _using_fallback_auth

    uri = app.config.get("MONGO_URI", "")
    if not uri:
        logger.warning("MONGO_URI not set – using in-memory auth fallback.")
        _using_fallback_auth = True
        mongo_db = _FallbackMongoDB()
        return

    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a connection test
        client.admin.command("ping")
        mongo_client = client
        db_name = uri.rsplit("/", 1)[-1].split("?")[0] or "nexus_ai_auth"
        mongo_db = client[db_name]
        logger.info("Connected to MongoDB: %s", db_name)
    except Exception as exc:
        logger.warning(
            "MongoDB connection failed (%s) – using in-memory auth fallback.", exc
        )
        _using_fallback_auth = True
        mongo_db = _FallbackMongoDB()


# ── Fallback in-memory store for dev without MongoDB ────────────
class _FallbackCollection:
    """Minimal dict-backed collection that mimics PyMongo's API."""

    def __init__(self):
        self._docs: list[dict] = []
        self._counter = 0

    def find_one(self, query: dict):
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def insert_one(self, doc: dict):
        self._counter += 1
        doc["_id"] = str(self._counter)
        self._docs.append(dict(doc))
        return type("Result", (), {"inserted_id": doc["_id"]})()


class _FallbackMongoDB:
    """Minimal dict-backed database that mimics PyMongo's DB."""

    def __init__(self):
        self._collections: dict[str, _FallbackCollection] = {}

    def __getitem__(self, name: str):
        if name not in self._collections:
            self._collections[name] = _FallbackCollection()
        return self._collections[name]
