#!/usr/bin/env python3
"""
SOAR Platform Initialization Script
Initializes database and default data
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.models import db
from backend.auth import init_default_users
from backend.orchestrator import initialize_default_playbooks


def init_database(app):
    """Initialize database tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created")


def init_users(app):
    """Initialize default users"""
    print("Initializing default users...")
    init_default_users(app)
    print("✓ Default users created")


def init_playbooks(app):
    """Initialize default playbooks"""
    print("Initializing default playbooks...")
    initialize_default_playbooks(app)
    print("✓ Default playbooks initialized")


def main():
    """Main initialization function"""
    print("=" * 50)
    print("SOAR Platform Initialization")
    print("=" * 50)

    # Create Flask app
    app = create_app()

    # Initialize components
    init_database(app)
    init_users(app)
    init_playbooks(app)

    print("\n" + "=" * 50)
    print("Initialization Complete!")
    print("=" * 50)
    print("\nDefault Credentials:")
    print("  Admin:     admin / changeme")
    print("  Commander: commander / changeme")
    print("  Analyst:   analyst / changeme")
    print("\n⚠️  IMPORTANT: Change default passwords immediately!")
    print("\nStart the application with:")
    print("  python backend/app.py")
    print("  OR")
    print("  docker-compose up")
    print("=" * 50)


if __name__ == '__main__':
    main()
