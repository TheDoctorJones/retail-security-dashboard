"""
Database schema and utilities for Retail Security Dashboard
Supports both SQLite (local dev) and PostgreSQL (production)
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Check if we're using PostgreSQL (via DATABASE_URL) or SQLite
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Fix for Render's postgres:// URLs (psycopg2 needs postgresql://)
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    import sqlite3
    _default_db_path = Path(__file__).parent / "data" / "retail_security.db"
    DATABASE_PATH = Path(os.environ.get('DB_PATH', str(_default_db_path)))

# PostgreSQL Schema
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    source_id TEXT UNIQUE,
    source_type TEXT NOT NULL,
    source_name TEXT,
    title TEXT,
    description TEXT,
    incident_type TEXT,
    severity INTEGER DEFAULT 1,
    country TEXT,
    country_code TEXT,
    state_province TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    retailer_mentioned TEXT,
    is_retail_related BOOLEAN DEFAULT FALSE,
    incident_date DATE,
    incident_datetime TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL,
    api_url TEXT,
    last_scraped TIMESTAMP,
    last_success BOOLEAN,
    total_incidents INTEGER DEFAULT 0,
    config TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    country TEXT,
    country_code TEXT,
    state_province TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    incident_count INTEGER DEFAULT 0,
    UNIQUE(country, state_province, city)
);

CREATE TABLE IF NOT EXISTS daily_trends (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    country TEXT,
    state_province TEXT,
    city TEXT,
    incident_type TEXT,
    incident_count INTEGER DEFAULT 0,
    avg_severity REAL,
    UNIQUE(date, country, state_province, city, incident_type)
);

CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(incident_date);
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(country, state_province, city);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_incidents_source ON incidents(source_type, source_name);
CREATE INDEX IF NOT EXISTS idx_daily_trends_date ON daily_trends(date);
"""

# SQLite Schema
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT UNIQUE,
    source_type TEXT NOT NULL,
    source_name TEXT,
    title TEXT,
    description TEXT,
    incident_type TEXT,
    severity INTEGER DEFAULT 1,
    country TEXT,
    country_code TEXT,
    state_province TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    retailer_mentioned TEXT,
    is_retail_related BOOLEAN DEFAULT 0,
    incident_date DATE,
    incident_datetime DATETIME,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL,
    api_url TEXT,
    last_scraped DATETIME,
    last_success BOOLEAN,
    total_incidents INTEGER DEFAULT 0,
    config TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT,
    country_code TEXT,
    state_province TEXT,
    city TEXT,
    latitude REAL,
    longitude REAL,
    incident_count INTEGER DEFAULT 0,
    UNIQUE(country, state_province, city)
);

CREATE TABLE IF NOT EXISTS daily_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    country TEXT,
    state_province TEXT,
    city TEXT,
    incident_type TEXT,
    incident_count INTEGER DEFAULT 0,
    avg_severity REAL,
    UNIQUE(date, country, state_province, city, incident_type)
);

CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(incident_date);
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(country, state_province, city);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_incidents_source ON incidents(source_type, source_name);
CREATE INDEX IF NOT EXISTS idx_daily_trends_date ON daily_trends(date);
CREATE INDEX IF NOT EXISTS idx_daily_trends_location ON daily_trends(country, state_province);
"""


@contextmanager
def get_connection():
    """Get database connection (works with both SQLite and PostgreSQL)"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DATABASE_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def get_cursor(conn):
    """Get appropriate cursor for the database type"""
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()


