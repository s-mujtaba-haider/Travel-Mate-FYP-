import os
from dotenv import load_dotenv

from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# os.environ["LANGCHAIN_TRACING_V2"]='true'

class Settings:
    PROJECT_NAME: str = "Travel Mate Api Service"
    PROJECT_VERSION: str = "1.0.0"

    DB_USERNAME: str = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", 3307)  # default postgres port is 5432
    DB_NAME: str = os.getenv("DB_NAME", "tb_data_collection_db")
    DATABASE_URL = f"postgresql+psycopg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    # os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")


settings = Settings()
