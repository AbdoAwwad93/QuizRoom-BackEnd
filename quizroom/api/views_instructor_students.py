from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course, StudentCourse
from quizroom.models.users.models import CustomUser, StudentProfile
from .serializers import StudentListSerializer, StudentSerializer

class InstructorAllStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request):
        instructor = request.user
        instructor_course = Course.objects.filter(instructorcourse__instructor=instructor).first()
        if not instructor_course:
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        student_ids = StudentCourse.objects.filter(course=instructor_course).values_list('student_id', flat=True).distinct()
        students = CustomUser.objects.filter(id__in=student_ids, role='student')
        serializer = StudentListSerializer(students, many=True)
        return Response(serializer.data)

class RemoveStudentFromCourseView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def delete(self, request, student_id):
        instructor = request.user
        instructor_course = Course.objects.filter(instructorcourse__instructor=instructor).first()
        if not instructor_course:
            return Response({'detail': 'Instructor is not assigned to any course.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student = CustomUser.objects.get(id=student_id, role='student')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        deleted, _ = StudentCourse.objects.filter(student=student, course=instructor_course).delete()
        if deleted:
            return Response({'detail': 'Student removed from your course.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Student was not assigned to your course.'}, status=status.HTTP_404_NOT_FOUND)

class UpdateStudentProfileView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def patch(self, request, student_id):
        try:
            student = CustomUser.objects.get(id=student_id, role='student')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        allowed_fields = {'name', 'email','password','level'}
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
