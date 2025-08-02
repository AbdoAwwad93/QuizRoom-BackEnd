# Views for QuizRoom API

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import *
from quizroom.models.users.models import CustomUser
from quizroom.models.courses.models import Course
from quizroom.models.quizzes.models import *
from quizroom.api.permissions import *
from quizroom.api.helpers import *
class StudentLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_active:
                return Response({'detail': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
            if getattr(user, 'role', None) != 'student':
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

class InstructorLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_active:
                return Response({'detail': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
            if getattr(user, 'role', None) != 'instructor':
                return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Logout successful.'}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        user = request.user
        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz not found.'}, status=404)

        course = quiz.course
        is_instructor = hasattr(user, 'role') and user.role == 'instructor' and Course.objects.filter(id=course.id, instructorcourse__instructor=user).exists()
        is_student = hasattr(user, 'role') and user.role == 'student' and Course.objects.filter(id=course.id, studentcourse__student=user).exists()

        if not (is_instructor or is_student):
            return Response({'detail': 'You are not enrolled in this course.'}, status=403)

        quiz_data = QuizSerializer(quiz).data
        from django.utils import timezone
        now = timezone.now()
        if is_instructor:
            questions = Question.objects.filter(quiz=quiz)
            quiz_data['questions'] = QuestionSerializer(questions, many=True).data
        elif is_student:
            if now < quiz.start_date:
                quiz_data['questions'] = []
            else:
                questions = Question.objects.filter(quiz=quiz)
                quiz_data['questions'] = QuestionSerializer(questions, many=True).data
        return Response(quiz_data)

class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email, is_active=True).first()
        if user:
            otp, entry = create_or_update_otp(user)
            send_otp_email(user, otp)
        return Response({'detail': 'If this email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        user = CustomUser.objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({'detail': 'OTP verification failed.'}, status=status.HTTP_400_BAD_REQUEST)
        valid, msg = check_otp_valid(user, otp)
        if valid:
            return Response({'detail': 'OTP verified.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        user = CustomUser.objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({'detail': 'Password reset failed.'}, status=status.HTTP_400_BAD_REQUEST)
        valid, msg = check_otp_valid(user, otp)
        if not valid:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        clear_otp(user)
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)




class AdminCreateInstructorView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = AdminCreateInstructorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if CustomUser.objects.filter(email=data['email']).exists():
            return Response({'detail': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        user = CustomUser.objects.create_user(
            email=data['email'],
            name=data['name'],
            password=data['password'],
            role='instructor',
            is_active=True
        )
        from quizroom.models.users.models import InstructorProfile
        InstructorProfile.objects.create(user=user)
        return Response({'detail': 'Instructor created.', 'id': user.id, 'email': user.email, 'name': user.name}, status=201)

class AdminCreateCourseView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = AdminCreateCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from quizroom.models.courses.models import Course
        if Course.objects.filter(code=data['code']).exists():
            return Response({'detail': 'Course code already exists.'}, status=400)
        course = Course.objects.create(
            name=data['name'],
            code=data['code'],
            level=data['level']
        )
        return Response({'detail': 'Course created.', 'id': course.id, 'name': course.name, 'code': course.code, 'level': course.level}, status=201)

class AdminAssignInstructorView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = AdminAssignInstructorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instructor_id = serializer.validated_data['instructor_id']
        course_ids = serializer.validated_data['course_ids']
        try:
            instructor = CustomUser.objects.get(id=instructor_id, role='instructor')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Instructor not found.'}, status=404)
        from quizroom.models.courses.models import Course, InstructorCourse
        courses = Course.objects.filter(id__in=course_ids)
        if courses.count() != len(course_ids):
            return Response({'detail': 'One or more courses not found.'}, status=400)
        created = 0
        for course in courses:
            obj, was_created = InstructorCourse.objects.get_or_create(instructor=instructor, course=course)
            if was_created:
                created += 1
        return Response({'detail': f'Instructor assigned to {created} course(s).'}, status=200)