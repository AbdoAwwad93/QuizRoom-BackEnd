import os
from supabase import create_client, Client
from decouple import config
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import tempfile
import os
import ffmpeg
import logging
import shutil

logger = logging.getLogger(__name__)
url: str = config('SUPABASE_URL')
key: str = config('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

BUCKET_NAME = 'recordings'
CHUNK_PREFIX = 'chunk_'
CHUNK_EXTENSION = '.webm'
FINAL_VIDEO_NAME = 'final_video.mp4'
MAX_FILE_SIZE = 500 * 1024 * 1024  

def validate_webm_chunk(chunk_data: bytes, sequence_number: int) -> tuple[bool, str]:
    """
    Validate a WebM chunk to ensure it's not corrupted.
    Returns (is_valid, error_message)
    """
    try:
        # Basic size check
        if not chunk_data or len(chunk_data) == 0:
            return False, "Chunk is empty"
        
        if len(chunk_data) < 100:  # Minimum viable WebM chunk size
            return False, f"Chunk too small ({len(chunk_data)} bytes)"
        
        # Check WebM/Matroska magic number
        # WebM files start with EBML header: 0x1A 0x45 0xDF 0xA3
        if len(chunk_data) >= 4:
            magic = chunk_data[:4]
            if magic != b'\x1a\x45\xdf\xa3':
                # Sometimes chunks might not start with EBML header if they're continuation chunks
                # Check for common WebM patterns
                found_webm_pattern = False
                
                # Look for WebM doctype in first 100 bytes
                header_section = chunk_data[:min(100, len(chunk_data))]
                if b'webm' in header_section.lower() or b'matroska' in header_section.lower():
                    found_webm_pattern = True
                
                # For continuation chunks, look for cluster elements (0x1F 0x43 0xB6 0x75)
                if not found_webm_pattern:
                    for i in range(min(50, len(chunk_data) - 4)):
                        if chunk_data[i:i+4] == b'\x1f\x43\xb6\x75':
                            found_webm_pattern = True
                            break
                
                if not found_webm_pattern:
                    logger.warning(f"Chunk {sequence_number} doesn't appear to be valid WebM format")
                    # Don't reject it completely as it might be a continuation chunk
        
        # Check for obvious corruption patterns
        # If chunk is all zeros or all same byte, it's likely corrupted
        if len(set(chunk_data[:100])) < 5:  # Very low entropy in first 100 bytes
            return False, "Chunk appears to be corrupted (low entropy)"
        
        return True, "Chunk appears valid"
        
    except Exception as e:
        return False, f"Error validating chunk: {str(e)}"

def upload_chunk(quiz_id: str, student_id: str, chunk_data: bytes, sequence_number: int) -> bool:
    """
    Upload a single video chunk to Supabase storage with validation.
    Returns True if successful, False otherwise.
    """
    try:
        chunk_name = f"{CHUNK_PREFIX}{sequence_number:04d}{CHUNK_EXTENSION}"
        file_path = f"quiz_{quiz_id}/student_{student_id}/{chunk_name}"
        
        # Validate chunk data before upload
        is_valid, validation_message = validate_webm_chunk(chunk_data, sequence_number)
        if not is_valid:
            logger.error(f"Chunk {sequence_number} validation failed: {validation_message}")
            return False
        
        logger.info(f"Chunk {sequence_number} validation passed: {validation_message} ({len(chunk_data)} bytes)")
        
        try:
            existing = supabase.storage.from_(BUCKET_NAME).list(file_path)
            if existing:
                logger.warning(f"Chunk {sequence_number} already exists, skipping upload")
                return True
        except Exception as e:
            logger.error(f"Error checking for existing chunk: {str(e)}")
            
        # Upload chunk to storage
        res = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            chunk_data,
            {"content-type": "video/webm", "x-upsert": "false"}
        )
        
        # Verify upload by checking file exists and has correct size
        try:
            uploaded_files = supabase.storage.from_(BUCKET_NAME).list(f"quiz_{quiz_id}/student_{student_id}/")
            uploaded_chunk = next((f for f in uploaded_files if f['name'] == chunk_name), None)
            
            if uploaded_chunk:
                uploaded_size = uploaded_chunk.get('metadata', {}).get('size', 0)
                if uploaded_size != len(chunk_data):
                    logger.error(f"Upload size mismatch for chunk {sequence_number}: expected {len(chunk_data)}, got {uploaded_size}")
                    return False
                else:
                    logger.info(f"Chunk {sequence_number} uploaded successfully and verified ({uploaded_size} bytes)")
            else:
                logger.error(f"Chunk {sequence_number} not found after upload")
                return False
                
        except Exception as e:
            logger.warning(f"Could not verify upload of chunk {sequence_number}: {str(e)}")
            # Don't fail the upload if we can't verify - the upload might have succeeded
        
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
        
        # Download and validate each chunk
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_number = chunk['name'].split('_')[-1].split('.')[0].zfill(4)
                chunk_name = f"chunk_{chunk_number}.webm"
                chunk_path = os.path.join(temp_dir, chunk_name)
                full_chunk_path = f"{prefix}{chunk['name']}"
                
                logger.info(f"Downloading chunk {chunk_number} from {full_chunk_path}")
                chunk_data = supabase.storage.from_(BUCKET_NAME).download(full_chunk_path)
                
                # Validate chunk data
                if not chunk_data or len(chunk_data) == 0:
                    logger.error(f"Chunk {chunk_number} is empty, skipping")
                    continue
                    
                # Check expected size from metadata if available
                expected_size = chunk.get('metadata', {}).get('size')
                if expected_size and len(chunk_data) != expected_size:
                    logger.warning(f"Chunk {chunk_number} size mismatch: got {len(chunk_data)}, expected {expected_size}")
                
                with open(chunk_path, 'wb') as f:
                    f.write(chunk_data)
                    
                # Verify the file was written correctly
                if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) != len(chunk_data):
                    logger.error(f"Failed to write chunk {chunk_number} correctly")
                    continue
                    
                chunk_paths.append(chunk_path)
                valid_chunks.append(chunk)
                logger.info(f"Successfully downloaded chunk {chunk_number} ({len(chunk_data)} bytes)")
                
            except Exception as e:
                logger.error(f"Error downloading chunk {chunk['name']}: {str(e)}")
                continue
        
        if not valid_chunks:
            logger.error("No valid chunks downloaded")
            return None
        logger.info(f"Successfully downloaded {len(valid_chunks)} valid chunks")
        
        # Try multiple merging strategies
        output_path = os.path.join(temp_dir, FINAL_VIDEO_NAME)
        merge_success = False
        
        # Strategy 1: Direct concatenation with concat demuxer (best for identical formats)
        try:
            logger.info("Attempting FFmpeg concat demuxer merge...")
            list_file = os.path.join(temp_dir, 'file_list.txt')
            with open(list_file, 'w') as f:
                for path in sorted(chunk_paths):
                    f.write(f"file '{path}'\n")
            
            (
                ffmpeg
                .input(list_file, format='concat', safe=0)
                .output(output_path, c='copy', loglevel='warning')
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
            
            # Verify the output file was created and is not empty
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("Concat demuxer merge successful")
                merge_success = True
            else:
                logger.warning("Concat demuxer produced empty file")
                
        except ffmpeg.Error as e:
            logger.warning(f"Concat demuxer failed: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            logger.warning(f"Concat demuxer failed: {str(e)}")
        
        # Strategy 2: Re-encode and concatenate (slower but more compatible)
        if not merge_success:
            try:
                logger.info("Attempting FFmpeg filter_complex merge with re-encoding...")
                
                # Create input streams for each chunk
                inputs = [ffmpeg.input(path) for path in sorted(chunk_paths)]
                
                # Concatenate using filter_complex
                (
                    ffmpeg
                    .concat(*inputs, v=1, a=1)
                    .output(output_path, vcodec='libx264', acodec='aac', loglevel='warning')
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info("Filter_complex merge successful")
                    merge_success = True
                else:
                    logger.warning("Filter_complex produced empty file")
                    
            except ffmpeg.Error as e:
                logger.warning(f"Filter_complex merge failed: {e.stderr.decode() if e.stderr else str(e)}")
            except Exception as e:
                logger.warning(f"Filter_complex merge failed: {str(e)}")
        
        # Strategy 3: Copy first chunk if all else fails
        if not merge_success and chunk_paths:
            try:
                logger.warning("All merge strategies failed, copying first chunk only")
                shutil.copy2(chunk_paths[0], output_path)
                merge_success = True
                logger.info("Copied first chunk as fallback")
            except Exception as e:
                logger.error(f"Failed to copy first chunk: {str(e)}")
        
        if not merge_success:
            logger.error("All merge strategies failed")
            return None
            
        # Verify final output
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("Final output file is missing or empty")
            return None
            
        logger.info(f"Final video created successfully ({os.path.getsize(output_path)} bytes)")
        
        # Upload the final video
        try:
            final_video_path = f"quiz_{quiz_id}/student_{student_id}/{FINAL_VIDEO_NAME}"
            with open(output_path, 'rb') as f:
                final_video_data = f.read()
                supabase.storage.from_(BUCKET_NAME).upload(
                    final_video_path,
                    final_video_data,
                    {"content-type": "video/mp4"}
                )
            
            logger.info(f"Final video uploaded successfully ({len(final_video_data)} bytes)")
            
            # Only delete chunks after successful upload
            try:
                logger.info("Cleaning up chunk files from storage...")
                for chunk in valid_chunks:  # Only delete chunks that were actually used
                    full_chunk_path = f"{prefix}{chunk['name']}"
                    supabase.storage.from_(BUCKET_NAME).remove([full_chunk_path])
                    logger.debug(f"Deleted chunk: {full_chunk_path}")
                logger.info(f"Successfully deleted {len(valid_chunks)} chunk files")
            except Exception as e:
                logger.warning(f"Error deleting some chunks: {str(e)}")
                # Don't fail the entire operation if cleanup fails
            
            return final_video_path
            
        except Exception as e:
            logger.error(f"Error uploading final video: {str(e)}")
            return None
        
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

def get_chunk_validation_report(quiz_id: str, student_id: str) -> dict:
    """
    Generate a validation report for all chunks for a student's quiz.
    This helps debug chunk upload issues.
    """
    try:
        prefix = f"quiz_{quiz_id}/student_{student_id}/"
        all_files = supabase.storage.from_(BUCKET_NAME).list(prefix)
        
        chunks = [
            f for f in all_files 
            if f['name'].startswith(CHUNK_PREFIX) 
            and f['name'].endswith(CHUNK_EXTENSION)
        ]
        
        if not chunks:
            return {
                "status": "no_chunks",
                "message": "No chunks found",
                "available_files": [f['name'] for f in all_files]
            }
        
        chunks.sort(key=lambda x: int(x['name'].split('_')[-1].split('.')[0]))
        
        validation_results = []
        for chunk in chunks:
            try:
                chunk_number = chunk['name'].split('_')[-1].split('.')[0]
                full_chunk_path = f"{prefix}{chunk['name']}"
                
                # Download and validate chunk
                chunk_data = supabase.storage.from_(BUCKET_NAME).download(full_chunk_path)
                is_valid, validation_message = validate_webm_chunk(chunk_data, int(chunk_number))
                
                validation_results.append({
                    "chunk_number": int(chunk_number),
                    "chunk_name": chunk['name'],
                    "size": len(chunk_data) if chunk_data else 0,
                    "expected_size": chunk.get('metadata', {}).get('size', 0),
                    "is_valid": is_valid,
                    "validation_message": validation_message,
                    "uploaded_at": chunk.get('created_at', 'unknown')
                })
                
            except Exception as e:
                validation_results.append({
                    "chunk_number": int(chunk['name'].split('_')[-1].split('.')[0]),
                    "chunk_name": chunk['name'],
                    "size": 0,
                    "expected_size": chunk.get('metadata', {}).get('size', 0),
                    "is_valid": False,
                    "validation_message": f"Error downloading/validating: {str(e)}",
                    "uploaded_at": chunk.get('created_at', 'unknown')
                })
        
        valid_chunks = [r for r in validation_results if r['is_valid']]
        invalid_chunks = [r for r in validation_results if not r['is_valid']]
        
        return {
            "status": "success",
            "total_chunks": len(validation_results),
            "valid_chunks": len(valid_chunks),
            "invalid_chunks": len(invalid_chunks),
            "validation_results": validation_results,
            "summary": {
                "has_valid_chunks": len(valid_chunks) > 0,
                "all_chunks_valid": len(invalid_chunks) == 0,
                "can_merge": len(valid_chunks) > 0
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating validation report: {str(e)}"
        }

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
