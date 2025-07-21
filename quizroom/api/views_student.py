from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from quizroom.api.permissions import IsStudent
from quizroom.models.users.models import CustomUser
from quizroom.models.courses.models import Course
from quizroom.models.quizzes.models import Quiz
from quizroom.api.serializers import CourseSerializer, QuizSerializer

class StudentCurrentQuizzesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        now = timezone.now()
        # Get all enrolled courses for the student using StudentCourse
        courses = Course.objects.filter(studentcourse__student=student)
        quizzes = Quiz.objects.filter(
            course__in=courses,
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

class StudentEnrolledCoursesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
