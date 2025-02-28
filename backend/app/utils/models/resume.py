from pydantic import BaseModel, AnyHttpUrl
from fastapi import Path, Query

class ResumeUploadResponse(BaseModel):
    resume_id: str

class ResumeDownloadLinkRequest(BaseModel):
    resume_id: str
    expiration: int = 3600

    @classmethod
    def query_params(
        cls,
        resume_id: str = Path(..., title="Resume ID", description="The ID of the resume to retrieve"),
        expiration: int = Query(3600, title="Expiration", description="Link expiration time in seconds (default 1 hour)")
    ):
        return cls(resume_id=resume_id, expiration=expiration)

class ResumeDownloadLinkResponse(BaseModel):
    download_link: AnyHttpUrl
