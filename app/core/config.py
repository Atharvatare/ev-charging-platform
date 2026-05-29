import os

class Settings:
    PROJECT_NAME: str = "Smart EV Charging & Route Optimizer"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "7d4b4a11f26a11394c8b2d41b8a5d3c8c24f6ae9bcfd9f4e244fe7ad54b51815")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # DB Configurations
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://postgres:ev_charging_password@localhost:5432/ev_charging"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Third Party Mock Options
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "mock_stripe_key_sk_test")

settings = Settings()
