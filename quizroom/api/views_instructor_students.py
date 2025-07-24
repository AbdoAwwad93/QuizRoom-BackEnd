from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, StudentCourse
from quizroom.models.users.models import CustomUser, StudentProfile
from .serializers import StudentListSerializer, StudentSerializer
from quizroom.api.helpers import is_instructor_for_course

class InstructorAllStudentsView(APIView):
    """
    API view for instructors to list all students in their courses.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        if not courses.exists():
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        student_ids = StudentCourse.objects.filter(course__in=courses).values_list('student_id', flat=True).distinct()
        students = CustomUser.objects.filter(id__in=student_ids, role='student')
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)

class RemoveStudentFromCourseView(APIView):
    """
    API view for instructors to remove a student from their course.
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def delete(self, request, student_id):
        instructor = request.user
        courses = Course.objects.filter(instructorcourse__instructor=instructor)
        if not courses.exists():
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = CustomUser.objects.get(id=student_id, role='student')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        deleted = False
        for course in courses:
            if is_instructor_for_course(course, instructor):
                num_deleted, _ = StudentCourse.objects.filter(student=student, course=course).delete()
                if num_deleted:
                    deleted = True
        if deleted:
            return Response({'detail': 'Student removed from your course(s).'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Student was not assigned to your course(s).'}, status=status.HTTP_404_NOT_FOUND)

class UpdateStudentProfileView(APIView):
    """
    API view for instructors to update a student's profile fields (name, email, password, level).
    """
    permission_classes = [IsAuthenticated, IsInstructor]

    def patch(self, request, student_id):
        try:
            student = CustomUser.objects.get(id=student_id, role='student')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        allowed_fields = {'name', 'email', 'password', 'level'}
        updated = False
        for field in allowed_fields:
            if field in data:
                if field == "level":
                    profile, _ = StudentProfile.objects.get_or_create(user=student)
                    profile.level = data["level"]
                    profile.save()
                    updated = True
                elif field == "password":
                    student.set_password(data["password"])
                    updated = True
                else:
                    setattr(student, field, data[field])
                    updated = True
        if updated:
            student.save()
            return Response({'student': StudentSerializer(student).data}, status=status.HTTP_200_OK)
        return Response({'detail': 'No valid fields to update.'}, status=status.HTTP_400_BAD_REQUEST)
