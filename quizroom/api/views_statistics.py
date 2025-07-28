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

class StudentsPerCourseView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        data = []
        for course in courses:
            student_count = StudentCourse.objects.filter(course=course).count()
            data.append({
                'course_id': course.id,
                'course_name': course.name,
                'student_count': student_count
            })
        return Response({'results': data})

class QuizScoresView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        course_id = request.query_params.get('course_id')
        quiz_id = request.query_params.get('quiz_id')
        quizzes = Quiz.objects.filter(course__instructorcourse__instructor=instructor)
        if course_id:
            quizzes = quizzes.filter(course_id=course_id)
        if quiz_id:
            quizzes = quizzes.filter(id=quiz_id)
        data = []
        for quiz in quizzes:
            submissions = StudentQuizSubmission.objects.filter(quiz=quiz, grade__isnull=False)
            scores = submissions.values_list('grade', flat=True)
            if scores:
                avg_score = submissions.aggregate(avg=Avg('grade'))['avg']
                max_score = submissions.aggregate(max=Max('grade'))['max']
                min_score = submissions.aggregate(min=Min('grade'))['min']
            else:
                avg_score = max_score = min_score = None
            data.append({
                'quiz_id': quiz.id,
                'quiz_title': quiz.title,
                'average_score': avg_score,
                'highest_score': max_score,
                'lowest_score': min_score
            })
        return Response({'results': data})

class SubmissionRatesView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        quiz_id = request.query_params.get('quiz_id')
        if not quiz_id:
            return Response({'detail': 'quiz_id is required'}, status=status.HTTP_400_BAD_REQUEST)
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

    def get(self, request):
        instructor = request.user
        quiz_id = request.query_params.get('quiz_id')
        if not quiz_id:
            return Response({'detail': 'quiz_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quiz = Quiz.objects.get(id=quiz_id, course__instructorcourse__instructor=instructor)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        submissions = StudentQuizSubmission.objects.filter(quiz=quiz, grade__isnull=False)
        histogram = {f'{bins[i]}-{bins[i+1]-1}': 0 for i in range(len(bins)-1)}
        for s in submissions:
            for i in range(len(bins)-1):
                if bins[i] <= float(s.grade) < bins[i+1]:
                    key = f'{bins[i]}-{bins[i+1]-1}'
                    histogram[key] += 1
                    break
                elif float(s.grade) == 100 and bins[i+1] == 100:
                    histogram['90-100'] += 1
        return Response({'quiz_id': quiz.id, 'quiz_title': quiz.title, 'grade_distribution': histogram})

class StudentProgressView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'detail': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(id=course_id, instructorcourse__instructor=instructor)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
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
        return Response({'course_id': course.id, 'course_name': course.name, 'student_progress': data})

# --- STUDENT STATISTICS ---

class StudentPerformanceSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        data = []
        for course in courses:
            quizzes = Quiz.objects.filter(course=course)
            quiz_ids = list(quizzes.values_list('id', flat=True))
            submissions = StudentQuizSubmission.objects.filter(student=student, quiz_id__in=quiz_ids, grade__isnull=False)
            avg_score = submissions.aggregate(avg=Avg('grade'))['avg'] if submissions.exists() else None
            # Ranking in class
            classmates = StudentCourse.objects.filter(course=course).values_list('student_id', flat=True)
            classmates_scores = StudentQuizSubmission.objects.filter(student_id__in=classmates, quiz_id__in=quiz_ids, grade__isnull=False)
            # Calculate average per classmate
            classmate_averages = {}
            for sid in classmates:
                s_subs = classmates_scores.filter(student_id=sid)
                avg = s_subs.aggregate(avg=Avg('grade'))['avg'] if s_subs.exists() else 0
                classmate_averages[sid] = avg
            sorted_averages = sorted([(sid, avg) for sid, avg in classmate_averages.items()], key=lambda x: x[1], reverse=True)
            rank = next((i+1 for i, (sid, avg) in enumerate(sorted_averages) if sid == student.id), None)
            data.append({
                'course_id': course.id,
                'course_name': course.name,
                'average_score': avg_score,
                'ranking': rank,
                'total_students': len(classmates)
            })
        return Response({'results': data})

class StudentProgressTrackingView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        courses = Course.objects.filter(studentcourse__student=student)
        data = []
        for course in courses:
            quizzes = Quiz.objects.filter(course=course)
            quiz_ids = list(quizzes.values_list('id', flat=True))
            submissions = StudentQuizSubmission.objects.filter(student=student, quiz_id__in=quiz_ids)
            completed = submissions.filter(grade__isnull=False)
            progress = []
            for quiz in quizzes:
                sub = submissions.filter(quiz=quiz).first()
                progress.append({
                    'quiz_id': quiz.id,
                    'quiz_title': quiz.title,
                    'score': sub.grade if sub and sub.grade is not None else None,
                    'status': sub.status if sub else 'not_started',
                })
            data.append({
                'course_id': course.id,
                'course_name': course.name,
                'progress': progress
            })
        return Response({'results': data})
