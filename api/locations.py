"""
Serverless API: Get location hierarchy for filters
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from collections import defaultdict

DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"

def load_incidents():
      if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                              return json.load(f)
                      return []

  class handler(BaseHTTPRequestHandler):
        def do_GET(self):
                  incidents = load_incidents()

            # Build hierarchy
                  hierarchy = defaultdict(lambda: defaultdict(set))

            for inc in incidents:
                          country = inc.get('country')
                          state = inc.get('state_province')
                          city = inc.get('city')

            if country:
                              if state:
                                                    if city:
                                                                              hierarchy[country][state].add(city)
                              else:
                                                        hierarchy[country][state]

                      # Convert sets to sorted lists
                      result = {}
        for country, states in hierarchy.items():
                      result[country] = {}
                      for state, cities in states.items():
                                        result[country][state] = sorted(list(cities))

                  self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(result).encode())
