# Retail Security Dashboard

Real-time dashboard for tracking retail security incidents, crime trends, and loss prevention data across North and South America.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🚀 Deploy to Cloud (Shareable Link)

Deploy to Render.com for free with automatic daily data updates:

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo (it auto-detects `render.yaml`)
4. Click Deploy

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.**

Your dashboard will be live at: `https://your-app-name.onrender.com`

---

## Features

- **Multi-Source Data Collection**
  - 15+ City Police Department APIs (Chicago, NYC, LA, San Francisco, etc.)
  - Google News RSS feeds for retail crime news
  - Industry RSS feeds (Loss Prevention Magazine, Security Magazine)
  - NewsAPI integration (optional, requires API key)

- **Interactive Dashboard**
  - Real-time incident feed with severity indicators
  - Trend charts showing incident patterns over time
  - Geographic distribution visualization
  - Filterable by location, incident type, severity, and time range

- **Data Processing**
  - Automatic crime type classification
  - Severity scoring
  - Retailer mention detection
  - Location normalization

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)

### Installation

1. **Clone and setup backend:**

```bash
cd retail-security-dashboard

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Initialize database and run first scrape:**

```bash
# This will create the database and fetch data from all sources
python run_scraper.py --days 7
```

3. **Start the API server:**

```bash
python backend/api_server.py
```

4. **Start the frontend (in a new terminal):**

```bash
cd frontend
npm install
npm run dev
```

5. **Open the dashboard:**

Navigate to `http://localhost:3000` in your browser.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEWS_API_KEY` | API key from newsapi.org | No (enables NewsAPI) |

### Adding Custom Data Sources

Edit `config/settings.py` to add new city data sources:

```python
CITY_DATA_SOURCES = {
    "new_city": {
        "name": "New City Police",
        "country": "United States",
        "country_code": "US",
        "state": "State Name",
        "city": "City Name",
        "api_url": "https://api.example.com/crimes.json",
        "params": {"$limit": 1000},
        "field_map": {
            "id": "incident_id",
            "date": "date_field",
            "type": "crime_type",
            "description": "description",
            "latitude": "lat",
            "longitude": "lon",
            "address": "address"
        }
    }
}
```

## Data Sources

### City Police APIs (Currently Configured)

| City | State/Province | Country |
|------|----------------|---------|
| Chicago | Illinois | US |
| New York | New York | US |
| Los Angeles | California | US |
| San Francisco | California | US |
| Philadelphia | Pennsylvania | US |
| Atlanta | Georgia | US |
| Seattle | Washington | US |
| Austin | Texas | US |
| Denver | Colorado | US |
| Boston | Massachusetts | US |
| Baltimore | Maryland | US |
| Dallas | Texas | US |
| Houston | Texas | US |
| Phoenix | Arizona | US |
| Washington | DC | US |
| Detroit | Michigan | US |
| Toronto | Ontario | CA |
| Vancouver | British Columbia | CA |

### News Sources

- Google News RSS (retail crime keywords)
- Loss Prevention Magazine RSS
- Security Magazine RSS
- Retail Dive RSS
- NewsAPI (optional, requires key)

## Usage

### Daily Data Collection

Run the scraper daily (e.g., via cron):

```bash
# Full scrape (all sources, last 30 days)
python run_scraper.py

# Quick scrape (last 7 days)
python run_scraper.py --days 7

# City data only (faster)
python run_scraper.py --cities-only

# News only
python run_scraper.py --news-only
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Overall statistics |
| `GET /api/incidents` | List incidents (with filters) |
| `GET /api/trends` | Trend data for charts |
| `GET /api/map` | Location data for map |
| `GET /api/locations` | Location hierarchy for filters |
| `GET /api/types` | List of incident types |
| `GET /api/search?q=query` | Search incidents |

### Filter Parameters

All list endpoints support:
- `country` - Filter by country
- `state` - Filter by state/province
- `city` - Filter by city
- `type` - Filter by incident type
- `min_severity` - Minimum severity (1-5)
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)
- `limit` - Max results (default 100)
- `offset` - Pagination offset

## Project Structure

```
retail-security-dashboard/
├── backend/
│   ├── data/                 # SQLite database
│   ├── scrapers/
│   │   ├── city_data_scraper.py
│   │   └── news_scraper.py
│   ├── pipeline/
│   │   └── processor.py
│   ├── api_server.py         # Flask REST API
│   └── database.py           # Database schema & queries
├── frontend/
│   ├── src/
│   │   └── App.jsx           # React dashboard
│   ├── package.json
│   └── vite.config.js
├── config/
│   └── settings.py           # Data source configurations
├── run_scraper.py            # Main scraper script
├── requirements.txt
└── README.md
```

## Incident Types

The system classifies incidents into these categories:

| Type | Description |
|------|-------------|
| `theft` | General theft, larceny, shoplifting |
| `robbery` | Robbery (may involve force) |
| `burglary` | Breaking and entering |
| `assault` | Physical assault |
| `orc` | Organized Retail Crime |
| `smash_grab` | Smash-and-grab incidents |
| `fraud` | Fraud, forgery, identity theft |
| `vandalism` | Property damage |
| `weapons` | Weapons offenses |
| `drugs` | Drug-related offenses |

## Severity Scale

| Level | Description |
|-------|-------------|
| 1 | Minor (petty theft, misdemeanor) |
| 2 | Low (standard theft, minor property crime) |
| 3 | Medium (burglary, organized theft) |
| 4 | High (robbery, assault, ORC) |
| 5 | Critical (armed robbery, violence, major ORC) |

## Limitations

- **News data bias**: High-profile incidents are overrepresented
- **Geocoding**: Not all incidents have precise coordinates
- **Historical data**: System starts collecting from day 1
- **API availability**: Some city APIs may have rate limits or downtime
- **Retail attribution**: Police data doesn't tag "retail" specifically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add new data sources or features
4. Submit a pull request

## License

MIT License - feel free to use for your security operations.
