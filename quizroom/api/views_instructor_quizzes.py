from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, InstructorCourse
from quizroom.models.quizzes.models import Quiz
from .serializers import QuizSerializer, QuizCreateSerializer
from django.utils import timezone

class InstructorCourseQuizzesView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def delete(self, request, quiz_id):
        instructor = request.user
        quiz = Quiz.objects.filter(id=quiz_id).first()
        if not quiz:
            return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)
        course = quiz.course
        if not Course.objects.filter(id=course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to delete this quiz.'}, status=status.HTTP_403_FORBIDDEN)
        quiz.delete()
        return Response({'detail': 'Quiz deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        instructor = request.user
        course_ids = Course.objects.filter(instructorcourse__instructor=instructor).values_list('id', flat=True)
        quizzes = Quiz.objects.filter(course_id__in=course_ids)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

    def post(self, request):
        instructor = request.user
        course = Course.objects.filter(instructorcourse__instructor=instructor).first()
        if not course:
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz = Quiz.objects.create(
            title=serializer.validated_data['title'],
            course=course,
            week_number=serializer.validated_data['week_number'],
            start_date=serializer.validated_data['start_date'],
            end_date=serializer.validated_data['end_date'],
            duration=serializer.validated_data['duration'],
            total_points=serializer.validated_data['total_points'],
            created_at=timezone.now(),
        )
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

    def patch(self, request, quiz_id):
        instructor = request.user
        quiz = Quiz.objects.filter(id=quiz_id).first()
        if not quiz:
            return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not Course.objects.filter(id=quiz.course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to edit this quiz.'}, status=status.HTTP_403_FORBIDDEN)
        allowed_fields = ['title', 'week_number', 'start_date', 'end_date', 'duration', 'total_points']
        data = request.data
        updated = False
        for field in allowed_fields:
            if field in data:
                setattr(quiz, field, data[field])
                updated = True
        if updated:
            quiz.updated_at = timezone.now()
            quiz.save()
            return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'No valid fields to update.'}, status=status.HTTP_400_BAD_REQUEST)
