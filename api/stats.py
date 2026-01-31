"""
Serverless API: Get dashboard statistics
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"

def load_incidents():
      if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                              return json.load(f)
                      return []

  class handler(BaseHTTPRequestHandler):
        def do_GET(self):
                  incidents = load_incidents()

            # Calculate stats
                  total = len(incidents)

            # By source
                  by_source = Counter(i.get('source_type') for i in incidents)

            # By type
                  by_type = Counter(i.get('incident_type') for i in incidents)
                  by_type_top = dict(by_type.most_common(10))

            # Recent counts
                  today = datetime.now().date()
                  last_7_days = sum(1 for i in incidents
                      if i.get('incident_date') and
                      (today - datetime.strptime(i['incident_date'][:10], '%Y-%m-%d').date()).days <= 7)
                  last_30_days = sum(1 for i in incidents
                      if i.get('incident_date') and
                      (today - datetime.strptime(i['incident_date'][:10], '%Y-%m-%d').date()).days <= 30)

            self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
                      'total_incidents': total,
                      'by_source': dict(by_source),
                      'by_type': by_type_top,
                      'last_7_days': last_7_days,
                      'last_30_days': last_30_days
        }

        self.wfile.write(json.dumps(response).encode())
