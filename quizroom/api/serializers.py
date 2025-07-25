# Serializers for QuizRoom API

from rest_framework import serializers
from quizroom.models.users.models import CustomUser, StudentProfile
from quizroom.models.courses.models import Course, StudentCourse
from quizroom.models.quizzes.models import Quiz, Question
from quizroom.models.submissions.models import StudentQuizSubmission, StudentAnswer

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'role')

class StudentSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'role', 'level')

    def get_level(self, obj):
        try:
            return obj.studentprofile.level
        except Exception:
            return None

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
    level = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name','level')
    
    def get_level(self, obj):
        try:
            return obj.studentprofile.level
        except Exception:
            return None

class QuizSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    course_name = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = (
            'id', 'title', 'course_id', 'course_name', 'week_number', 'start_date', 'end_date',
            'duration', 'total_points', 'created_at', 'updated_at'
        )

    def get_course_name(self, obj):
        return obj.course.name if obj.course else None

class QuestionCreateSerializer(serializers.Serializer):
    question_text = serializers.CharField(max_length=2048)
    # correct_answer = serializers.CharField(max_length=2048)
    points = serializers.IntegerField(min_value=1)

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'quiz', 'question_text', 'question_type', 'correct_answer', 'points')

class QuizCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    week_number = serializers.IntegerField(min_value=1)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    duration = serializers.IntegerField(min_value=1, help_text='Duration in minutes')
    total_points = serializers.IntegerField(min_value=1)

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ['id', 'question', 'answer_text', 'points', 'feedback']
        read_only_fields = ['id', 'question', 'answer_text']

class InstructorGradeAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ['points', 'feedback']

    def validate_points(self, value):
        question = self.instance.question
        if value < 0 or value > question.points:
            raise serializers.ValidationError(f'Points must be between 0 and {question.points}.')
        return value

class StudentQuizSubmissionSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(source='studentanswer_set', many=True, read_only=True)
    student_name = serializers.SerializerMethodField()

    def get_student_name(self, obj):
        return obj.student.name if obj.student else None

    class Meta:
        model = StudentQuizSubmission
        fields = ['id', 'student', 'student_name', 'quiz', 'submission_date', 'grade', 'feedback', 'graded_at', 'status', 'answers']
        read_only_fields = ['id', 'student', 'quiz', 'submission_date', 'grade', 'graded_at', 'status', 'answers']

class InstructorSubmissionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentQuizSubmission
        fields = ['feedback']

class InstructorProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['name']