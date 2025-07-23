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
from quizroom.models.submissions.models import StudentAnswer
from quizroom.api.serializers import StudentAnswerSerializer
from django.db import transaction

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

class StudentQuizQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not Course.objects.filter(id=quiz.course_id, studentcourse__student=student).exists():
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        now = timezone.now()
        if now < quiz.start_date or now > quiz.end_date:
            return Response({'detail': 'Quiz is not active.'}, status=403)
        questions = Question.objects.filter(quiz=quiz).order_by('id')
        submission, _ = StudentQuizSubmission.objects.get_or_create(student=student, quiz=quiz)
        answers = {a.question_id: a for a in StudentAnswer.objects.filter(submission=submission)}
        data = []
        for q in questions:
            answer = answers.get(q.id)
            data.append({
                'id': q.id,
                'question_text': q.question_text,
                'question_type': q.question_type,
                'points': q.points,
                'answer_text': answer.answer_text if answer else '',
            })
        return Response({'questions': data, 'duration': quiz.duration, 'start_date': quiz.start_date, 'end_date': quiz.end_date})

class StudentSaveAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, quiz_id, question_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            question = Question.objects.get(id=question_id, quiz=quiz)
        except (Quiz.DoesNotExist, Question.DoesNotExist):
            return Response({'detail': 'Quiz or Question not found.'}, status=404)
        if not Course.objects.filter(id=quiz.course_id, studentcourse__student=student).exists():
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        now = timezone.now()
        if now < quiz.start_date or now > quiz.end_date:
            return Response({'detail': 'Quiz is not active.'}, status=403)
        submission, _ = StudentQuizSubmission.objects.get_or_create(student=student, quiz=quiz)
        if submission.status != 'ungraded':
            return Response({'detail': 'Submission is already finalized.'}, status=403)
        answer_text = request.data.get('answer_text', '')
        if not answer_text:
            return Response({'detail': 'Answer text is required.'}, status=400)
        answer, created = StudentAnswer.objects.get_or_create(submission=submission, question=question)
        answer.answer_text = answer_text
        answer.save()
        return Response({'detail': 'Answer saved.'})

class StudentSubmitQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not Course.objects.filter(id=quiz.course_id, studentcourse__student=student).exists():
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        now = timezone.now()
        if now < quiz.start_date or now > quiz.end_date:
            return Response({'detail': 'Quiz is not active.'}, status=403)
        submission, _ = StudentQuizSubmission.objects.get_or_create(student=student, quiz=quiz)
        if submission.status != 'ungraded':
            return Response({'detail': 'Submission is already finalized.'}, status=403)
        submission.status = 'grading'
        submission.submission_date = timezone.now()
        submission.save(update_fields=['status', 'submission_date'])
        return Response({'detail': 'Quiz submitted successfully.'})