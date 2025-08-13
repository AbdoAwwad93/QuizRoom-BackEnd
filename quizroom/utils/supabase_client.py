import os
from supabase import create_client, Client
from decouple import config
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import tempfile
import os
import ffmpeg
import logging

logger = logging.getLogger(__name__)
url: str = config('SUPABASE_URL')
key: str = config('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

BUCKET_NAME = 'recordings'
CHUNK_PREFIX = 'chunk_'
CHUNK_EXTENSION = '.webm'
FINAL_VIDEO_NAME = 'final_video.mp4'
MAX_FILE_SIZE = 500 * 1024 * 1024  

def upload_chunk(quiz_id: str, student_id: str, chunk_data: bytes, sequence_number: int) -> bool:
    """
    Upload a single video chunk to Supabase storage.
    Returns True if successful, False otherwise.
    """
    try:
        chunk_name = f"{CHUNK_PREFIX}{sequence_number:04d}{CHUNK_EXTENSION}"
        file_path = f"quiz_{quiz_id}/student_{student_id}/{chunk_name}"
        
        try:
            existing = supabase.storage.from_(BUCKET_NAME).list(file_path)
            if existing:
                logger.warning(f"Chunk {sequence_number} already exists, skipping upload")
                return True
        except Exception as e:
            logger.error(f"Error checking for existing chunk: {str(e)}")
            
        res = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            chunk_data,
            {"content-type": "video/webm", "x-upsert": "false"}
        )
        return True
    except Exception as e:
        logger.error(f"Error uploading chunk {sequence_number}: {str(e)}")
        return False

def merge_video_chunks(quiz_id: str, student_id: str) -> Optional[str]:
    """
    Download all chunks for a student's quiz, merge them, and upload the final video.
    Returns the path to the final video in Supabase if successful, None otherwise.
    """
    temp_dir = tempfile.mkdtemp()
    chunk_paths = []
    
    try:
        prefix = f"quiz_{quiz_id}/student_{student_id}/"
        all_files = supabase.storage.from_(BUCKET_NAME).list(prefix)
        
        chunks = [
            f for f in all_files 
            if f['name'].startswith(CHUNK_PREFIX) 
            and f['name'].endswith(CHUNK_EXTENSION)
        ]
        
        if not chunks:
            logger.warning(f"No chunks found for quiz {quiz_id} and student {student_id}")
            logger.info(f"Available files in {prefix}: {[f['name'] for f in all_files]}")
            return None
            
        logger.info(f"Found {len(chunks)} chunks for quiz {quiz_id} and student {student_id}: {[c['name'] for c in chunks]}")
        chunks.sort(key=lambda x: int(x['name'].split('_')[-1].split('.')[0]))
            
        for i, chunk in enumerate(chunks):
            chunk_number = chunk['name'].split('_')[-1].split('.')[0].zfill(4)
            chunk_name = f"chunk_{chunk_number}.webm"
            chunk_path = os.path.join(temp_dir, chunk_name)
            full_chunk_path = f"{prefix}{chunk['name']}"
            chunk_data = supabase.storage.from_(BUCKET_NAME).download(full_chunk_path)
            
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            chunk_paths.append(chunk_path)
        
        list_file = os.path.join(temp_dir, 'file_list.txt')
        with open(list_file, 'w') as f:
            for path in sorted(chunk_paths):
                f.write(f"file '{path}'\n")
        
        output_path = os.path.join(temp_dir, FINAL_VIDEO_NAME)
        (
            ffmpeg
            .input(list_file, format='concat', safe=0)
            .output(output_path, c='copy', loglevel='error')
            .run(overwrite_output=True)
        )
        
        final_video_path = f"quiz_{quiz_id}/student_{student_id}/{FINAL_VIDEO_NAME}"
        with open(output_path, 'rb') as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                final_video_path,
                f.read(),
                {"content-type": "video/mp4"}
            )
        
        for chunk in chunks:
            full_chunk_path = f"{prefix}{chunk['name']}"
            supabase.storage.from_(BUCKET_NAME).remove([full_chunk_path])
        
        return final_video_path
        
    except Exception as e:
        logger.error(f"Error merging video chunks: {str(e)}")
        return None
    finally:
        for path in chunk_paths + [output_path] if 'output_path' in locals() else chunk_paths:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Error cleaning up {path}: {str(e)}")

def get_signed_url(quiz_id: str, student_id: str) -> Optional[str]:
    """
    Generate a signed URL for accessing the final video.
    The URL will be valid for 30 days.
    Returns None if the video doesn't exist.
    """
    try:
        file_path = f"quiz_{quiz_id}/student_{student_id}/{FINAL_VIDEO_NAME}"
        
        try:
            supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            res = supabase.storage.from_(BUCKET_NAME).create_signed_url(
                file_path,
                expires_in=2592000
            )
            return res['signedURL']
            
        except Exception as e:
            if "The resource was not found" in str(e):
                return None
            logger.error(f"Error generating signed URL: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error in get_signed_url: {str(e)}")
        return None
