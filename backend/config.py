"""
SOAR Platform Configuration Management
Handles environment variables and application settings
"""
import os
from datetime import timedelta
from typing import Optional


class Config:
    """Base configuration class"""

    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False

    # Application Settings
    APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.getenv('APP_PORT', 5000))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://soar_user:soar_password@localhost:5432/soar_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True

    # Session Configuration
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_TIMEOUT', 3600)))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')

    # Security Settings
    ENABLE_RBAC = os.getenv('ENABLE_RBAC', 'True').lower() == 'true'
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 12))
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'change-this-encryption-key')

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = f"{os.getenv('API_RATE_LIMIT', 100)}/hour"
    RATELIMIT_STORAGE_URL = REDIS_URL

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')

    # Performance Settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    PLAYBOOK_TIMEOUT = int(os.getenv('PLAYBOOK_TIMEOUT', 300))  # 5 minutes

    # Metrics & Monitoring
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))

    # API Keys - Threat Intelligence
    VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
    ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY', '')
    ALIENVAULT_OTX_API_KEY = os.getenv('ALIENVAULT_OTX_API_KEY', '')
    MISP_API_KEY = os.getenv('MISP_API_KEY', '')
    MISP_URL = os.getenv('MISP_URL', '')

    # Email Security APIs
    PROOFPOINT_API_KEY = os.getenv('PROOFPOINT_API_KEY', '')
    PROOFPOINT_API_SECRET = os.getenv('PROOFPOINT_API_SECRET', '')
    MIMECAST_APP_ID = os.getenv('MIMECAST_APP_ID', '')
    MIMECAST_APP_KEY = os.getenv('MIMECAST_APP_KEY', '')
    MIMECAST_ACCESS_KEY = os.getenv('MIMECAST_ACCESS_KEY', '')
    MIMECAST_SECRET_KEY = os.getenv('MIMECAST_SECRET_KEY', '')

    # Microsoft Graph API
    MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET', '')
    MICROSOFT_TENANT_ID = os.getenv('MICROSOFT_TENANT_ID', '')

    # Active Directory / LDAP
    AD_SERVER = os.getenv('AD_SERVER', '')
    AD_DOMAIN = os.getenv('AD_DOMAIN', '')
    AD_USER = os.getenv('AD_USER', '')
    AD_PASSWORD = os.getenv('AD_PASSWORD', '')
    AD_BASE_DN = os.getenv('AD_BASE_DN', '')

    # Firewall API
    FIREWALL_API_URL = os.getenv('FIREWALL_API_URL', '')
    FIREWALL_API_KEY = os.getenv('FIREWALL_API_KEY', '')

    # EDR Configuration
    WAZUH_API_URL = os.getenv('WAZUH_API_URL', '')
    WAZUH_API_USER = os.getenv('WAZUH_API_USER', '')
    WAZUH_API_PASSWORD = os.getenv('WAZUH_API_PASSWORD', '')
    OSQUERY_API_URL = os.getenv('OSQUERY_API_URL', '')

    # SIEM Integration
    SPLUNK_HOST = os.getenv('SPLUNK_HOST', '')
    SPLUNK_PORT = int(os.getenv('SPLUNK_PORT', 8089))
    SPLUNK_API_KEY = os.getenv('SPLUNK_API_KEY', '')
    SPLUNK_INDEX = os.getenv('SPLUNK_INDEX', 'main')
    ELK_HOST = os.getenv('ELK_HOST', '')
    ELK_PORT = int(os.getenv('ELK_PORT', 9200))
    ELK_API_KEY = os.getenv('ELK_API_KEY', '')

    # Ticketing Systems
    JIRA_URL = os.getenv('JIRA_URL', '')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL', '')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', '')
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SEC')
    SERVICENOW_INSTANCE = os.getenv('SERVICENOW_INSTANCE', '')
    SERVICENOW_USERNAME = os.getenv('SERVICENOW_USERNAME', '')
    SERVICENOW_PASSWORD = os.getenv('SERVICENOW_PASSWORD', '')

    # Communication Channels
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
    SLACK_CHANNEL_SECURITY = os.getenv('SLACK_CHANNEL_SECURITY', '#security')
    SLACK_CHANNEL_INCIDENTS = os.getenv('SLACK_CHANNEL_INCIDENTS', '#incidents')

    # Email (SMTP)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'soar-platform@company.com')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'

    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration values"""
        critical_keys = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
        missing = [key for key in critical_keys if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Missing critical configuration: {', '.join(missing)}")

        return True


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def validate_config(cls) -> bool:
        """Additional production validation"""
        super().validate_config()

        # Ensure strong secret key in production
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("Production SECRET_KEY must be changed from default")

        return True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')

    config_class = config.get(env, config['default'])
    config_class.validate_config()

    return config_class
