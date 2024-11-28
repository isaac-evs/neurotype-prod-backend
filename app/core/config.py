from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    PROJECT_NAME: str = "NeuroType"
    SQLALCHEMY_DATABASE_URI: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-2"
    AWS_S3_BUCKET_NAME: str

    GOOGLE_CLIENT_ID: str

    class Config:
        case_sensitive = True

settings = Settings()
