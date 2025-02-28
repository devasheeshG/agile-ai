import uuid
from io import BytesIO
from functools import lru_cache
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from app.config import get_settings
from app.logger import get_logger

logger = get_logger()
settings = get_settings()

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure that the bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            logger.error(f"MinIO error: {e}")
            raise

    # async def upload_file(self, file: UploadFile) -> str:
    #     """Upload file to MinIO and return the generated ID"""
    #     try:
    #         # Generate a unique ID for the file
    #         file_id = str(uuid.uuid4())
    #         file_name = f"{file_id}.pdf"
            
    #         # Get file content
    #         file_data = await file.read()
    #         file_size = len(file_data)
    #         file_stream = BytesIO(file_data)
            
    #         # Upload the file to MinIO
    #         self.client.put_object(
    #             self.bucket_name,
    #             file_name,
    #             file_stream,
    #             file_size,
    #             content_type="application/pdf"
    #         )
            
    #         logger.info(f"Successfully uploaded file {file_name} to bucket {self.bucket_name}")
    #         return file_id
            
    #     except S3Error as e:
    #         logger.error(f"Error uploading file to MinIO: {e}")
    #         raise
    #     finally:
    #         await file.close()

    async def upload_file_from_bytes(self, file_stream: BytesIO, file_size: int, original_filename: str = None) -> str:
        """Upload file from BytesIO stream to MinIO and return the generated ID"""
        try:
            # Generate a unique ID for the file
            file_id = str(uuid.uuid4())
            file_name = f"{file_id}.pdf"
            
            # Upload the file to MinIO
            self.client.put_object(
                self.bucket_name,
                file_name,
                file_stream,
                file_size,
                content_type="application/pdf"
            )
            
            logger.info(f"Successfully uploaded file {file_name} to bucket {self.bucket_name}")
            return file_id
            
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from MinIO"""
        try:
            file_name = f"{file_id}.pdf"
            self.client.remove_object(self.bucket_name, file_name)
            logger.info(f"Successfully deleted file {file_name} from bucket {self.bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            return False

    def get_download_link(self, file_id: str, expires=3600) -> str:
        """
        Generate a presigned URL for downloading a file
        Args:
            file_id: The ID of the file
            expires: Link expiration time in seconds (default 1 hour)
        Returns:
            Presigned URL for downloading the file
        """
        try:
            file_name = f"{file_id}.pdf"
            # Generate a presigned URL
            url = self.client.presigned_get_object(
                self.bucket_name,
                file_name,
                expires=expires
            )
            logger.info(f"Generated download link for file {file_name}")
            return url
        except S3Error as e:
            logger.error(f"Error generating download link: {e}")
            raise

    def get_file_content(self, file_id: str) -> bytes:
        """
        Get the content of a file from MinIO
        Args:
            file_id: The ID of the file
        Returns:
            The file content as bytes
        """
        try:
            file_name = f"{file_id}.pdf"
            response = self.client.get_object(self.bucket_name, file_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Successfully retrieved file {file_name} from bucket {self.bucket_name}")
            return data
        except S3Error as e:
            logger.error(f"Error retrieving file from MinIO: {e}")
            raise

@lru_cache
def get_minio_client():
    return MinioClient()
