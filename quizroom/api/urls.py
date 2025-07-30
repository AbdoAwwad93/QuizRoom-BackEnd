# API URLs for QuizRoom
from django.urls import path
from .views import *
from .views_instructor import *
from .views_instructor_courses import *
from .views_instructor_students import *
from .views_instructor_quizzes import *
from .views_instructor_questions import *
from .views_instructor_grading import *
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views_student import *
from .views_statistics import *

urlpatterns = [
    path('auth/student-login/', StudentLoginView.as_view(), name='student_login'),
    path('auth/instructor-login/', InstructorLoginView.as_view(), name='instructor_login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('quiz/<int:quiz_id>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('instructor/create-student/', CreateStudentView.as_view(), name='create_student'),
    path('instructor/students/<int:student_id>/assign-courses/', AssignCoursesToStudentView.as_view(), name='assign_courses_to_student'),
    path('instructor/courses/', InstructorCoursesView.as_view(), name='instructor_courses'),
    path('instructor/courses/<int:course_id>/students/', CourseStudentsView.as_view(), name='course_students'),
    path('instructor/students/', InstructorAllStudentsView.as_view(), name='instructor_all_students'),
    path('instructor/students/all/', InstructorAllStudentsSystemView.as_view(), name='instructor_all_students_system'),
    path('instructor/students/<int:student_id>/remove/', RemoveStudentFromCourseView.as_view(), name='remove_student_from_course'),
    path('instructor/students/<int:student_id>/update/', UpdateStudentProfileView.as_view(), name='update_student_profile'),
    path('instructor/quizzes/', InstructorCourseQuizzesView.as_view(), name='instructor_course_quizzes'),
    path('instructor/quizzes/<int:quiz_id>/remove/', InstructorCourseQuizzesView.as_view(), name='remove_quiz'),
    path('instructor/quizzes/<int:quiz_id>/edit/', InstructorCourseQuizzesView.as_view(), name='edit_quiz'),
    path('instructor/quizzes/<int:quiz_id>/questions/create/', InstructorQuizQuestionCreateView.as_view(), name='instructor_quiz_create_question'),
    path('instructor/quizzes/<int:quiz_id>/questions/', InstructorQuizQuestionListView.as_view(), name='instructor_quiz_list_questions'),
    path('instructor/quizzes/<int:quiz_id>/submissions/', InstructorQuizSubmissionsListView.as_view(), name='instructor_quiz_submissions'),
    path('instructor/quizzes/<int:quiz_id>/release/', InstructorReleaseQuizGradesView.as_view(), name='instructor_release_quiz_grades'),
    path('instructor/questions/<int:question_id>/remove/', InstructorQuizQuestionEditRemoveView.as_view(), name='instructor_remove_question'),
    path('instructor/questions/<int:question_id>/edit/', InstructorQuizQuestionEditRemoveView.as_view(), name='instructor_edit_question'),
    path('instructor/submissions/<int:submission_id>/grade/', InstructorGradeSubmissionView.as_view(), name='instructor_grade_submission'),
    path('instructor/submissions/<int:submission_id>/', InstructorSubmissionDetailView.as_view(), name='instructor_submission_detail'),
    path('instructor/submissions/<int:submission_id>/edit-feedback/', InstructorEditSubmissionFeedbackView.as_view(), name='instructor_edit_submission_feedback'),
    path('instructor/answers/<int:answer_id>/edit-grade/', InstructorEditAnswerGradeView.as_view(), name='instructor_edit_answer_grade'),
    path('instructor/profile/edit/', InstructorProfileEditView.as_view(), name='instructor_profile_edit'),
   
    path('student/quizzes/', StudentAllQuizzesView.as_view(), name='student_all_quizzes'),
    path('student/quizzes/current/', StudentCurrentQuizzesView.as_view(), name='student_current_quizzes'),
    path('student/courses/', StudentEnrolledCoursesView.as_view(), name='student_enrolled_courses'),
    path('student/quizzes/<int:quiz_id>/submission/', StudentQuizSubmissionView.as_view(), name='student_quiz_submission'),
    path('student/quizzes/<int:quiz_id>/questions/', StudentQuizQuestionsView.as_view(), name='student_quiz_questions'),
    path('student/quizzes/<int:quiz_id>/questions/<int:question_id>/answer/', StudentSaveAnswerView.as_view(), name='student_save_answer'),
    path('student/quizzes/<int:quiz_id>/submit/', StudentSubmitQuizView.as_view(), name='student_submit_quiz'),
    path('student/submissions/', StudentAllSubmissionsView.as_view(), name='student_all_submissions'),
    

    path('instructor/statistics/summary/', InstructorStatisticsSummaryView.as_view(), name='instructor_statistics_summary'),
    path('instructor/statistics/quiz-scores/<int:quiz_id>/', QuizScoresView.as_view(), name='instructor_quiz_scores'),
    path('instructor/statistics/submission-rates/<int:quiz_id>/', SubmissionRatesView.as_view(), name='instructor_submission_rates'),
    path('instructor/statistics/grade-distribution/<int:quiz_id>/', GradeDistributionView.as_view(), name='instructor_grade_distribution'),
    path('instructor/statistics/student-progress/', StudentProgressView.as_view(), name='instructor_student_progress'),   
    path('student/statistics/performance-summary/<int:course_id>/', StudentPerformanceSummaryView.as_view(), name='student_performance_summary'),

]
