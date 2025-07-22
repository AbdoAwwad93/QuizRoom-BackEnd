from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from quizroom.api.permissions import IsStudent
from quizroom.models.users.models import CustomUser
from quizroom.models.courses.models import Course
from quizroom.models.quizzes.models import Quiz,Question
from quizroom.api.serializers import CourseSerializer, QuizSerializer
from quizroom.api.serializers import StudentQuizSubmissionSerializer,QuestionSerializer
from quizroom.models.submissions.models import StudentQuizSubmission
class StudentAllQuizzesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        quizzes = Quiz.objects.filter(course__in=courses)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

class StudentCurrentQuizzesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        now = timezone.now()
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

class StudentQuizSubmissionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not Course.objects.filter(id=quiz.course_id, studentcourse__student=student).exists():
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        submission = StudentQuizSubmission.objects.filter(student=student, quiz=quiz).first()
        if submission:
            data = StudentQuizSubmissionSerializer(submission).data
            return Response(data)
        else:
            return Response({'submission': None})