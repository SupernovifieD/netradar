#!/usr/bin/env python3

from app import create_app
from app.services.monitor import monitor

app = create_app()

if __name__ == '__main__':
    # Start background monitoring
    monitor.start()
    
    # Run Flask app
    print("\nFlask API running on http://localhost:5001")
    print("API endpoints:")
    print("  GET  /api/status          - Current status of all services")
    print("  GET  /api/history         - Recent check history")
    print("  GET  /api/service/<name>  - History for specific service")
    print("  POST /api/monitor/start   - Start monitoring")
    print("  POST /api/monitor/stop    - Stop monitoring")
    print("  GET  /api/health          - Health check\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
