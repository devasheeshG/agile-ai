from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.postgres import get_db, Users, ResumeUploads, Tasks
from app.utils.minio import get_minio_client, MinioClient
from app.config import get_settings
from app.logger import get_logger

router = APIRouter(
    prefix="/system",
    tags=["System"],
)

logger = get_logger()
settings = get_settings()

@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_all_databases(
    db: Session = Depends(get_db),
    minio_client: MinioClient = Depends(get_minio_client),
):
    """Reset all databases and storage to a clean state"""
    try:
        # 1. Clear PostgreSQL database
        logger.info("Dropping all tables in PostgreSQL")
        
        # Drop all table data
        db.query(Users).delete()
        db.query(ResumeUploads).delete()
        db.query(Tasks).delete()
        db.commit()
        
        # 2. Clear MongoDB collections
        logger.info("Clearing MongoDB collections")
        mongo_client = AsyncIOMotorClient(settings.get_mongo_uri())
        mongo_db = mongo_client[settings.MONGO_DB]
        
        # Drop specific collections
        await mongo_db[settings.MONGO_COLLECTION_RESUMES].drop()
        await mongo_db[settings.MONGO_COLLECTION_CHAT].drop()
        
        # 3. Clear MinIO storage
        logger.info("Clearing MinIO storage")
        # Get list of all objects in bucket
        objects = minio_client.client.list_objects(minio_client.bucket_name, recursive=True)
        # Delete all objects
        for obj in objects:
            minio_client.client.remove_object(minio_client.bucket_name, obj.object_name)
        
        logger.info("All databases successfully reset")
        return {"status": "success", "message": "All databases have been reset"}
        
    except Exception as e:
        logger.error(f"Error resetting databases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset databases: {str(e)}"
        )
