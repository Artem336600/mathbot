import uuid
import aioboto3
from loguru import logger
from bot.config import settings

class StorageService:
    @staticmethod
    def _get_session() -> aioboto3.Session:
        return aioboto3.Session()

    @staticmethod
    def _client_kwargs() -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": settings.s3_endpoint_url,
            "aws_access_key_id": settings.s3_access_key,
            "aws_secret_access_key": settings.s3_secret_key,
        }

    @staticmethod
    async def upload_file(file_key: str, data: bytes, content_type: str) -> str:
        size = len(data)
        logger.debug(f"[STORAGE] uploading key={file_key} size={size}B content_type={content_type}")
        try:
            session = StorageService._get_session()
            async with session.client(**StorageService._client_kwargs()) as s3:
                await s3.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=file_key,
                    Body=data,
                    ContentType=content_type
                )
            logger.info(f"[STORAGE] uploaded key={file_key}")
            return file_key
        except Exception as e:
            logger.error(f"[STORAGE] upload failed key={file_key}: {e}")
            raise e

    @staticmethod
    async def delete_file(file_key: str) -> bool:
        logger.debug(f"[STORAGE] deleting key={file_key}")
        try:
            session = StorageService._get_session()
            async with session.client(**StorageService._client_kwargs()) as s3:
                await s3.delete_object(
                    Bucket=settings.s3_bucket_name,
                    Key=file_key
                )
            logger.info(f"[STORAGE] deleted key={file_key}")
            return True
        except Exception as e:
            logger.error(f"[STORAGE] delete failed key={file_key}: {e}")
            return False

    @staticmethod
    async def get_file(file_key: str) -> bytes | None:
        try:
            session = StorageService._get_session()
            async with session.client(**StorageService._client_kwargs()) as s3:
                resp = await s3.get_object(Bucket=settings.s3_bucket_name, Key=file_key)
                return await resp['Body'].read()
        except Exception as e:
            logger.error(f"[STORAGE] get_file failed key={file_key}: {e}")
            return None

    @staticmethod
    async def get_presigned_url(file_key: str, expires: int = 3600) -> str:
        try:
            session = StorageService._get_session()
            # If using MinIO locally, presigned URL should use the internal network 
            # if requested from backend, but the client needs public URL.
            # aioboto3 will generate URL with endpoint_url. 
            # So let's override it or replace it afterwards.
            
            client_kwargs = StorageService._client_kwargs()
            async with session.client(**client_kwargs) as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.s3_bucket_name, 'Key': file_key},
                    ExpiresIn=expires
                )
            
            # Replace internal endpoint with public URL if needed
            if settings.s3_public_url and settings.s3_endpoint_url != settings.s3_public_url:
                url = url.replace(settings.s3_endpoint_url, settings.s3_public_url)
                
            return url
        except Exception as e:
            logger.error(f"[STORAGE] get_presigned_url failed key={file_key}: {e}")
            return ""

    @staticmethod
    def generate_key(entity_type: str, entity_id: int, filename: str) -> str:
        # e.g. "topic/1/123e4567-e89b-12d3.../image.png"
        unique_id = str(uuid.uuid4())
        return f"{entity_type}/{entity_id}/{unique_id}/{filename}"
