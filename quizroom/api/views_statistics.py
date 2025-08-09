from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Avg, Max, Min, Q, F, Sum
from quizroom.api.permissions import IsInstructor, IsStudent
from quizroom.models.courses.models import Course, StudentCourse
from quizroom.models.quizzes.models import Quiz, Question
from quizroom.models.submissions.models import StudentQuizSubmission, StudentAnswer
from quizroom.models.users.models import CustomUser

class QuizScoresView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id, course__instructorcourse__instructor=instructor)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
        submissions = StudentQuizSubmission.objects.filter(quiz=quiz, grade__isnull=False)
        scores = submissions.values_list('grade', flat=True)
        if scores:
            avg_score = submissions.aggregate(avg=Avg('grade'))['avg']
            max_score = submissions.aggregate(max=Max('grade'))['max']
            min_score = submissions.aggregate(min=Min('grade'))['min']
        else:
            avg_score = max_score = min_score = None
        data = {
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'average_score': avg_score,
            'highest_score': max_score,
            'lowest_score': min_score
        }
        return Response(data)


class SubmissionRatesView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id, course__instructorcourse__instructor=instructor)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
        course = quiz.course
        students = StudentCourse.objects.filter(course=course).values_list('student_id', flat=True)
        submitted = StudentQuizSubmission.objects.filter(quiz=quiz).values_list('student_id', flat=True)
        submitted_students = CustomUser.objects.filter(id__in=submitted)
        not_submitted_students = CustomUser.objects.filter(id__in=students).exclude(id__in=submitted)
        return Response({
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'submitted_students': [{'id': s.id, 'email': s.email, 'name': s.name} for s in submitted_students],
            'not_submitted_students': [{'id': s.id, 'email': s.email, 'name': s.name} for s in not_submitted_students]
        })

class GradeDistributionView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id, course__instructorcourse__instructor=instructor)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
        total_points = quiz.total_points
        bin_count = 10
        bin_size = max(1, total_points // bin_count)
        bins = [i for i in range(0, total_points, bin_size)]
        if bins[-1] != total_points:
            bins.append(total_points)
        histogram = {f'{bins[i]}-{bins[i+1]-1 if bins[i+1]-1 < total_points else total_points}': 0 for i in range(len(bins)-1)}
        submissions = StudentQuizSubmission.objects.filter(quiz=quiz, grade__isnull=False)
        for s in submissions:
            grade = float(s.grade)
            placed = False
            for i in range(len(bins)-1):
                lower = bins[i]
                upper = bins[i+1] if bins[i+1] < total_points else total_points
                if lower <= grade < bins[i+1] or (i == len(bins)-2 and grade == total_points):
                    key = f'{lower}-{upper-1 if upper-1 < total_points else total_points}'
                    histogram[key] += 1
                    placed = True
                    break
            if not placed and grade == total_points:
                last_key = list(histogram.keys())[-1]
                histogram[last_key] += 1
        return Response({'quiz_id': quiz.id, 'quiz_title': quiz.title, 'grade_distribution': histogram})

class StudentProgressView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        results = []
        for course in courses:
            quizzes = Quiz.objects.filter(course=course)
            quiz_ids = list(quizzes.values_list('id', flat=True))
            students = StudentCourse.objects.filter(course=course).select_related('student')
            data = []
            for sc in students:
                completed = StudentQuizSubmission.objects.filter(student=sc.student, quiz_id__in=quiz_ids, grade__isnull=False).count()
                pending = len(quiz_ids) - completed
                data.append({
                    'student_id': sc.student.id,
                    'student_name': sc.student.name,
                    'completed_quizzes': completed,
                    'pending_quizzes': pending
                })
            results.append({
                'course_id': course.id,
                'course_name': course.name,
                'student_progress': data
            })
        return Response({'results': results})

# --- STUDENT STATISTICS ---

class StudentPerformanceSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, course_id):
        student = request.user
        try:
            course = Course.objects.get(id=course_id, studentcourse__student=student)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or not enrolled'}, status=status.HTTP_404_NOT_FOUND)
        quizzes = Quiz.objects.filter(course=course)
        quiz_ids = list(quizzes.values_list('id', flat=True))

        per_student = (
            StudentQuizSubmission.objects
            .filter(quiz_id__in=quiz_ids, grade__isnull=False)
            .values('student_id')
            .annotate(total_score=Sum('grade'), average_score=Avg('grade'))
        )

        total_by_student = {row['student_id']: row['total_score'] for row in per_student}
        avg_by_student = {row['student_id']: row['average_score'] for row in per_student}
        student_total = total_by_student.get(student.id, 0)
        student_avg = avg_by_student.get(student.id)
        higher_totals = sum(1 for total in total_by_student.values() if total is not None and total > student_total)
        ranking_by_total = higher_totals + 1 if total_by_student else None

        higher_avgs = sum(1 for avg in avg_by_student.values() if avg is not None and student_avg is not None and avg > student_avg)
        ranking_by_avg = higher_avgs + 1 if student_avg is not None else None

        classmates = StudentCourse.objects.filter(course=course).values_list('student_id', flat=True)
        data = {
            'course_id': course.id,
            'course_name': course.name,
            'average_score': student_avg,
            'ranking': ranking_by_avg,
            'total_score': student_total,
            'ranking_by_total_score': ranking_by_total,
            'total_students': len(classmates)
        }
        return Response(data)


class InstructorQuizQuestionStatsView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id, course__instructorcourse__instructor=instructor)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
        submissions = StudentQuizSubmission.objects.filter(quiz=quiz, status='released', grade__isnull=False)
        submission_ids = submissions.values_list('id', flat=True)

        questions = list(Question.objects.filter(quiz=quiz).values('id', 'question_text', 'points'))
        stats_by_q = {q['id']: {'question_id': q['id'], 'question_text': q['question_text'], 'points': q['points'], 'correct': 0, 'incorrect': 0} for q in questions}

        if submission_ids:
            answer_counts = (
                StudentAnswer.objects
                .filter(submission_id__in=submission_ids)
                .values('question_id')
                .annotate(
                    correct=Count('id', filter=Q(points=F('question__points'))),
                    total=Count('id')
                )
            )
            for row in answer_counts:
                qid = row['question_id']
                stats_by_q[qid]['correct'] = row['correct']
                stats_by_q[qid]['incorrect'] = row['total'] - row['correct']
        most_missed = None
        most_correct = None
        if stats_by_q:
            most_missed = max(stats_by_q.values(), key=lambda x: x['incorrect'])
            most_correct = max(stats_by_q.values(), key=lambda x: x['correct'])

        return Response({
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'question_stats': list(stats_by_q.values()),
            'most_missed_question': most_missed,
            'most_correct_question': most_correct,
        })

class InstructorStatisticsSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        course_ids = courses.values_list('id', flat=True)
        quizzes = Quiz.objects.filter(course_id__in=course_ids)
        quiz_ids = quizzes.values_list('id', flat=True)
        student_ids = StudentCourse.objects.filter(course_id__in=course_ids).values_list('student_id', flat=True).distinct()
        submission_count = StudentQuizSubmission.objects.filter(quiz_id__in=quiz_ids).count()

        data = {
            "total_quizzes": quizzes.count(),
            "total_students": len(student_ids),
            "total_submissions": submission_count
        }
        return Response(data)