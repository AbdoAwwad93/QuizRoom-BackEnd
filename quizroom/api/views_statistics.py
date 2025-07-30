from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Avg, Max, Min, Q, F
from quizroom.api.permissions import IsInstructor, IsStudent
from quizroom.models.courses.models import Course, StudentCourse, InstructorCourse
from quizroom.models.quizzes.models import Quiz
from quizroom.models.submissions.models import StudentQuizSubmission
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
        submissions = StudentQuizSubmission.objects.filter(student=student, quiz_id__in=quiz_ids, grade__isnull=False)
        avg_score = submissions.aggregate(avg=Avg('grade'))['avg'] if submissions.exists() else None
        classmates = StudentCourse.objects.filter(course=course).values_list('student_id', flat=True)
        classmate_averages = {}
        for sid in classmates:
            s_subs = StudentQuizSubmission.objects.filter(student_id=sid, quiz_id__in=quiz_ids, grade__isnull=False)
            avg = s_subs.aggregate(avg=Avg('grade'))['avg'] if s_subs.exists() else 0
            classmate_averages[sid] = avg
        sorted_averages = sorted([(sid, avg) for sid, avg in classmate_averages.items()], key=lambda x: x[1], reverse=True)
        rank = next((i+1 for i, (sid, avg) in enumerate(sorted_averages) if sid == student.id), None)
        data = {
            'course_id': course.id,
            'course_name': course.name,
            'average_score': avg_score,
            'ranking': rank,
            'total_students': len(classmates)
        }
        return Response(data)

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