def init_db():
    """Initialize database with schema"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if USE_POSTGRES:
            cursor.execute(POSTGRES_SCHEMA)
        else:
            conn.executescript(SQLITE_SCHEMA)
        conn.commit()

    db_type = "PostgreSQL" if USE_POSTGRES else f"SQLite at {DATABASE_PATH}"
    print(f"Database initialized ({db_type})")


def _get_placeholder():
    """Get the correct placeholder for the database type"""
    return "%s" if USE_POSTGRES else "?"


def insert_incident(conn, incident: Dict[str, Any]) -> bool:
    """Insert an incident, returns True if inserted, False if duplicate"""
    ph = _get_placeholder()

    try:
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute(f"""
                INSERT INTO incidents (
                    source_id, source_type, source_name, title, description,
                    incident_type, severity, country, country_code, state_province,
                    city, address, latitude, longitude, retailer_mentioned,
                    is_retail_related, incident_date, incident_datetime, raw_data, url
                ) VALUES (
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph}
                )
                ON CONFLICT (source_id) DO NOTHING
            """, (
                incident.get('source_id'),
                incident.get('source_type'),
                incident.get('source_name'),
                incident.get('title'),
                incident.get('description'),
                incident.get('incident_type', 'unknown'),
                incident.get('severity', 1),
                incident.get('country'),
                incident.get('country_code'),
                incident.get('state_province'),
                incident.get('city'),
                incident.get('address'),
                incident.get('latitude'),
                incident.get('longitude'),
                json.dumps(incident.get('retailer_mentioned', [])),
                incident.get('is_retail_related', False),
                incident.get('incident_date'),
                incident.get('incident_datetime'),
                json.dumps(incident.get('raw_data', {})),
                incident.get('url')
            ))
            return cursor.rowcount > 0
        else:
            cursor.execute(f"""
                INSERT INTO incidents (
                    source_id, source_type, source_name, title, description,
                    incident_type, severity, country, country_code, state_province,
                    city, address, latitude, longitude, retailer_mentioned,
                    is_retail_related, incident_date, incident_datetime, raw_data, url
                ) VALUES (
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph},
                    {ph}, {ph}, {ph}, {ph}, {ph}
                )
            """, (
                incident.get('source_id'),
                incident.get('source_type'),
                incident.get('source_name'),
                incident.get('title'),
                incident.get('description'),
                incident.get('incident_type', 'unknown'),
                incident.get('severity', 1),
                incident.get('country'),
                incident.get('country_code'),
                incident.get('state_province'),
                incident.get('city'),
                incident.get('address'),
                incident.get('latitude'),
                incident.get('longitude'),
                json.dumps(incident.get('retailer_mentioned', [])),
                incident.get('is_retail_related', False),
                incident.get('incident_date'),
                incident.get('incident_datetime'),
                json.dumps(incident.get('raw_data', {})),
                incident.get('url')
            ))
            return True
    except Exception as e:
        if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
            return False
        raise


def bulk_insert_incidents(incidents: List[Dict[str, Any]]) -> tuple:
    """Bulk insert incidents, returns (inserted_count, duplicate_count)"""
    inserted = 0
    duplicates = 0

    with get_connection() as conn:
        for incident in incidents:
            if insert_incident(conn, incident):
                inserted += 1
            else:
                duplicates += 1
        conn.commit()

    return inserted, duplicates


def update_source_status(source_name: str, success: bool, incident_count: int = 0):
    """Update source scraping status"""
    ph = _get_placeholder()

    with get_connection() as conn:
        cursor = conn.cursor()

        if USE_POSTGRES:
            cursor.execute(f"""
                INSERT INTO sources (name, source_type, last_scraped, last_success, total_incidents)
                VALUES ({ph}, '', CURRENT_TIMESTAMP, {ph}, {ph})
                ON CONFLICT(name) DO UPDATE SET
                    last_scraped = CURRENT_TIMESTAMP,
                    last_success = EXCLUDED.last_success,
                    total_incidents = sources.total_incidents + EXCLUDED.total_incidents
            """, (source_name, success, incident_count))
        else:
            cursor.execute(f"""
                INSERT INTO sources (name, source_type, last_scraped, last_success, total_incidents)
                VALUES ({ph}, '', CURRENT_TIMESTAMP, {ph}, {ph})
                ON CONFLICT(name) DO UPDATE SET
                    last_scraped = CURRENT_TIMESTAMP,
                    last_success = {ph},
                    total_incidents = total_incidents + {ph}
            """, (source_name, success, incident_count, success, incident_count))

        conn.commit()


def _rows_to_dicts(cursor, rows) -> List[Dict[str, Any]]:
    """Convert database rows to list of dicts"""
    if USE_POSTGRES:
        return [dict(row) for row in rows]
    else:
        return [dict(row) for row in rows]


def get_incidents(
    limit: int = 100,
    offset: int = 0,
    country: Optional[str] = None,
    state_province: Optional[str] = None,
    city: Optional[str] = None,
    incident_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_severity: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get incidents with filtering"""
    ph = _get_placeholder()

    with get_connection() as conn:
        cursor = get_cursor(conn)

        query = "SELECT * FROM incidents WHERE 1=1"
        params = []

        if country:
            query += f" AND country = {ph}"
            params.append(country)
        if state_province:
            query += f" AND state_province = {ph}"
            params.append(state_province)
        if city:
            query += f" AND city = {ph}"
            params.append(city)
        if incident_type:
            query += f" AND incident_type = {ph}"
            params.append(incident_type)
        if start_date:
            query += f" AND incident_date >= {ph}"
            params.append(start_date)
        if end_date:
            query += f" AND incident_date <= {ph}"
            params.append(end_date)
        if min_severity:
            query += f" AND severity >= {ph}"
            params.append(min_severity)

        query += f" ORDER BY incident_datetime DESC LIMIT {ph} OFFSET {ph}"
        params.extend([limit, offset])

        cursor.execute(query, params)
        return _rows_to_dicts(cursor, cursor.fetchall())


