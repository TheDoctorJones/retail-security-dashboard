"""
City Open Data Scraper
Fetches crime data from various city police department open data APIs
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import CITY_DATA_SOURCES
from backend.database import bulk_insert_incidents, update_source_status


def get_nested_value(data: dict, key_path: str) -> Any:
    """Get nested value from dict using dot notation"""
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def parse_date(date_str: str) -> tuple[Optional[str], Optional[str]]:
    """Parse various date formats, returns (date, datetime)"""
    if not date_str:
        return None, None

    # Handle timestamps (milliseconds since epoch)
    if isinstance(date_str, (int, float)):
        dt = datetime.fromtimestamp(date_str / 1000 if date_str > 1e11 else date_str)
        return dt.strftime('%Y-%m-%d'), dt.isoformat()

    # Try various date formats
    formats = [
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y',
        '%Y/%m/%d',
    ]

    date_str = str(date_str).replace('Z', '').replace('+00:00', '')

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:26], fmt)
            return dt.strftime('%Y-%m-%d'), dt.isoformat()
        except ValueError:
            continue

    return None, None


def fetch_city_data(city_key: str, days_back: int = 30) -> List[Dict[str, Any]]:
    """Fetch data from a specific city's open data API"""
    if city_key not in CITY_DATA_SOURCES:
        print(f"Unknown city: {city_key}")
        return []

    config = CITY_DATA_SOURCES[city_key]
    print(f"Fetching data from {config['name']}...")

    # Build request parameters
    params = dict(config.get('params', {}))

    # Replace date placeholder if present
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    for key, value in params.items():
        if isinstance(value, str) and '{start_date}' in value:
            params[key] = value.format(start_date=start_date)

    try:
        response = requests.get(
            config['api_url'],
            params=params,
            timeout=30,
            headers={'User-Agent': 'RetailSecurityDashboard/1.0'}
        )
        response.raise_for_status()
        data = response.json()

        # Navigate to the correct response path if specified
        if 'response_path' in config:
            for key in config['response_path'].split('.'):
                if isinstance(data, dict):
                    data = data.get(key, [])
                else:
                    data = []
                    break

        if not isinstance(data, list):
            print(f"Unexpected response format from {city_key}")
            return []

        # Transform data to common format
        incidents = []
        field_map = config['field_map']
        attributes_key = config.get('attributes_key')

        for record in data:
            # Handle ArcGIS-style responses with nested attributes
            if attributes_key and isinstance(record, dict):
                record = record.get(attributes_key, record)

            # Extract fields using mapping
            incident_date, incident_datetime = parse_date(
                get_nested_value(record, field_map.get('date', ''))
            )

            # Skip records without dates or very old records
            if not incident_date:
                continue

            raw_id = get_nested_value(record, field_map.get('id', ''))
            source_id = f"{city_key}_{raw_id}" if raw_id else f"{city_key}_{hash(json.dumps(record, default=str))}"

            incident = {
                'source_id': source_id,
                'source_type': 'police_api',
                'source_name': city_key,
                'title': None,
                'description': get_nested_value(record, field_map.get('description', '')),
                'incident_type': get_nested_value(record, field_map.get('type', '')),
                'country': config['country'],
                'country_code': config['country_code'],
                'state_province': config['state'],
                'city': config['city'],
                'address': get_nested_value(record, field_map.get('address', '')),
                'latitude': get_nested_value(record, field_map.get('latitude', '')),
                'longitude': get_nested_value(record, field_map.get('longitude', '')),
                'incident_date': incident_date,
                'incident_datetime': incident_datetime,
                'raw_data': record
            }

            # Convert lat/lon to float if present
            try:
                if incident['latitude']:
                    incident['latitude'] = float(incident['latitude'])
                if incident['longitude']:
                    incident['longitude'] = float(incident['longitude'])
            except (ValueError, TypeError):
                incident['latitude'] = None
                incident['longitude'] = None

            incidents.append(incident)

        print(f"  Retrieved {len(incidents)} incidents from {config['name']}")
        return incidents

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching from {city_key}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"  Error parsing JSON from {city_key}: {e}")
        return []


def scrape_all_cities(days_back: int = 30, cities: Optional[List[str]] = None) -> Dict[str, Any]:
    """Scrape data from all configured cities or a specific list"""
    cities_to_scrape = cities or list(CITY_DATA_SOURCES.keys())

    results = {
        'total_incidents': 0,
        'total_inserted': 0,
        'total_duplicates': 0,
        'by_city': {}
    }

    for city_key in cities_to_scrape:
        incidents = fetch_city_data(city_key, days_back)

        if incidents:
            inserted, duplicates = bulk_insert_incidents(incidents)
            update_source_status(f"city_{city_key}", True, inserted)

            results['by_city'][city_key] = {
                'fetched': len(incidents),
                'inserted': inserted,
                'duplicates': duplicates
            }
            results['total_incidents'] += len(incidents)
            results['total_inserted'] += inserted
            results['total_duplicates'] += duplicates
        else:
            update_source_status(f"city_{city_key}", False, 0)
            results['by_city'][city_key] = {
                'fetched': 0,
                'inserted': 0,
                'duplicates': 0,
                'error': True
            }

    return results


if __name__ == "__main__":
    # Test with a single city
    from backend.database import init_db
    init_db()

    print("\n=== Testing City Data Scraper ===\n")

    # Test with Chicago (usually reliable)
    results = scrape_all_cities(days_back=7, cities=['chicago', 'san_francisco'])

    print(f"\n=== Results ===")
    print(f"Total fetched: {results['total_incidents']}")
    print(f"Total inserted: {results['total_inserted']}")
    print(f"Total duplicates: {results['total_duplicates']}")
