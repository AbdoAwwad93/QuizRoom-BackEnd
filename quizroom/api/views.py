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
from quizroom.api.permissions import IsStudent, IsInstructor
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
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
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
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
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
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response({'detail': 'Password reset failed.'}, status=status.HTTP_400_BAD_REQUEST)
        valid, msg = check_otp_valid(user, otp)
        if not valid:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        clear_otp(user)
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)