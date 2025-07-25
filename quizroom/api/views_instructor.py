from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status , permissions
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from quizroom.models.users.models import StudentProfile
from quizroom.models.courses.models import Course, StudentCourse
from .serializers import StudentCreateSerializer, StudentSerializer, InstructorProfileEditSerializer
from .permissions import IsInstructor
from quizroom.api.helpers import is_instructor_for_course

User = get_user_model()
class InstructorProfileEditView(APIView):
    """
    API view for instructors to edit their profile information.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def patch(self, request):
        instructor = request.user
        serializer = InstructorProfileEditSerializer(instructor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Name updated successfully.', 'name': serializer.data['name']})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateStudentView(APIView):
    """
    API view for instructors to create a new student user and profile and assign him to his course.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request):
        serializer = StudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        name = serializer.validated_data['name']
        password = serializer.validated_data['password']
        level = serializer.validated_data['level']

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, password=password, name=name, role='student')
        StudentProfile.objects.create(user=user, level=level)

        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        for course in courses:
            if not StudentCourse.objects.filter(student=user, course=course).exists():
                StudentCourse.objects.create(student=user, course=course, status='active')

        return Response({'student': StudentSerializer(user).data}, status=status.HTTP_201_CREATED)

class AssignCoursesToStudentView(APIView):
    """
    API view for instructors to assign a student to one of their courses.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request, student_id):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        if not courses.exists():
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = User.objects.get(id=student_id, role='student')
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        assigned = False
        for course in courses:
            if is_instructor_for_course(course, instructor):
                already_assigned = StudentCourse.objects.filter(student=student, course=course).exists()
                if not already_assigned:
                    StudentCourse.objects.create(student=student, course=course, status='active')
                    assigned = True
        if assigned:
            return Response({'detail': 'Student assigned to your course(s) successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Student is already assigned to your course(s).'}, status=status.HTTP_200_OK)
