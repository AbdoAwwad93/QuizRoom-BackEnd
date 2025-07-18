# API URLs for QuizRoom
from django.urls import path
from .views import LoginView
from .views_instructor import CreateStudentView, AssignCoursesToStudentView
from .views_instructor_courses import InstructorCoursesView, CourseStudentsView
from .views_instructor_students import InstructorAllStudentsView, RemoveStudentFromCourseView, UpdateStudentProfileView
from .views_instructor_quizzes import InstructorCourseQuizzesView
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
]
