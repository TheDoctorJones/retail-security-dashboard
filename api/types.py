"""
Serverless API: Get list of incident types
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"

def load_incidents():
      if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                              return json.load(f)
                      return []

  class handler(BaseHTTPRequestHandler):
        def do_GET(self):
                  incidents = load_incidents()

            types = sorted(set(i.get('incident_type') for i in incidents if i.get('incident_type')))

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps({'types': types}).encode())
