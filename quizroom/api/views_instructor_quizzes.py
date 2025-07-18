from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, InstructorCourse
from quizroom.models.quizzes.models import Quiz
from .serializers import QuizSerializer

class InstructorCourseQuizzesView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        course_ids = Course.objects.filter(instructorcourse__instructor=instructor).values_list('id', flat=True)
        quizzes = Quiz.objects.filter(course_id__in=course_ids)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)
