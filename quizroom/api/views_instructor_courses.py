from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, InstructorCourse, StudentCourse
from quizroom.models.users.models import CustomUser
from .serializers import CourseSerializer, StudentListSerializer

class InstructorCoursesView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

class CourseStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, course_id):
        instructor = request.user
        if not InstructorCourse.objects.filter(instructor=instructor, course_id=course_id).exists():
            return Response({'detail': 'Not authorized for this course.'}, status=status.HTTP_403_FORBIDDEN)
        student_courses = StudentCourse.objects.filter(course_id=course_id)
        students = CustomUser.objects.filter(id__in=student_courses.values_list('student_id', flat=True))
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)
