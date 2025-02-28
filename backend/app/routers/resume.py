from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
import io
import uuid
from pdf2image import convert_from_bytes
import PyPDF2
from app.utils.minio import get_minio_client, MinioClient
from app.logger import get_logger
from app.utils.models import (
    ResumeUploadResponse,
    ResumeDownloadLinkRequest,
    ResumeDownloadLinkResponse,
)
from app.config import get_settings
from app.utils.postgres.schema import ResumeUploads
from app.utils.postgres.base import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)

logger = get_logger()
settings = get_settings()

# MongoDB client setup
mongo_client = AsyncIOMotorClient(settings.get_mongo_uri())
mongo_db = mongo_client[settings.MONGO_DB]
resumes_collection = mongo_db[settings.MONGO_COLLECTION_RESUMES]

async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text content from a PDF file"""
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        
        # Reset file pointer for future use
        await file.seek(0)
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
            
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

async def save_resume_to_mongodb(resume_text: str) -> uuid.UUID:
    """Save resume text to MongoDB and return document ID"""
    doc_id = uuid.uuid4()
    await resumes_collection.insert_one({
        "_id": str(doc_id),
        "text": resume_text
    })
    return doc_id

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    resume: UploadFile = File(...),
    minio_client: MinioClient = Depends(get_minio_client),
    db: Session = Depends(get_db)
) -> ResumeUploadResponse:
    """Upload a resume to MinIO storage and process it for MongoDB storage"""
    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported"
        )
        
    try:
        # Read file content once
        content = await resume.read()
        
        # Extract text from PDF using the content
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        resume_text = ""
        
        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            resume_text += page.extract_text() + "\n"
        
        # Create a new BytesIO for MinIO upload
        file_stream = io.BytesIO(content)
        
        # Upload to MinIO using the content directly
        minio_resume_id = await minio_client.upload_file_from_bytes(file_stream, len(content), resume.filename)
        
        # Save text to MongoDB
        mongodb_resume_id = await save_resume_to_mongodb(resume_text)
        
        # Create record in PostgreSQL
        resume_upload = ResumeUploads(
            minio_resume_id=minio_resume_id,
            mongodb_resume_id=mongodb_resume_id
        )
        db.add(resume_upload)
        db.commit()
        
        return ResumeUploadResponse(
            resume_id=str(resume_upload.id)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume: {str(e)}"
        )

@router.get("/{resume_id}")
async def get_resume_download_link(
    request: ResumeDownloadLinkRequest = Depends(ResumeDownloadLinkRequest.query_params),
    minio_client: MinioClient = Depends(get_minio_client),
    db: Session = Depends(get_db)
) -> ResumeDownloadLinkResponse:
    """Get a download link for a resume stored in MinIO"""
    try:
        minio_resume_id = (
            db.query(ResumeUploads)
            .filter(ResumeUploads.id == request.resume_id)
            .first()
        )
        download_url = minio_client.get_download_link(minio_resume_id, request.expiration)
        return ResumeDownloadLinkResponse(download_link=download_url)
    except Exception as e:
        logger.error(f"Failed to generate download link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link"
        )

@router.get("/{resume_id}/preview", response_class=StreamingResponse)
async def get_resume_preview_image(
    resume_id: str = Path(..., title="Resume ID", description="The ID of the resume to preview"),
    minio_client: MinioClient = Depends(get_minio_client),
    db: Session = Depends(get_db)
):
    """Get a preview image of the first page of a resume"""
    try:
        # Get the MinIO resume ID from PostgreSQL
        resume_upload = db.query(ResumeUploads).filter(ResumeUploads.id == resume_id).first()
        
        if not resume_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
            
        minio_resume_id = resume_upload.minio_resume_id
        
        # Retrieve the PDF from MinIO
        pdf_content = minio_client.get_file_content(str(minio_resume_id))
        
        # Convert the first page of the PDF to image
        images = convert_from_bytes(pdf_content, first_page=1, last_page=1)
        
        if not images:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate preview image"
            )
        
        # Take the first page and convert to JPEG
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        # Return the image
        return StreamingResponse(
            content=img_byte_arr,
            media_type="image/jpeg"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate resume preview image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate resume preview image: {str(e)}"
        )
