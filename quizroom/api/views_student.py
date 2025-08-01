from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from quizroom.api.permissions import IsStudent
from quizroom.models.users.models import CustomUser
from quizroom.models.courses.models import Course
from quizroom.models.quizzes.models import Quiz, Question
from quizroom.api.serializers import CourseSerializer, QuizSerializer
from quizroom.api.serializers import StudentQuizSubmissionSerializer, QuestionSerializer
from quizroom.models.submissions.models import StudentQuizSubmission
from quizroom.models.submissions.models import StudentAnswer
from quizroom.api.serializers import StudentAnswerSerializer
from django.db import transaction
from quizroom.api.helpers import is_student_enrolled_in_course, is_student_enrolled_in_quiz
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
class StudentAllQuizzesView(APIView):
    """
    List all quizzes for courses the student is enrolled in.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        quizzes = Quiz.objects.filter(course__in=courses).select_related('course')
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)

class StudentCurrentQuizzesView(APIView):
    """
    List all currently active quizzes for the student's enrolled courses.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        now = timezone.now()
        courses = Course.objects.filter(studentcourse__student=student)
        quizzes = Quiz.objects.filter(
            course__in=courses,
            start_date__lte=now,
            end_date__gte=now
        ).select_related('course')
        serializer = QuizSerializer(quizzes, many=True, context={'student': student})
        return Response(serializer.data)

class StudentEnrolledCoursesView(APIView):
    """
    List all courses the student is enrolled in.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        data = []
        for course in courses:
            instructor_rel = course.instructorcourse_set.first()
            instructor_name = instructor_rel.instructor.name if instructor_rel else None
            course_data = CourseSerializer(course).data
            course_data['instructor_name'] = instructor_name
            data.append(course_data)
        return Response(data)

class StudentQuizSubmissionView(APIView):
    """
    Retrieve the student's submission for a specific quiz.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not is_student_enrolled_in_quiz(quiz, student):
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        submission = StudentQuizSubmission.objects.filter(student=student, quiz=quiz).first()
        if not submission:
            return Response({'submission': None})

        questions = Question.objects.filter(quiz=quiz).order_by('id')
        answers = {a.question_id: a for a in StudentAnswer.objects.filter(submission=submission)}
        questions_data = []
        for q in questions:
            answer = answers.get(q.id)
            questions_data.append({
                'question_id': q.id,
                'question_text': q.question_text,
                'answer_text': answer.answer_text if answer else '',
                'points': answer.points if (answer and submission.status in ['released']) else None,
                'feedback': answer.feedback if (answer and submission.status in ['released']) else None
            })

        response = {
            'submission_id': submission.id,
            'quiz_id': quiz.id,
            'status': submission.status,
            'questions': questions_data,
        }
        if submission.status in ['released']:
            response['grade'] = submission.grade
            response['feedback'] = submission.feedback
            response['graded_at'] = submission.graded_at
        return Response(response)

class StudentQuizQuestionsView(APIView):
    """
    Retrieve the questions for a quiz, including the student's answers if any.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not is_student_enrolled_in_quiz(quiz, student):
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
    """
    Save or update the student's answer to a quiz question.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, quiz_id, question_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            question = Question.objects.get(id=question_id, quiz=quiz)
        except (Quiz.DoesNotExist, Question.DoesNotExist):
            return Response({'detail': 'Quiz or Question not found.'}, status=404)
        if not is_student_enrolled_in_quiz(quiz, student):
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        now = timezone.now()
        if now < quiz.start_date:
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
    """
    Submit the student's quiz for grading.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    @transaction.atomic
    def post(self, request, quiz_id):
        student = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)
        if not is_student_enrolled_in_quiz(quiz, student):
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)
        now = timezone.now()
        if now < quiz.start_date:
            return Response({'detail': 'Quiz is not active.'}, status=403)
        submission, _ = StudentQuizSubmission.objects.get_or_create(student=student, quiz=quiz)
        if submission.status != 'ungraded':
            return Response({'detail': 'Submission is already finalized.'}, status=403)
        answers = request.data.get('answers', [])
        if not isinstance(answers, list):
            return Response({'detail': 'Answers must be a list.'}, status=400)
            
        for answer in answers:
            question_id = answer.get('question_id')
            answer_text = answer.get('answer_text', '').strip()
            if not question_id or not answer_text:
                return Response({'detail': 'Each answer must have question_id and answer_text.'}, status=400)
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
            except Question.DoesNotExist:
                return Response({'detail': f'Question {question_id} not found in this quiz.'}, status=404)
            ans_obj, _ = StudentAnswer.objects.get_or_create(
                submission=submission,
                question=question,
                defaults={'points': 0}
            )
            ans_obj.answer_text = answer_text
            if ans_obj.points is None:
                ans_obj.points = 0
            ans_obj.save()

        submission.status = 'grading'
        submission.submission_date = timezone.now()
        submission.save(update_fields=['status', 'submission_date'])
        return Response({'detail': 'Quiz submitted and answers saved successfully.'})

class StudentAllSubmissionsView(APIView):
    """
    List all submissions for the authenticated student.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        submissions = StudentQuizSubmission.objects.filter(student=student).select_related('quiz__course')
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK.get('PAGE_SIZE', 5)
        page = paginator.paginate_queryset(submissions, request)
        if page is not None:
            serializer = StudentQuizSubmissionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = StudentQuizSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)