from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from quizroom.models.submissions.models import StudentQuizSubmission, StudentAnswer
from quizroom.models.quizzes.models import Quiz
from quizroom.api.permissions import IsInstructor
from quizroom.api.serializers import *
from django.db import transaction

class InstructorQuizSubmissionsListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        submissions = StudentQuizSubmission.objects.filter(
            quiz__id=quiz_id,
            quiz__course__instructorcourse__instructor=instructor
        ).select_related('student', 'quiz')
        serializer = StudentQuizSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

class InstructorSubmissionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get(self, request, submission_id):
        instructor = request.user
        try:
            submission = StudentQuizSubmission.objects.select_related('student', 'quiz').get(
                id=submission_id,
                quiz__course__instructorcourse__instructor=instructor
            )
        except StudentQuizSubmission.DoesNotExist:
            return Response({'detail': 'Submission not found.'}, status=404)
        serializer = StudentQuizSubmissionSerializer(submission)
        return Response(serializer.data)

class InstructorGradeAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    @transaction.atomic
    def patch(self, request, answer_id):
        instructor = request.user
        try:
            answer = StudentAnswer.objects.select_related('question', 'submission', 'submission__quiz').get(
                id=answer_id,
                submission__quiz__course__instructorcourse__instructor=instructor
            )
        except StudentAnswer.DoesNotExist:
            return Response({'detail': 'Answer not found.'}, status=404)
        points = request.data.get('points')
        feedback = request.data.get('feedback', '')
        if points is None or not (0 <= points <= answer.question.points):
            return Response({'detail': f'Points must be between 0 and {answer.question.points}.'}, status=400)
        answer.points = points
        answer.feedback = feedback
        answer.save()
        submission = answer.submission
        answers = StudentAnswer.objects.filter(submission=submission)
        total = sum(a.points for a in answers)
        quiz_total = submission.quiz.total_points
        submission.grade = min(total, quiz_total)
        if all(a.points is not None for a in answers):
            submission.status = 'graded'
            submission.graded_at = timezone.now()
        else:
            submission.status = 'grading'
        submission.save(update_fields=['grade', 'status', 'graded_at'])
        return Response({'detail': 'Answer graded successfully.'})

class InstructorSubmissionFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def patch(self, request, submission_id):
        instructor = request.user
        try:
            submission = StudentQuizSubmission.objects.get(
                id=submission_id,
                quiz__course__instructorcourse__instructor=instructor
            )
        except StudentQuizSubmission.DoesNotExist:
            return Response({'detail': 'Submission not found.'}, status=404)
        if submission.status != 'graded':
            return Response({'detail': 'All answers must be graded before setting submission feedback.'}, status=400)
        feedback = request.data.get('feedback', '')
        submission.feedback = feedback
        submission.save(update_fields=['feedback'])
        return Response({'detail': 'Submission feedback set.'})

class InstructorReleaseQuizGradesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def post(self, request, quiz_id):
        instructor = request.user
        submissions = StudentQuizSubmission.objects.filter(
            quiz__id=quiz_id,
            quiz__course__instructorcourse__instructor=instructor,
            status='graded'
        )
        count = submissions.update(status='released')
        return Response({'detail': f'{count} submissions released to students.'}, status=200)
