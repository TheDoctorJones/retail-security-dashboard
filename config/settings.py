"""
Configuration settings for Retail Security Dashboard
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"

# API Keys (set via environment variables)
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")  # Get free key at newsapi.org
FBI_API_KEY = os.environ.get("FBI_API_KEY", "")  # Get at api.data.gov

# News API Configuration
NEWS_CONFIG = {
    "base_url": "https://newsapi.org/v2",
    "keywords": [
        "retail theft", "shoplifting", "organized retail crime",
        "store robbery", "smash and grab", "retail security",
        "store theft", "retail crime", "loss prevention",
        "armed robbery store", "burglary retail"
    ],
    "domains": None,  # None for all, or list like ["reuters.com", "apnews.com"]
    "language": "en",
    "page_size": 100
}

# RSS Feed Sources for retail/security news
RSS_FEEDS = [
    {
        "name": "lp_magazine",
        "url": "https://losspreventionmedia.com/feed/",
        "category": "retail_security"
    },
    {
        "name": "security_magazine",
        "url": "https://www.securitymagazine.com/rss/topic/2236-retail",
        "category": "retail_security"
    },
    {
        "name": "retail_dive",
        "url": "https://www.retaildive.com/feeds/news/",
        "category": "retail_news"
    }
]

# City Open Data Sources - Police/Crime APIs
# Each entry contains the API endpoint and field mappings
CITY_DATA_SOURCES = {
    # United States
    "chicago": {
        "name": "Chicago Police Department",
        "country": "United States",
        "country_code": "US",
        "state": "Illinois",
        "city": "Chicago",
        "api_url": "https://data.cityofchicago.org/resource/ijzp-q8t2.json",
        "params": {
            "$limit": 1000,
            "$order": "date DESC",
            "$where": "date >= '{start_date}'"
        },
        "field_map": {
            "id": "id",
            "date": "date",
            "type": "primary_type",
            "description": "description",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "block"
        }
    },
    "nyc": {
        "name": "NYPD",
        "country": "United States",
        "country_code": "US",
        "state": "New York",
        "city": "New York",
        "api_url": "https://data.cityofnewyork.us/resource/5uac-w243.json",
        "params": {
            "$limit": 1000,
            "$order": "cmplnt_fr_dt DESC"
        },
        "field_map": {
            "id": "cmplnt_num",
            "date": "cmplnt_fr_dt",
            "type": "ofns_desc",
            "description": "pd_desc",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "prem_typ_desc"
        }
    },
    "los_angeles": {
        "name": "LAPD",
        "country": "United States",
        "country_code": "US",
        "state": "California",
        "city": "Los Angeles",
        "api_url": "https://data.lacity.org/resource/2nrs-mtv8.json",
        "params": {
            "$limit": 1000,
            "$order": "date_occ DESC"
        },
        "field_map": {
            "id": "dr_no",
            "date": "date_occ",
            "type": "crm_cd_desc",
            "description": "crm_cd_desc",
            "latitude": "lat",
            "longitude": "lon",
            "address": "location"
        }
    },
    "philadelphia": {
        "name": "Philadelphia Police",
        "country": "United States",
        "country_code": "US",
        "state": "Pennsylvania",
        "city": "Philadelphia",
        "api_url": "https://phl.carto.com/api/v2/sql",
        "params": {
            "q": "SELECT * FROM incidents_part1_part2 ORDER BY dispatch_date DESC LIMIT 1000"
        },
        "field_map": {
            "id": "objectid",
            "date": "dispatch_date",
            "type": "text_general_code",
            "description": "text_general_code",
            "latitude": "lat",
            "longitude": "lng",
            "address": "location_block"
        },
        "response_path": "rows"
    },
    "atlanta": {
        "name": "Atlanta Police",
        "country": "United States",
        "country_code": "US",
        "state": "Georgia",
        "city": "Atlanta",
        "api_url": "https://services3.arcgis.com/Et5Qfajgiyosiw4d/arcgis/rest/services/CrimeDataExport/FeatureServer/0/query",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "Report_Date DESC",
            "resultRecordCount": 1000,
            "f": "json"
        },
        "field_map": {
            "id": "Report_Number",
            "date": "Report_Date",
            "type": "UC2_Literal",
            "description": "UC2_Literal",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "location"
        },
        "response_path": "features",
        "attributes_key": "attributes"
    },
    "san_francisco": {
        "name": "San Francisco Police",
        "country": "United States",
        "country_code": "US",
        "state": "California",
        "city": "San Francisco",
        "api_url": "https://data.sfgov.org/resource/wg3w-h783.json",
        "params": {
            "$limit": 1000,
            "$order": "incident_datetime DESC"
        },
        "field_map": {
            "id": "incident_number",
            "date": "incident_date",
            "type": "incident_category",
            "description": "incident_description",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "intersection"
        }
    },
    "seattle": {
        "name": "Seattle Police",
        "country": "United States",
        "country_code": "US",
        "state": "Washington",
        "city": "Seattle",
        "api_url": "https://data.seattle.gov/resource/tazs-3rd5.json",
        "params": {
            "$limit": 1000,
            "$order": "offense_start_datetime DESC"
        },
        "field_map": {
            "id": "offense_id",
            "date": "offense_start_datetime",
            "type": "offense",
            "description": "offense",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "100_block_address"
        }
    },
    "austin": {
        "name": "Austin Police",
        "country": "United States",
        "country_code": "US",
        "state": "Texas",
        "city": "Austin",
        "api_url": "https://data.austintexas.gov/resource/fdj4-gpfu.json",
        "params": {
            "$limit": 1000,
            "$order": "occ_date_time DESC"
        },
        "field_map": {
            "id": "incident_report_number",
            "date": "occ_date_time",
            "type": "crime_type",
            "description": "crime_type",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "address"
        }
    },
    "denver": {
        "name": "Denver Police",
        "country": "United States",
        "country_code": "US",
        "state": "Colorado",
        "city": "Denver",
        "api_url": "https://data.denvergov.org/resource/crime.json",
        "params": {
            "$limit": 1000,
            "$order": "reported_date DESC"
        },
        "field_map": {
            "id": "incident_id",
            "date": "reported_date",
            "type": "offense_category_id",
            "description": "offense_type_id",
            "latitude": "geo_lat",
            "longitude": "geo_lon",
            "address": "incident_address"
        }
    },
    "boston": {
        "name": "Boston Police",
        "country": "United States",
        "country_code": "US",
        "state": "Massachusetts",
        "city": "Boston",
        "api_url": "https://data.boston.gov/api/3/action/datastore_search",
        "params": {
            "resource_id": "12cb3883-56f5-47de-afa5-3b1cf61b257b",
            "limit": 1000,
            "sort": "OCCURRED_ON_DATE desc"
        },
        "field_map": {
            "id": "INCIDENT_NUMBER",
            "date": "OCCURRED_ON_DATE",
            "type": "OFFENSE_DESCRIPTION",
            "description": "OFFENSE_DESCRIPTION",
            "latitude": "Lat",
            "longitude": "Long",
            "address": "STREET"
        },
        "response_path": "result.records"
    },
    "baltimore": {
        "name": "Baltimore Police",
        "country": "United States",
        "country_code": "US",
        "state": "Maryland",
        "city": "Baltimore",
        "api_url": "https://data.baltimorecity.gov/resource/wsfq-mvij.json",
        "params": {
            "$limit": 1000,
            "$order": "crimedate DESC"
        },
        "field_map": {
            "id": "rowid",
            "date": "crimedate",
            "type": "description",
            "description": "description",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "location"
        }
    },
    "dallas": {
        "name": "Dallas Police",
        "country": "United States",
        "country_code": "US",
        "state": "Texas",
        "city": "Dallas",
        "api_url": "https://www.dallasopendata.com/resource/qv6i-rri7.json",
        "params": {
            "$limit": 1000,
            "$order": "date1 DESC"
        },
        "field_map": {
            "id": "incidentnum",
            "date": "date1",
            "type": "offincident",
            "description": "offincident",
            "latitude": "geocoded_column.latitude",
            "longitude": "geocoded_column.longitude",
            "address": "location"
        }
    },
    "houston": {
        "name": "Houston Police",
        "country": "United States",
        "country_code": "US",
        "state": "Texas",
        "city": "Houston",
        "api_url": "https://data.houstontx.gov/resource/gvaq-kkpc.json",
        "params": {
            "$limit": 1000,
            "$order": "date DESC"
        },
        "field_map": {
            "id": "incident",
            "date": "date",
            "type": "offense_type",
            "description": "offense_type",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "block_range"
        }
    },
    "phoenix": {
        "name": "Phoenix Police",
        "country": "United States",
        "country_code": "US",
        "state": "Arizona",
        "city": "Phoenix",
        "api_url": "https://data.phoenix.gov/resource/yp46-pbax.json",
        "params": {
            "$limit": 1000,
            "$order": "occurred_to DESC"
        },
        "field_map": {
            "id": "inc_number",
            "date": "occurred_to",
            "type": "ucr_crime_category",
            "description": "ucr_crime_category",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "address"
        }
    },
    "dc": {
        "name": "DC Metropolitan Police",
        "country": "United States",
        "country_code": "US",
        "state": "District of Columbia",
        "city": "Washington",
        "api_url": "https://opendata.dc.gov/resource/89pz-zy7h.json",
        "params": {
            "$limit": 1000,
            "$order": "report_dat DESC"
        },
        "field_map": {
            "id": "ccn",
            "date": "report_dat",
            "type": "offense",
            "description": "offense",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "block"
        }
    },
    "detroit": {
        "name": "Detroit Police",
        "country": "United States",
        "country_code": "US",
        "state": "Michigan",
        "city": "Detroit",
        "api_url": "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/Crime_Incidents/FeatureServer/0/query",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "incident_timestamp DESC",
            "resultRecordCount": 1000,
            "f": "json"
        },
        "field_map": {
            "id": "crime_id",
            "date": "incident_timestamp",
            "type": "offense_description",
            "description": "offense_description",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "address"
        },
        "response_path": "features",
        "attributes_key": "attributes"
    },
    # Canada
    "toronto": {
        "name": "Toronto Police",
        "country": "Canada",
        "country_code": "CA",
        "state": "Ontario",
        "city": "Toronto",
        "api_url": "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search",
        "params": {
            "resource_id": "3c2e737b-4c0b-4fc8-8a77-9d6c4e691f7b",
            "limit": 1000,
            "sort": "OCC_DATE desc"
        },
        "field_map": {
            "id": "_id",
            "date": "OCC_DATE",
            "type": "MCI_CATEGORY",
            "description": "OFFENCE",
            "latitude": "LAT_WGS84",
            "longitude": "LONG_WGS84",
            "address": "PREMISES_TYPE"
        },
        "response_path": "result.records"
    },
    "vancouver": {
        "name": "Vancouver Police",
        "country": "Canada",
        "country_code": "CA",
        "state": "British Columbia",
        "city": "Vancouver",
        "api_url": "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/crimedata_csv_all_years/records",
        "params": {
            "limit": 1000,
            "order_by": "year DESC, month DESC"
        },
        "field_map": {
            "id": "row_id",
            "date": "year,month",
            "type": "type",
            "description": "type",
            "latitude": "latitude",
            "longitude": "longitude",
            "address": "hundred_block"
        },
        "response_path": "records"
    }
}

# FBI Crime Data Explorer Configuration
FBI_CONFIG = {
    "base_url": "https://api.usa.gov/crime/fbi/cde",
    "endpoints": {
        "summary": "/summarized/agency/{ori}/{offense}/{since}/{until}",
        "agencies": "/agency",
        "offenses": "/offense"
    }
}

# Crime type mappings - normalize different sources to common types
CRIME_TYPE_MAPPINGS = {
    # Theft-related
    "theft": ["theft", "larceny", "shoplifting", "retail theft", "petit larceny", "grand larceny", "stealing"],
    "robbery": ["robbery", "armed robbery", "strong arm robbery", "mugging"],
    "burglary": ["burglary", "breaking and entering", "b&e", "break-in"],

    # Violent
    "assault": ["assault", "battery", "aggravated assault", "simple assault", "attack"],
    "homicide": ["homicide", "murder", "manslaughter", "killing"],

    # Property
    "vandalism": ["vandalism", "criminal mischief", "property damage", "graffiti"],
    "arson": ["arson", "fire", "burning"],

    # Fraud
    "fraud": ["fraud", "forgery", "counterfeit", "identity theft", "credit card fraud"],

    # Other
    "trespass": ["trespass", "trespassing", "criminal trespass"],
    "weapons": ["weapons", "gun", "firearm", "knife"],
    "drugs": ["drugs", "narcotics", "controlled substance", "possession"]
}

# Retailer names to detect in text
MAJOR_RETAILERS = [
    "walmart", "target", "costco", "kroger", "walgreens", "cvs",
    "home depot", "lowe's", "best buy", "macy's", "nordstrom",
    "tj maxx", "marshalls", "ross", "dollar general", "dollar tree",
    "7-eleven", "circle k", "wawa", "sheetz", "safeway", "albertsons",
    "whole foods", "trader joe's", "aldi", "publix", "h-e-b",
    "rite aid", "ulta", "sephora", "apple store", "nike",
    "foot locker", "dick's sporting goods", "rei", "academy sports",
    "autozone", "o'reilly", "advance auto", "pep boys",
    "bed bath", "pier 1", "pottery barn", "williams sonoma",
    "gamestop", "barnes noble", "staples", "office depot"
]
