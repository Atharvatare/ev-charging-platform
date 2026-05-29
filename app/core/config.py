import os

class Settings:
    PROJECT_NAME: str = "GoBharat EV - Premium EV Route Coordinator & Charging Station Locator Platform"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7d4b4a11f26a11394c8b2d41b8a5d3c8c24f6ae9bcfd9f4e244fe7ad54b51815")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Secure DB Configurations loaded from environment variables
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://postgres:ev_charging_password@localhost:5432/ev_charging?connect_timeout=3"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Third Party API Keys secured in backend
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "mock_stripe_key_sk_test")

settings = Settings()
