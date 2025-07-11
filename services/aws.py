import os
import uuid
import boto3
import logging
from datetime import datetime
from typing import Optional, Dict
from utils.response_utils import create_response
from uuid import uuid4
import dotenv
import pytz
from botocore.config import Config

dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class AWSService:
    """
    AWS HANDLER
    """

    _s3_client = None
    AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
    AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    CLOUDFRONT_URL = os.getenv('CLOUDFRONT_URL', '')

    CONTENT_TYPE_TO_EXTENSION = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'video/mp4': '.mp4',
        'video/avi': '.avi',
        'video/mpeg': '.mpeg',
        'video/quicktime': '.mov',
        'video/x-msvideo': '.avi',
        'video/x-ms-wmv': '.wmv',
        'video/x-flv': '.flv',
        'video/x-matroska': '.mkv',
        'video/webm': '.webm',
    }

    @classmethod
    def init_s3_client(cls):
        """
        Initialize S3 client
        """
        if cls._s3_client is None:
            try:

                config = Config(
                    region_name=cls.AWS_REGION,
                    signature_version='s3v4',
                    retries={
                        'max_attempts': 3,
                        'mode': 'standard'
                    }
                )

                cls._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=cls.AWS_ACCESS_KEY,
                    aws_secret_access_key=cls.AWS_SECRET_KEY,
                    region_name=cls.AWS_REGION,
                    config=config
                )

                logger.info("S3 client initialized successfully with Signature V4")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                raise
        return cls._s3_client

    @classmethod
    def get_s3_client(cls):
        if cls._s3_client is None:
            cls.init_s3_client()
        return cls._s3_client

    @classmethod
    def generate_presigned_put_url(cls, file_name: str, content_type: str) -> dict:
        """
        Generate a presigned PUT URL for direct S3 upload

        Args:
            file_name: Name of the file
            content_type: MIME type of the file

        Returns:
            dict: Response with presigned URL and metadata
        """
        try:
            s3_client = cls.get_s3_client()

            extension = cls.get_extension_by_mime_type(content_type)
            if not extension:
                if '.' in file_name:
                    extension = os.path.splitext(file_name)[1]
                else:
                    return create_response(code=400, message="Unable to determine file extension")

            date_str = datetime.now(pytz.timezone('America/Vancouver')).strftime('%Y%m%d')
            oid = str(uuid4())
            object_key = f"zomi-dishes/{date_str}/{oid}{extension}"

            expires_in = 3600

            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': cls.AWS_BUCKET,
                    'Key': object_key,
                    'ContentType': 'octet-stream',
                    'ACL': 'public-read'
                },
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )

            # Construct URLs
            cloudfront_url = f"{cls.CLOUDFRONT_URL}{object_key}"
            s3_url = f"https://{cls.AWS_BUCKET}.s3.{cls.AWS_REGION}.amazonaws.com/{object_key}"

            logger.info(presigned_url)
            logger.info(cloudfront_url)

            correct_host = f"{cls.AWS_BUCKET}.s3.amazonaws.com"

            return create_response(
                code=0,
                data={
                    'signedUrl': presigned_url,
                    'signedHeaders': {
                        "Host": [
                            correct_host
                        ],
                        'X-Amz-Acl': [
                            "public-read"
                        ]
                    },
                    'objectKey': object_key,
                    'cloudFrontUrl': cloudfront_url,
                    's3Url': s3_url
                },
                message="Success"
            )

        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return create_response(code=500, message=f"Failed to generate presigned URL: {str(e)}")

    @classmethod
    def get_extension_by_mime_type(cls, mime_type: str) -> str:
        """Get file extension from MIME type"""
        return cls.CONTENT_TYPE_TO_EXTENSION.get(mime_type, '')
