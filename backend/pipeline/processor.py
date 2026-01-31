"""
Data Processing Pipeline
Normalizes crime types, geocodes locations, and updates trends
"""
import sqlite3
import re
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import CRIME_TYPE_MAPPINGS
from backend.database import get_connection


def normalize_crime_type(raw_type: str) -> str:
    """Normalize various crime type descriptions to standard categories"""
    if not raw_type:
        return 'other'

    raw_lower = raw_type.lower()

    for normalized_type, keywords in CRIME_TYPE_MAPPINGS.items():
        for keyword in keywords:
            if keyword in raw_lower:
                return normalized_type

    # Additional mappings for police codes
    police_codes = {
        'theft': ['larceny', 'stealing', 'shoplifting', 'pocket-picking', 'purse-snatching'],
        'robbery': ['robbery', 'strong-arm', 'mugging'],
        'burglary': ['burglary', 'break', 'entry', 'b&e'],
        'assault': ['assault', 'battery', 'agg assault'],
        'fraud': ['fraud', 'forgery', 'embezzlement', 'counterfeit'],
        'vandalism': ['vandalism', 'mischief', 'damage', 'graffiti'],
        'weapons': ['weapon', 'firearm', 'gun', 'knife'],
        'drugs': ['drug', 'narcotic', 'controlled substance']
    }

    for norm_type, terms in police_codes.items():
        if any(term in raw_lower for term in terms):
            return norm_type

    return 'other'


def calculate_severity_from_type(incident_type: str, description: str = '') -> int:
    """Calculate severity based on incident type and description"""
    desc_lower = (description or '').lower()

    # Base severity by type
    type_severity = {
        'homicide': 5,
        'armed_robbery': 5,
        'assault': 4,
        'robbery': 4,
        'orc': 4,
        'smash_grab': 4,
        'burglary': 3,
        'arson': 4,
        'weapons': 4,
        'theft': 2,
        'shoplifting': 2,
        'fraud': 2,
        'vandalism': 2,
        'trespass': 1,
        'drugs': 2,
        'other': 2
    }

    base = type_severity.get(incident_type, 2)

    # Adjust based on description
    if any(word in desc_lower for word in ['aggravated', 'felony', 'armed', 'weapon', 'gun']):
        base = min(5, base + 1)
    if any(word in desc_lower for word in ['petty', 'minor', 'misdemeanor']):
        base = max(1, base - 1)

    return base


def update_incident_classifications():
    """Update incident type classifications and severity scores"""
    conn = get_connection()

    # Get incidents needing classification update
    cursor = conn.execute("""
        SELECT id, incident_type, description, severity
        FROM incidents
        WHERE incident_type IS NULL
           OR incident_type = ''
           OR incident_type = 'other'
           OR severity IS NULL
           OR severity = 0
    """)

    updates = []
    for row in cursor.fetchall():
        inc_id = row['id']
        raw_type = row['incident_type'] or ''
        description = row['description'] or ''

        # Normalize type
        normalized_type = normalize_crime_type(f"{raw_type} {description}")

        # Calculate severity
        severity = calculate_severity_from_type(normalized_type, description)

        updates.append((normalized_type, severity, inc_id))

    # Batch update
    if updates:
        conn.executemany("""
            UPDATE incidents
            SET incident_type = ?, severity = ?
            WHERE id = ?
        """, updates)
        conn.commit()
        print(f"Updated classifications for {len(updates)} incidents")

    conn.close()
    return len(updates)


def update_daily_trends():
    """Aggregate daily incident counts for trend charts"""
    conn = get_connection()

    # Clear and rebuild trends for recent data
    conn.execute("DELETE FROM daily_trends WHERE date >= date('now', '-90 days')")

    # Aggregate by date, location, and type
    conn.execute("""
        INSERT INTO daily_trends (date, country, state_province, city, incident_type, incident_count, avg_severity)
        SELECT
            incident_date,
            country,
            state_province,
            city,
            incident_type,
            COUNT(*) as incident_count,
            AVG(severity) as avg_severity
        FROM incidents
        WHERE incident_date >= date('now', '-90 days')
          AND incident_date IS NOT NULL
        GROUP BY incident_date, country, state_province, city, incident_type
    """)

    conn.commit()

    # Get count of new trend records
    cursor = conn.execute("SELECT COUNT(*) FROM daily_trends WHERE date >= date('now', '-90 days')")
    count = cursor.fetchone()[0]

    conn.close()
    print(f"Generated {count} daily trend records")
    return count


def update_location_summaries():
    """Update location summary table for quick filtering"""
    conn = get_connection()

    # Clear and rebuild
    conn.execute("DELETE FROM locations")

    conn.execute("""
        INSERT INTO locations (country, country_code, state_province, city, latitude, longitude, incident_count)
        SELECT
            country,
            country_code,
            state_province,
            city,
            AVG(latitude) as latitude,
            AVG(longitude) as longitude,
            COUNT(*) as incident_count
        FROM incidents
        WHERE country IS NOT NULL
        GROUP BY country, country_code, state_province, city
    """)

    conn.commit()

    cursor = conn.execute("SELECT COUNT(*) FROM locations")
    count = cursor.fetchone()[0]

    conn.close()
    print(f"Updated {count} location summaries")
    return count


def run_full_pipeline():
    """Run complete data processing pipeline"""
    print("\n=== Running Data Processing Pipeline ===\n")

    results = {
        'classifications_updated': 0,
        'trends_generated': 0,
        'locations_updated': 0
    }

    print("1. Updating incident classifications...")
    results['classifications_updated'] = update_incident_classifications()

    print("\n2. Generating daily trends...")
    results['trends_generated'] = update_daily_trends()

    print("\n3. Updating location summaries...")
    results['locations_updated'] = update_location_summaries()

    print("\n=== Pipeline Complete ===")
    return results


if __name__ == "__main__":
    results = run_full_pipeline()
    print(f"\nResults: {results}")
