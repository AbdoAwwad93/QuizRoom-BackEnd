# Serializers for QuizRoom API

from rest_framework import serializers
from quizroom.models.users.models import CustomUser, StudentProfile
from quizroom.models.courses.models import Course, StudentCourse
from quizroom.models.quizzes.models import Quiz

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'role')

class StudentCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    level = serializers.IntegerField(min_value=1, max_value=4)
    courses = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    def validate_courses(self, value):
        # Only validate if courses is provided and not empty
        if value is not None and len(value) > 0:
            courses = Course.objects.filter(id__in=value)
            if courses.count() != len(value):
                raise serializers.ValidationError("One or more courses do not exist.")
        return value

class AssignCoursesSerializer(serializers.Serializer):
    courses = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def validate_courses(self, value):
        if not value:
            raise serializers.ValidationError("At least one course must be assigned.")
        courses = Course.objects.filter(id__in=value)
        if courses.count() != len(value):
            raise serializers.ValidationError("One or more courses do not exist.")
        return value

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'name', 'code', 'level')

class StudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name')

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'course', 'created_at')
