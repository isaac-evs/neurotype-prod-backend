import boto3
from botocore.exceptions import NoCredentialsError
import uuid

from app.core.config import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def upload_file_to_s3(file, bucket_name, object_name=None):
    if object_name is None:
        object_name = str(uuid.uuid4())
    try:
        s3_client.upload_fileobj(
            file.file,
            bucket_name,
            object_name,
            ExtraArgs={"ContentType": file.content_type}
        )
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        return s3_url
    except NoCredentialsError:
        raise Exception("Credentials not available")
