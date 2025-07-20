from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status , permissions
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from quizroom.models.users.models import StudentProfile
from quizroom.models.courses.models import Course, StudentCourse
from .serializers import StudentCreateSerializer, AssignCoursesSerializer, UserSerializer
from .permissions import IsInstructor

User = get_user_model()
class InstructorProfileEditView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInstructor]

    def patch(self, request):
        instructor = request.user
        serializer = InstructorProfileEditSerializer(instructor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Name updated successfully.', 'name': serializer.data['name']})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateStudentView(APIView):
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
        return Response({'student': UserSerializer(user).data}, status=status.HTTP_201_CREATED)

class AssignCoursesToStudentView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request, student_id):
        instructor = request.user
        instructor_course = Course.objects.filter(instructorcourse__instructor=instructor).first()
        if not instructor_course:
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = User.objects.get(id=student_id, role='student')
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        already_assigned = StudentCourse.objects.filter(student=student, course=instructor_course).exists()
        if already_assigned:
            return Response({'detail': 'Student is already assigned to your course.'}, status=status.HTTP_200_OK)
        StudentCourse.objects.create(student=student, course=instructor_course, status='active')
        return Response({'detail': 'Student assigned to your course successfully.'}, status=status.HTTP_201_CREATED)