def get_trend_data(
    days: int = 30,
    country: Optional[str] = None,
    state_province: Optional[str] = None,
    group_by: str = 'day'
) -> List[Dict[str, Any]]:
    """Get trend data for charts"""
    ph = _get_placeholder()

    with get_connection() as conn:
        cursor = get_cursor(conn)

        if USE_POSTGRES:
            date_trunc = {'day': 'day', 'week': 'week', 'month': 'month'}.get(group_by, 'day')
            query = f"""
                SELECT
                    TO_CHAR(DATE_TRUNC('{date_trunc}', incident_date), 'YYYY-MM-DD') as period,
                    incident_type,
                    COUNT(*) as count,
                    AVG(severity) as avg_severity
                FROM incidents
                WHERE incident_date >= CURRENT_DATE - INTERVAL '{days} days'
            """
        else:
            date_format = {'day': '%Y-%m-%d', 'week': '%Y-%W', 'month': '%Y-%m'}.get(group_by, '%Y-%m-%d')
            query = f"""
                SELECT
                    strftime('{date_format}', incident_date) as period,
                    incident_type,
                    COUNT(*) as count,
                    AVG(severity) as avg_severity
                FROM incidents
                WHERE incident_date >= date('now', '-{days} days')
            """

        params = []
        if country:
            query += f" AND country = {ph}"
            params.append(country)
        if state_province:
            query += f" AND state_province = {ph}"
            params.append(state_province)

        if USE_POSTGRES:
            query += f" GROUP BY DATE_TRUNC('{date_trunc}', incident_date), incident_type ORDER BY period"
        else:
            query += f" GROUP BY strftime('{date_format}', incident_date), incident_type ORDER BY period"

        cursor.execute(query, params)
        return _rows_to_dicts(cursor, cursor.fetchall())


def get_location_summary() -> List[Dict[str, Any]]:
    """Get summary of incidents by location for map"""
    with get_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            SELECT
                country,
                state_province,
                city,
                AVG(latitude) as latitude,
                AVG(longitude) as longitude,
                COUNT(*) as incident_count,
                AVG(severity) as avg_severity
            FROM incidents
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY country, state_province, city
            ORDER BY incident_count DESC
        """)
        return _rows_to_dicts(cursor, cursor.fetchall())


def get_incident_types() -> List[str]:
    """Get list of all incident types"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT incident_type FROM incidents WHERE incident_type IS NOT NULL")
        return [row[0] for row in cursor.fetchall()]


def get_locations_hierarchy() -> Dict[str, Any]:
    """Get hierarchical location data for filters"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT country, state_province, city
            FROM incidents
            WHERE country IS NOT NULL
            ORDER BY country, state_province, city
        """)

        hierarchy = {}
        for row in cursor.fetchall():
            country, state, city = row[0], row[1], row[2]
            if country not in hierarchy:
                hierarchy[country] = {}
            if state and state not in hierarchy[country]:
                hierarchy[country][state] = []
            if city and state:
                hierarchy[country][state].append(city)

        return hierarchy


def get_stats() -> Dict[str, Any]:
    """Get overall statistics"""
    with get_connection() as conn:
        cursor = conn.cursor()
        stats = {}

        # Total incidents
        cursor.execute("SELECT COUNT(*) FROM incidents")
        stats['total_incidents'] = cursor.fetchone()[0]

        # Incidents by source
        cursor.execute("""
            SELECT source_type, COUNT(*) as count
            FROM incidents
            GROUP BY source_type
        """)
        stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Incidents by type
        cursor.execute("""
            SELECT incident_type, COUNT(*) as count
            FROM incidents
            GROUP BY incident_type
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Recent activity
        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE incident_date >= CURRENT_DATE - INTERVAL '7 days'")
            stats['last_7_days'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE incident_date >= CURRENT_DATE - INTERVAL '30 days'")
            stats['last_30_days'] = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE incident_date >= date('now', '-7 days')")
            stats['last_7_days'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM incidents WHERE incident_date >= date('now', '-30 days')")
            stats['last_30_days'] = cursor.fetchone()[0]

        return stats


if __name__ == "__main__":
    init_db()
    print("Database schema created successfully")
