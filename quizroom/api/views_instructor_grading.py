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
    """
    List all quiz submissions for a given quiz, accessible only to the instructor who owns the course.
    """
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
    """
    Retrieve details for a single submission, instructor-only.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def get(self, request, submission_id):
        instructor = request.user
        try:
            submission = StudentQuizSubmission.objects.select_related('student', 'quiz').get(
                id=submission_id,
                quiz__course__instructorcourse__instructor=instructor
            )
        except StudentQuizSubmission.DoesNotExist:
            return Response({'detail': 'Submission not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentQuizSubmissionSerializer(submission)
        return Response(serializer.data)

class InstructorEditAnswerGradeView(APIView):
    """
    Edit the grade and feedback for a student's answer to a quiz question. Instructor-only.
    """
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
            return Response({'detail': 'Answer not found.'}, status=status.HTTP_404_NOT_FOUND)
        points = request.data.get('points')
        feedback = request.data.get('feedback', '')
        if points is None or not (0 <= points <= answer.question.points):
            return Response({'detail': f'Points must be between 0 and {answer.question.points}.'}, status=status.HTTP_400_BAD_REQUEST)
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

class InstructorEditSubmissionFeedbackView(APIView):
    """
    Edit the overall feedback for a student's quiz submission, instructor-only.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def patch(self, request, submission_id):
        instructor = request.user
        try:
            submission = StudentQuizSubmission.objects.get(
                id=submission_id,
                quiz__course__instructorcourse__instructor=instructor
            )
        except StudentQuizSubmission.DoesNotExist:
            return Response({'detail': 'Submission not found.'}, status=status.HTTP_404_NOT_FOUND)
        if submission.status != 'graded':
            return Response({'detail': 'All answers must be graded before setting submission feedback.'}, status=status.HTTP_400_BAD_REQUEST)
        feedback = request.data.get('feedback', '')
        submission.feedback = feedback
        submission.save(update_fields=['feedback'])
        return Response({'detail': 'Submission feedback set.'})

class InstructorReleaseQuizGradesView(APIView):
    """
    Release grades for all graded submissions for a quiz. Instructor-only.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def post(self, request, quiz_id):
        instructor = request.user
        submissions = StudentQuizSubmission.objects.filter(
            quiz__id=quiz_id,
            quiz__course__instructorcourse__instructor=instructor,
            status='graded'
        )
        count = submissions.update(status='released')
        return Response({'detail': f'{count} submissions released to students.'}, status=status.HTTP_200_OK)

class InstructorGradeSubmissionView(APIView):
    """
    grade all answers for a student quiz submission in one request. Instructor-only.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    @transaction.atomic
    def patch(self, request, submission_id):
        instructor = request.user
        try:
            submission = StudentQuizSubmission.objects.select_related('quiz', 'student').get(
                id=submission_id,
                quiz__course__instructorcourse__instructor=instructor
            )
        except StudentQuizSubmission.DoesNotExist:
            return Response({'detail': 'Submission not found.'}, status=status.HTTP_404_NOT_FOUND)
        answers_data = request.data.get('answers', [])
        if not isinstance(answers_data, list):
            return Response({'detail': 'answers must be a list.'}, status=status.HTTP_400_BAD_REQUEST)
        answer_objs = {a.id: a for a in StudentAnswer.objects.filter(submission=submission)}
        for entry in answers_data:
            answer_id = entry.get('answer_id')
            points = entry.get('points')
            feedback = entry.get('feedback', '')
            answer = answer_objs.get(answer_id)
            if not answer:
                return Response({'detail': f'Answer {answer_id} not found in this submission.'}, status=status.HTTP_404_NOT_FOUND)
            if points is None or not (0 <= points <= answer.question.points):
                return Response({'detail': f'Points for answer {answer_id} must be between 0 and {answer.question.points}.'}, status=status.HTTP_400_BAD_REQUEST)
            answer.points = points
            answer.feedback = feedback
            answer.save()
        submission_feedback = request.data.get('feedback')
        if submission_feedback is not None:
            submission.feedback = submission_feedback
        answers = StudentAnswer.objects.filter(submission=submission)
        total = sum(a.points for a in answers if a.points is not None)
        quiz_total = submission.quiz.total_points
        submission.grade = min(total, quiz_total)
        if all(a.points is not None for a in answers):
            submission.status = 'graded'
            submission.graded_at = timezone.now()
        else:
            submission.status = 'grading'
        submission.save(update_fields=['grade', 'status', 'graded_at', 'feedback'])
        return Response({'detail': 'All answers graded successfully.'})
