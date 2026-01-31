"""
News API Scraper
Fetches retail crime news from NewsAPI and Google News RSS
"""
import requests
import feedparser
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import NEWS_CONFIG, RSS_FEEDS, MAJOR_RETAILERS, NEWS_API_KEY
from backend.database import bulk_insert_incidents, update_source_status


def extract_retailers(text: str) -> List[str]:
    """Extract retailer names mentioned in text"""
    if not text:
        return []

    text_lower = text.lower()
    found = []
    for retailer in MAJOR_RETAILERS:
        if retailer in text_lower:
            found.append(retailer.title())
    return found


def extract_location_from_text(text: str) -> Dict[str, Optional[str]]:
    """Extract location info from news text (basic heuristic)"""
    # US States
    us_states = {
        'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
        'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
        'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
        'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
        'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
        'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
        'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
        'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
        'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
        'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
        'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
        'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
        'wisconsin': 'WI', 'wyoming': 'WY'
    }

    # Major cities
    major_cities = {
        'new york': ('New York', 'NY'), 'los angeles': ('California', 'CA'),
        'chicago': ('Illinois', 'IL'), 'houston': ('Texas', 'TX'),
        'phoenix': ('Arizona', 'AZ'), 'philadelphia': ('Pennsylvania', 'PA'),
        'san antonio': ('Texas', 'TX'), 'san diego': ('California', 'CA'),
        'dallas': ('Texas', 'TX'), 'san francisco': ('California', 'CA'),
        'austin': ('Texas', 'TX'), 'seattle': ('Washington', 'WA'),
        'denver': ('Colorado', 'CO'), 'boston': ('Massachusetts', 'MA'),
        'atlanta': ('Georgia', 'GA'), 'miami': ('Florida', 'FL'),
        'detroit': ('Michigan', 'MI'), 'minneapolis': ('Minnesota', 'MN'),
        'portland': ('Oregon', 'OR'), 'las vegas': ('Nevada', 'NV'),
        'baltimore': ('Maryland', 'MD'), 'milwaukee': ('Wisconsin', 'WI'),
        'toronto': ('Ontario', None), 'vancouver': ('British Columbia', None),
        'montreal': ('Quebec', None), 'calgary': ('Alberta', None)
    }

    text_lower = text.lower() if text else ''
    location = {
        'country': None,
        'country_code': None,
        'state_province': None,
        'city': None
    }

    # Check for cities first (more specific)
    for city, (state, code) in major_cities.items():
        if city in text_lower:
            location['city'] = city.title()
            location['state_province'] = state
            if code:  # US city
                location['country'] = 'United States'
                location['country_code'] = 'US'
            else:  # Canadian city
                location['country'] = 'Canada'
                location['country_code'] = 'CA'
            return location

    # Check for state names
    for state, code in us_states.items():
        if state in text_lower:
            location['state_province'] = state.title()
            location['country'] = 'United States'
            location['country_code'] = 'US'
            return location

    return location


def classify_incident_type(text: str) -> str:
    """Classify incident type based on text content"""
    text_lower = text.lower() if text else ''

    classifications = [
        ('orc', ['organized retail crime', 'orc', 'theft ring', 'crime ring', 'fencing operation']),
        ('smash_grab', ['smash and grab', 'smash-and-grab', 'flash mob', 'mob robbery']),
        ('armed_robbery', ['armed robbery', 'gunpoint', 'gun robbery', 'armed suspect']),
        ('robbery', ['robbery', 'robbed', 'robber']),
        ('assault', ['assault', 'attacked', 'violence', 'violent', 'injured']),
        ('shoplifting', ['shoplifting', 'shoplift', 'shoplifter']),
        ('theft', ['theft', 'stolen', 'stole', 'stealing', 'larceny']),
        ('burglary', ['burglary', 'break-in', 'breaking and entering', 'broke into']),
        ('fraud', ['fraud', 'scam', 'counterfeit', 'identity theft']),
        ('vandalism', ['vandalism', 'vandalized', 'graffiti', 'property damage']),
    ]

    for incident_type, keywords in classifications:
        if any(kw in text_lower for kw in keywords):
            return incident_type

    return 'other'


