"""API routes for file upload and transcription."""
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.core.worker import enqueue_file

router = APIRouter(prefix="/api/v1")


@router.post("/transcribe")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for transcription.
    
    Args:
        file: The file to upload.
        
    Returns:
        JSONResponse: Job information.
    """
    # Check file type
    allowed_extensions = [".mp3", ".wav", ".mp4", ".m4a", ".aac", ".flac"]
    file_extension = "." + file.filename.split(".")[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Enqueue file for processing
        job_info = enqueue_file(file_content, file.filename)
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "File uploaded and queued for transcription",
                "job_id": job_info["job_id"],
                "file_id": job_info["file_id"],
                "filename": job_info["original_filename"],
                "status": "queued"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
