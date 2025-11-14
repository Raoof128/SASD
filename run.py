#!/usr/bin/env python3
"""
SOAR Platform Entrypoint Script
Starts the Flask application with proper configuration
"""
import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from backend.app import create_app

if __name__ == '__main__':
    # Create Flask app
    app = create_app()

    # Get configuration
    host = app.config.get('APP_HOST', '0.0.0.0')
    port = app.config.get('APP_PORT', 5000)
    debug = app.config.get('DEBUG', False)

    print("=" * 60)
    print("SOAR Platform Starting...")
    print("=" * 60)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)
    print(f"\n🌐 Access the platform at: http://{host}:{port}")
    print(f"📊 Dashboard: http://{host}:{port}/")
    print(f"💊 Health Check: http://{host}:{port}/health")
    print(f"📡 API Status: http://{host}:{port}/api/v1/status")
    print("\n⚠️  Default credentials: admin / changeme")
    print("=" * 60)

    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug
    )
