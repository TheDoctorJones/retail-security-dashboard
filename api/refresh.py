from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
      def do_POST(self):
                try:
                              # Get GitHub token from environment variable
                              github_token = os.environ.get('GITHUB_TOKEN')

            if not github_token:
                              self.send_response(500)
                              self.send_header('Content-Type', 'application/json')
                              self.send_header('Access-Control-Allow-Origin', '*')
                              self.end_headers()
                              self.wfile.write(json.dumps({
                                  'success': False,
                                  'error': 'GitHub token not configured'
                              }).encode())
                              return

            # Trigger GitHub Actions workflow
            url = 'https://api.github.com/repos/TheDoctorJones/retail-security-dashboard/actions/workflows/scraper.yml/dispatches'

            data = json.dumps({'ref': 'main'}).encode('utf-8')

            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Authorization', f'token {github_token}')
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('Content-Type', 'application/json')
            req.add_header('User-Agent', 'Retail-Security-Dashboard')

            try:
                              urllib.request.urlopen(req)
                              self.send_response(200)
                              self.send_header('Content-Type', 'application/json')
                              self.send_header('Access-Control-Allow-Origin', '*')
                              self.end_headers()
                              self.wfile.write(json.dumps({
                                  'success': True,
                                  'message': 'Scraper triggered successfully. Data will update in a few minutes.'
                              }).encode())
except urllib.error.HTTPError as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                                      'success': False,
                                      'error': f'GitHub API error: {e.code}'
                }).encode())

except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                              'success': False,
                              'error': str(e)
            }).encode())

    def do_OPTIONS(self):
              self.send_response(200)
              self.send_header('Access-Control-Allow-Origin', '*')
              self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
              self.send_header('Access-Control-Allow-Headers', 'Content-Type')
              self.end_headers()
