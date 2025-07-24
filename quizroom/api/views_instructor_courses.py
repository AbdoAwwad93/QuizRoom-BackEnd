from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, InstructorCourse, StudentCourse
from quizroom.models.users.models import CustomUser
from .serializers import CourseSerializer, StudentListSerializer
from quizroom.api.helpers import is_instructor_for_course

class InstructorCoursesView(APIView):
    """
    API view for instructors to list their courses.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

class CourseStudentsView(APIView):
    """
    API view for instructors to list students enrolled in a course they teach.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, course_id):
        instructor = request.user
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({'detail': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not is_instructor_for_course(course, instructor):
            return Response({'detail': 'Not authorized for this course.'}, status=status.HTTP_403_FORBIDDEN)
        students = CustomUser.objects.filter(id__in=StudentCourse.objects.filter(course=course).values_list('student_id', flat=True))
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)