def calculate_severity(text: str, incident_type: str) -> int:
    """Calculate severity score 1-5 based on incident details"""
    text_lower = text.lower() if text else ''

    severity = 2  # Default

    # Increase for violence indicators
    violence_terms = ['shot', 'shooting', 'stabbed', 'killed', 'murder', 'dead', 'weapon', 'gun', 'hostage']
    if any(term in text_lower for term in violence_terms):
        severity += 2

    # Increase for organized crime
    if incident_type == 'orc' or 'organized' in text_lower:
        severity += 1

    # Increase for large scale
    scale_terms = ['million', '$100,000', 'hundreds of thousands', 'mass', 'multiple stores', 'spree']
    if any(term in text_lower for term in scale_terms):
        severity += 1

    # Decrease for minor incidents
    minor_terms = ['petty', 'minor', 'misdemeanor', 'small']
    if any(term in text_lower for term in minor_terms):
        severity -= 1

    return max(1, min(5, severity))


def fetch_newsapi(days_back: int = 7) -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI"""
    if not NEWS_API_KEY:
        print("NewsAPI key not set - skipping NewsAPI")
        return []

    incidents = []
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    for keyword in NEWS_CONFIG['keywords'][:5]:  # Limit keywords to avoid rate limits
        try:
            params = {
                'q': keyword,
                'from': from_date,
                'language': NEWS_CONFIG['language'],
                'pageSize': 50,
                'sortBy': 'publishedAt',
                'apiKey': NEWS_API_KEY
            }

            response = requests.get(
                f"{NEWS_CONFIG['base_url']}/everything",
                params=params,
                timeout=15
            )

            if response.status_code == 426:
                print("  NewsAPI requires paid plan for this query")
                continue

            response.raise_for_status()
            data = response.json()

            for article in data.get('articles', []):
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('content', '')
                full_text = f"{title} {description} {content}"

                # Extract location
                location = extract_location_from_text(full_text)

                # Classify incident
                incident_type = classify_incident_type(full_text)
                severity = calculate_severity(full_text, incident_type)

                # Extract retailers
                retailers = extract_retailers(full_text)

                # Parse date
                pub_date = article.get('publishedAt', '')[:10]

                source_id = f"newsapi_{hashlib.md5(article.get('url', '').encode()).hexdigest()}"

                incident = {
                    'source_id': source_id,
                    'source_type': 'news',
                    'source_name': 'newsapi',
                    'title': title,
                    'description': description,
                    'incident_type': incident_type,
                    'severity': severity,
                    'country': location['country'],
                    'country_code': location['country_code'],
                    'state_province': location['state_province'],
                    'city': location['city'],
                    'address': None,
                    'latitude': None,
                    'longitude': None,
                    'retailer_mentioned': retailers,
                    'is_retail_related': len(retailers) > 0 or 'retail' in full_text.lower(),
                    'incident_date': pub_date,
                    'incident_datetime': article.get('publishedAt'),
                    'url': article.get('url'),
                    'raw_data': article
                }

                incidents.append(incident)

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching NewsAPI for '{keyword}': {e}")

    # Deduplicate by source_id
    seen = set()
    unique_incidents = []
    for inc in incidents:
        if inc['source_id'] not in seen:
            seen.add(inc['source_id'])
            unique_incidents.append(inc)

    print(f"  Retrieved {len(unique_incidents)} articles from NewsAPI")
    return unique_incidents


def fetch_google_news_rss(days_back: int = 7) -> List[Dict[str, Any]]:
    """Fetch news from Google News RSS"""
    incidents = []

    search_terms = [
        'retail+theft',
        'shoplifting+crime',
        'organized+retail+crime',
        'store+robbery'
    ]

    for term in search_terms:
        try:
            url = f"https://news.google.com/rss/search?q={term}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:25]:  # Limit per term
                title = entry.get('title', '')
                description = entry.get('summary', '')
                full_text = f"{title} {description}"

                # Parse date
                pub_date = None
                if 'published_parsed' in entry and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')

                # Skip if too old
                if pub_date:
                    article_date = datetime.strptime(pub_date, '%Y-%m-%d')
                    if article_date < datetime.now() - timedelta(days=days_back):
                        continue

                location = extract_location_from_text(full_text)
                incident_type = classify_incident_type(full_text)
                severity = calculate_severity(full_text, incident_type)
                retailers = extract_retailers(full_text)

                source_id = f"gnews_{hashlib.md5(entry.get('link', '').encode()).hexdigest()}"

                incident = {
                    'source_id': source_id,
                    'source_type': 'news',
                    'source_name': 'google_news',
                    'title': title,
                    'description': description,
                    'incident_type': incident_type,
                    'severity': severity,
                    'country': location['country'],
                    'country_code': location['country_code'],
                    'state_province': location['state_province'],
                    'city': location['city'],
                    'address': None,
                    'latitude': None,
                    'longitude': None,
                    'retailer_mentioned': retailers,
                    'is_retail_related': len(retailers) > 0 or 'retail' in full_text.lower(),
                    'incident_date': pub_date,
                    'incident_datetime': pub_date,
                    'url': entry.get('link'),
                    'raw_data': {'title': title, 'summary': description, 'link': entry.get('link')}
                }

                incidents.append(incident)

        except Exception as e:
            print(f"  Error fetching Google News for '{term}': {e}")

    # Deduplicate
    seen = set()
    unique_incidents = []
    for inc in incidents:
        if inc['source_id'] not in seen:
            seen.add(inc['source_id'])
            unique_incidents.append(inc)

    print(f"  Retrieved {len(unique_incidents)} articles from Google News RSS")
    return unique_incidents


def fetch_industry_rss() -> List[Dict[str, Any]]:
    """Fetch from industry-specific RSS feeds"""
    incidents = []

    for feed_config in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_config['url'])

            for entry in feed.entries[:20]:
                title = entry.get('title', '')
                description = entry.get('summary', entry.get('description', ''))
                full_text = f"{title} {description}"

                # Parse date
                pub_date = None
                if 'published_parsed' in entry and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')

                location = extract_location_from_text(full_text)
                incident_type = classify_incident_type(full_text)
                severity = calculate_severity(full_text, incident_type)
                retailers = extract_retailers(full_text)

                source_id = f"rss_{feed_config['name']}_{hashlib.md5(entry.get('link', '').encode()).hexdigest()}"

                incident = {
                    'source_id': source_id,
                    'source_type': 'rss',
                    'source_name': feed_config['name'],
                    'title': title,
                    'description': description,
                    'incident_type': incident_type,
                    'severity': severity,
                    'country': location['country'],
                    'country_code': location['country_code'],
                    'state_province': location['state_province'],
                    'city': location['city'],
                    'address': None,
                    'latitude': None,
                    'longitude': None,
                    'retailer_mentioned': retailers,
                    'is_retail_related': True,  # Industry feeds are retail-focused
                    'incident_date': pub_date,
                    'incident_datetime': pub_date,
                    'url': entry.get('link'),
                    'raw_data': {'title': title, 'summary': description, 'link': entry.get('link')}
                }

                incidents.append(incident)

            print(f"  Retrieved {len(feed.entries[:20])} articles from {feed_config['name']}")

        except Exception as e:
            print(f"  Error fetching RSS feed {feed_config['name']}: {e}")

    return incidents


def scrape_all_news(days_back: int = 7) -> Dict[str, Any]:
    """Scrape all news sources"""
    results = {
        'total_incidents': 0,
        'total_inserted': 0,
        'total_duplicates': 0,
        'by_source': {}
    }

    # NewsAPI
    print("\nFetching from NewsAPI...")
    newsapi_incidents = fetch_newsapi(days_back)
    if newsapi_incidents:
        inserted, duplicates = bulk_insert_incidents(newsapi_incidents)
        update_source_status('newsapi', True, inserted)
        results['by_source']['newsapi'] = {'fetched': len(newsapi_incidents), 'inserted': inserted, 'duplicates': duplicates}
        results['total_incidents'] += len(newsapi_incidents)
        results['total_inserted'] += inserted
        results['total_duplicates'] += duplicates

    # Google News RSS
    print("\nFetching from Google News RSS...")
    gnews_incidents = fetch_google_news_rss(days_back)
    if gnews_incidents:
        inserted, duplicates = bulk_insert_incidents(gnews_incidents)
        update_source_status('google_news', True, inserted)
        results['by_source']['google_news'] = {'fetched': len(gnews_incidents), 'inserted': inserted, 'duplicates': duplicates}
        results['total_incidents'] += len(gnews_incidents)
        results['total_inserted'] += inserted
        results['total_duplicates'] += duplicates

    # Industry RSS
    print("\nFetching from Industry RSS feeds...")
    rss_incidents = fetch_industry_rss()
    if rss_incidents:
        inserted, duplicates = bulk_insert_incidents(rss_incidents)
        update_source_status('industry_rss', True, inserted)
        results['by_source']['industry_rss'] = {'fetched': len(rss_incidents), 'inserted': inserted, 'duplicates': duplicates}
        results['total_incidents'] += len(rss_incidents)
        results['total_inserted'] += inserted
        results['total_duplicates'] += duplicates

    return results


if __name__ == "__main__":
    from backend.database import init_db
    init_db()

    print("=== Testing News Scraper ===")
    results = scrape_all_news(days_back=7)

    print(f"\n=== Results ===")
    print(f"Total fetched: {results['total_incidents']}")
    print(f"Total inserted: {results['total_inserted']}")
    print(f"Total duplicates: {results['total_duplicates']}")
