"""
Serverless API: Get data source information
"""
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from collections import Counter

DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"
META_FILE = Path(__file__).parent.parent / "data" / "meta.json"

def load_incidents():
      if DATA_FILE.exists():
                with open(DATA_FILE, 'r') as f:
                              return json.load(f)
                      return []

  def load_meta():
        if META_FILE.exists():
                  with open(META_FILE, 'r') as f:
                                return json.load(f)
                        return {}

    class handler(BaseHTTPRequestHandler):
          def do_GET(self):
                    incidents = load_incidents()
                    meta = load_meta()

              source_counts = Counter(i.get('source_name') for i in incidents)

        sources = []
        for name, count in source_counts.most_common():
                      sources.append({
                                        'name': name,
                                        'total_incidents': count,
                                        'last_scraped': meta.get('last_scraped'),
                                        'last_success': True
                      })

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps({'sources': sources}).encode())
