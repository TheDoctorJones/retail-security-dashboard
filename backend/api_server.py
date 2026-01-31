"""
REST API Server for Retail Security Dashboard
Provides endpoints for the React frontend
Serves static files in production
"""
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.database import (
    get_incidents, get_trend_data, get_location_summary,
    get_incident_types, get_locations_hierarchy, get_stats,
    get_connection, get_cursor, USE_POSTGRES, _get_placeholder
)

# Determine static folder path
STATIC_FOLDER = Path(__file__).parent.parent / 'frontend' / 'dist'
app = Flask(__name__, static_folder=str(STATIC_FOLDER), static_url_path='')
CORS(app)

# Check if we're in production
IS_PRODUCTION = os.environ.get('RENDER', False) or os.environ.get('PRODUCTION', False)


# Serve React app
@app.route('/')
def serve():
    if STATIC_FOLDER.exists() and (STATIC_FOLDER / 'index.html').exists():
        return send_from_directory(str(STATIC_FOLDER), 'index.html')
    return jsonify({'message': 'API running. Build frontend with: cd frontend && npm run build'})


@app.route('/<path:path>')
def serve_static(path):
    # Don't intercept /api routes
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    if STATIC_FOLDER.exists():
        file_path = STATIC_FOLDER / path
        if file_path.exists():
            return send_from_directory(str(STATIC_FOLDER), path)
        # SPA fallback
        if (STATIC_FOLDER / 'index.html').exists():
            return send_from_directory(str(STATIC_FOLDER), 'index.html')

    return jsonify({'error': 'Not found'}), 404


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': 'postgresql' if USE_POSTGRES else 'sqlite'
    })


@app.route('/api/stats')
def stats():
    """Get overall dashboard statistics"""
    return jsonify(get_stats())


@app.route('/api/incidents')
def incidents():
    """Get incidents with filtering"""
    params = {
        'limit': request.args.get('limit', 100, type=int),
        'offset': request.args.get('offset', 0, type=int),
        'country': request.args.get('country'),
        'state_province': request.args.get('state'),
        'city': request.args.get('city'),
        'incident_type': request.args.get('type'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'min_severity': request.args.get('min_severity', type=int)
    }
    params = {k: v for k, v in params.items() if v is not None}

    incidents_list = get_incidents(**params)

    return jsonify({
        'incidents': incidents_list,
        'count': len(incidents_list),
        'limit': params.get('limit', 100),
        'offset': params.get('offset', 0)
    })


@app.route('/api/incidents/<int:incident_id>')
def incident_detail(incident_id):
    """Get single incident details"""
    ph = _get_placeholder()
    with get_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(f"SELECT * FROM incidents WHERE id = {ph}", (incident_id,))
        row = cursor.fetchone()

    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Incident not found'}), 404


@app.route('/api/trends')
def trends():
    """Get trend data for charts"""
    days = request.args.get('days', 30, type=int)
    country = request.args.get('country')
    state = request.args.get('state')
    group_by = request.args.get('group_by', 'day')

    data = get_trend_data(days=days, country=country, state_province=state, group_by=group_by)

    # Pivot data for easier charting
    pivoted = {}
    for row in data:
        period = row['period']
        if period not in pivoted:
            pivoted[period] = {'period': period, 'total': 0}
        inc_type = row['incident_type'] or 'unknown'
        pivoted[period][inc_type] = row['count']
        pivoted[period]['total'] += row['count']

    return jsonify({
        'trends': list(pivoted.values()),
        'raw': data,
        'days': days,
        'group_by': group_by
    })


@app.route('/api/map')
def map_data():
    """Get location summary for map visualization"""
    locations = get_location_summary()

    with get_connection() as conn:
        cursor = get_cursor(conn)

        if USE_POSTGRES:
            cursor.execute("""
                SELECT id, title, description, incident_type, severity,
                       city, state_province, country, latitude, longitude,
                       incident_date, url
                FROM incidents
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                  AND incident_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY incident_date DESC
                LIMIT 500
            """)
        else:
            cursor.execute("""
                SELECT id, title, description, incident_type, severity,
                       city, state_province, country, latitude, longitude,
                       incident_date, url
                FROM incidents
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
                  AND incident_date >= date('now', '-30 days')
                ORDER BY incident_date DESC
                LIMIT 500
            """)

        recent_incidents = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'clusters': locations,
        'incidents': recent_incidents
    })


@app.route('/api/locations')
def locations():
    """Get hierarchical location data for filters"""
    hierarchy = get_locations_hierarchy()
    return jsonify(hierarchy)


@app.route('/api/types')
def incident_types():
    """Get list of incident types"""
    types = get_incident_types()
    return jsonify({'types': types})


@app.route('/api/sources')
def sources():
    """Get data source status"""
    with get_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            SELECT name, source_type, last_scraped, last_success, total_incidents
            FROM sources
            ORDER BY last_scraped DESC
        """)
        sources_list = [dict(row) for row in cursor.fetchall()]

    return jsonify({'sources': sources_list})


@app.route('/api/search')
def search():
    """Search incidents by text"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)
    ph = _get_placeholder()

    if not query:
        return jsonify({'error': 'Search query required'}), 400

    with get_connection() as conn:
        cursor = get_cursor(conn)
        if USE_POSTGRES:
            cursor.execute(f"""
                SELECT * FROM incidents
                WHERE title ILIKE {ph} OR description ILIKE {ph}
                ORDER BY incident_date DESC
                LIMIT {ph}
            """, (f'%{query}%', f'%{query}%', limit))
        else:
            cursor.execute(f"""
                SELECT * FROM incidents
                WHERE title LIKE {ph} OR description LIKE {ph}
                ORDER BY incident_date DESC
                LIMIT {ph}
            """, (f'%{query}%', f'%{query}%', limit))

        results = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })


@app.route('/api/retailers')
def retailers():
    """Get incidents by retailer mention"""
    with get_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            SELECT retailer_mentioned, COUNT(*) as count
            FROM incidents
            WHERE retailer_mentioned IS NOT NULL
              AND retailer_mentioned != '[]'
            GROUP BY retailer_mentioned
            ORDER BY count DESC
            LIMIT 20
        """)
        results = [dict(row) for row in cursor.fetchall()]

    return jsonify({'retailers': results})


@app.route('/api/severity-distribution')
def severity_distribution():
    """Get severity distribution for charts"""
    with get_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute("""
            SELECT severity, COUNT(*) as count, incident_type
            FROM incidents
            WHERE severity IS NOT NULL
            GROUP BY severity, incident_type
            ORDER BY severity
        """)
        results = [dict(row) for row in cursor.fetchall()]

    return jsonify({'distribution': results})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not IS_PRODUCTION
    print(f"Starting Retail Security Dashboard API Server on port {port}...")
    if not IS_PRODUCTION:
        print("Development mode - API at http://localhost:5000")
    app.run(debug=debug, port=port, host='0.0.0.0')
