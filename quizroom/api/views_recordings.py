import logging
import os
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_ratelimit.decorators import ratelimit
from ..models import Quiz, CustomUser, VideoChunk, StudentQuizSubmission
from ..utils.supabase_client import upload_chunk, merge_video_chunks, get_signed_url

logger = logging.getLogger(__name__)

class VideoChunkUploadView(APIView):
    """
    Handle video chunk uploads from students during a quiz.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @ratelimit(key='user', rate='10/m', method='POST')
    def post(self, request, quiz_id, student_id):
        if str(request.user.id) != str(student_id) and not request.user.is_staff:
            return Response(
                {"detail": "You can only upload chunks for your own session."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            student = CustomUser.objects.get(id=student_id, role='student')
        except (Quiz.DoesNotExist, CustomUser.DoesNotExist):
            return Response(
                {"detail": "Quiz or student not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        now = timezone.now()
        if now < quiz.start_date or now > quiz.end_date:
            return Response(
                {"detail": "Quiz is not currently active."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        chunk_file = request.FILES.get('file')
        sequence_number = request.data.get('sequence_number')
        
        if not chunk_file or sequence_number is None:
            return Response(
                {"detail": "Both 'file' and 'sequence_number' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            sequence_number = int(sequence_number)
            if sequence_number < 0:
                raise ValueError("Sequence number must be non-negative")
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid sequence number."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            chunk_data = chunk_file.read()
            if not chunk_data:
                raise ValueError("Empty chunk data")
                
            success = upload_chunk(quiz_id, student_id, chunk_data, sequence_number)
            if not success:
                return Response(
                    {"detail": "Failed to upload chunk."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
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
                "message": f"Chunk {sequence_number} uploaded successfully"
            })
            
        except Exception as e:
            logger.error(f"Error processing chunk {sequence_number}: {str(e)}")
            return Response(
                {"detail": f"Error processing chunk: {str(e)}"},
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
@ratelimit(key='ip', rate='5/h', method='POST')
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
