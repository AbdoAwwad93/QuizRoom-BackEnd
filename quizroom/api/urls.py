# API URLs for QuizRoom
from django.urls import path
from .views import LoginView
from .views_instructor import *
from .views_instructor_courses import *
from .views_instructor_students import *
from .views_instructor_quizzes import *
from .views_instructor_questions import *
from .views_instructor_grading import *
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('instructor/create-student/', CreateStudentView.as_view(), name='create_student'),
    path('instructor/students/<int:student_id>/assign-courses/', AssignCoursesToStudentView.as_view(), name='assign_courses_to_student'),
    path('instructor/courses/', InstructorCoursesView.as_view(), name='instructor_courses'),
    path('instructor/courses/<int:course_id>/students/', CourseStudentsView.as_view(), name='course_students'),
    path('instructor/students/', InstructorAllStudentsView.as_view(), name='instructor_all_students'),
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
    path('instructor/submissions/<int:submission_id>/', InstructorSubmissionDetailView.as_view(), name='instructor_submission_detail'),
    path('instructor/submissions/<int:submission_id>/feedback/', InstructorSubmissionFeedbackView.as_view(), name='instructor_submission_feedback'),
    path('instructor/answers/<int:answer_id>/grade/', InstructorGradeAnswerView.as_view(), name='instructor_grade_answer'),
    path('instructor/profile/edit/', InstructorProfileEditView.as_view(), name='instructor_profile_edit'),
]
