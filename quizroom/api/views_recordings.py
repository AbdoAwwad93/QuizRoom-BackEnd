import logging
import os
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from ..models import Quiz, CustomUser, VideoChunk, StudentQuizSubmission
from ..utils.supabase_client import upload_chunk, merge_video_chunks, get_signed_url

logger = logging.getLogger(__name__)

class VideoChunkUploadView(APIView):
    """
    Handle video chunk uploads from students during a quiz.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # Increase the max upload size to 100MB
    max_upload_size = 100 * 1024 * 1024  # 100MB
    
    def validate_upload_size(self, request):
        if request.content_type == '':
            return False
        if request.content_type.startswith('multipart'):
            try:
                request.META['CONTENT_LENGTH'] = str(self.max_upload_size + 1)
                return int(request.META['CONTENT_LENGTH']) <= self.max_upload_size
            except (ValueError, KeyError):
                return False
        return True
    
    @method_decorator(ratelimit(key='user', rate='100/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
        
    def post(self, request, quiz_id, student_id):
        try:
            # Authentication and validation
            if str(request.user.id) != str(student_id) and not request.user.is_staff:
                return Response(
                    {"status": "error", "message": "You can only upload chunks for your own session."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Get quiz and student
            quiz = Quiz.objects.get(id=quiz_id)
            student = CustomUser.objects.get(id=student_id, role='student')
            
            # Check quiz time window
            now = timezone.now()
            if now < quiz.start_date or now > quiz.end_date:
                return Response(
                    {"status": "error", "message": "Quiz is not currently active."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate content length first
            if not self.validate_upload_size(request):
                return Response(
                    {"status": "error", "message": f"File too large. Maximum size is {self.max_upload_size} bytes."},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )
                
# Get chunk file and sequence number
            try:
                chunk_file = request.FILES['file']  # Use direct access to trigger proper error
                sequence_number = request.data.get('sequence_number')
                if not sequence_number:
                    raise KeyError("sequence_number is required")
            except KeyError as e:
                return Response(
                    {"status": "error", "message": f"Missing required field: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate inputs
            if not chunk_file:
                return Response(
                    {"status": "error", "message": "No file was uploaded."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                sequence_number = int(sequence_number)
                if sequence_number < 0:
                    raise ValueError("Sequence number must be non-negative")
            except (ValueError, TypeError):
                return Response(
                    {"status": "error", "message": "Invalid sequence number."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Read chunk data
            try:
                chunk_data = chunk_file.read()
                if not chunk_data:
                    raise ValueError("Empty chunk data")
                
                # Upload chunk to storage
                success = upload_chunk(quiz_id, student_id, chunk_data, sequence_number)
                if not success:
                    return Response(
                        {"status": "error", "message": "Failed to upload chunk to storage."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Update or create chunk record
                VideoChunk.objects.update_or_create(
                    quiz=quiz,
                    student=student,
                    sequence_number=sequence_number,
                    defaults={
                        'chunk_path': f"quiz_{quiz_id}/student_{student_id}/chunk_{sequence_number:04d}.webm",
                        'size': len(chunk_data),
                        'is_processed': False
                    }
                )
                
                return Response({
                    "status": "success",
                    "message": f"Chunk {sequence_number} uploaded successfully",
                    "chunk_id": sequence_number
                })
                
            except Exception as e:
                logger.error(f"Error processing chunk {sequence_number}: {str(e)}", exc_info=True)
                return Response(
                    {"status": "error", "message": f"Error processing chunk: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Quiz.DoesNotExist:
            return Response(
                {"status": "error", "message": "Quiz not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except CustomUser.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error in chunk upload: {str(e)}", exc_info=True)
            return Response(
                {"status": "error", "message": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VideoRecordingView(APIView):
    """
    Handle retrieval of video recordings by instructors.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, quiz_id, student_id):
        if not request.user.is_staff and not hasattr(request.user, 'instructorprofile'):
            return Response(
                {"detail": "Only instructors can access recordings."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            student = CustomUser.objects.get(id=student_id, role='student')
        except (Quiz.DoesNotExist, CustomUser.DoesNotExist):
            return Response(
                {"detail": "Quiz or student not found."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if timezone.now() < quiz.end_date:
            return Response(
                {"detail": "Quiz has not ended yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        signed_url = get_signed_url(quiz_id, student_id)
        if not signed_url:
            return Response(
                {"detail": "No recording found for this quiz session."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response({
            "status": "success",
            "video_url": signed_url,
            "expires_in": 3600 
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='ip', rate='100/h', method='POST')
def merge_videos(request, quiz_id, student_id):
    """
    Endpoint to trigger video merging for a student's quiz session.
    This should be called when a quiz ends.
    """
    if not request.user.is_staff:
        return Response(
            {"detail": "Only staff can trigger video merging."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        student = CustomUser.objects.get(id=student_id, role='student')
    except (Quiz.DoesNotExist, CustomUser.DoesNotExist):
        return Response(
            {"detail": "Quiz or student not found."},
            status=status.HTTP_404_NOT_FOUND
        )
        
    if timezone.now() < quiz.end_date:
        return Response(
            {"detail": "Cannot merge videos before quiz ends."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    submission = StudentQuizSubmission.objects.filter(
        quiz=quiz,
        student=student
    ).first()
    
    if submission and submission.screen_recording_path:
        return Response({
            "status": "already_merged",
            "message": "Videos have already been merged for this submission."
        })
        
    try:
        video_path = merge_video_chunks(quiz_id, student_id)
        if not video_path:
            return Response(
                {"detail": "No video chunks found to merge."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if submission:
            submission.screen_recording_path = video_path
            submission.save()
            
        VideoChunk.objects.filter(
            quiz=quiz,
            student=student,
            is_processed=False
        ).update(is_processed=True)
        
        return Response({
            "status": "success",
            "message": "Videos merged successfully",
            "video_path": video_path
        })
        
    except Exception as e:
        logger.error(f"Error merging videos: {str(e)}")
        return Response(
            {"detail": f"Error merging videos: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
