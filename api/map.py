"""
Serverless API: Get map data (locations with coordinates)
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

            with_coords = [i for i in incidents if i.get('latitude') and i.get('longitude')]

        clusters = defaultdict(lambda: {'count': 0, 'lat_sum': 0, 'lon_sum': 0, 'severity_sum': 0})

        for inc in with_coords:
                      key = (inc.get('country'), inc.get('state_province'), inc.get('city'))
                      clusters[key]['count'] += 1
                      clusters[key]['lat_sum'] += float(inc['latitude'])
                      clusters[key]['lon_sum'] += float(inc['longitude'])
                      clusters[key]['severity_sum'] += inc.get('severity', 2)
                      clusters[key]['country'] = inc.get('country')
                      clusters[key]['state_province'] = inc.get('state_province')
                      clusters[key]['city'] = inc.get('city')

        cluster_list = []
        for key, data in clusters.items():
                      cluster_list.append({
                                        'country': data['country'],
                                        'state_province': data['state_province'],
                                        'city': data['city'],
                                        'latitude': data['lat_sum'] / data['count'],
                                        'longitude': data['lon_sum'] / data['count'],
                                        'incident_count': data['count'],
                                        'avg_severity': data['severity_sum'] / data['count']
                      })

        cluster_list.sort(key=lambda x: x['incident_count'], reverse=True)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {'clusters': cluster_list[:50], 'incidents': with_coords[:500]}
        self.wfile.write(json.dumps(response).encode())
