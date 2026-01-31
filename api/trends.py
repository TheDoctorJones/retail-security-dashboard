"""
Serverless API: Get trend data for charts
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"

def load_incidents():
      if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                              return json.load(f)
                      return []

  class handler(BaseHTTPRequestHandler):
        def do_GET(self):
                  parsed = urlparse(self.path)
                  params = parse_qs(parsed.query)

            country = params.get('country', [None])[0]
        state = params.get('state', [None])[0]

        incidents = load_incidents()

        # Filter
        if country:
                      incidents = [i for i in incidents if i.get('country') == country]
                  if state:
                                incidents = [i for i in incidents if i.get('state_province') == state]

        # Group by date and type
        by_date_type = defaultdict(lambda: defaultdict(int))
        for inc in incidents:
                      date = inc.get('incident_date', '')[:10] if inc.get('incident_date') else None
                      inc_type = inc.get('incident_type', 'other')
                      if date:
                                        by_date_type[date][inc_type] += 1
                                        by_date_type[date]['total'] += 1

                  # Convert to list format for charts
                  trends = []
        for date in sorted(by_date_type.keys()):
                      entry = {'period': date, **by_date_type[date]}
                      trends.append(entry)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {'trends': trends[-30:]}
        self.wfile.write(json.dumps(response).encode())
