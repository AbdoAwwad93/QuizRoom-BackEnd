from quizroom.models.courses.models import Course
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from quizroom.models.users.models import CustomUser, PasswordResetOTP
from django.conf import settings
import logging

def is_instructor_for_course(course, instructor):
    """Returns True if instructor is assigned to the course."""
    return Course.objects.filter(id=course.id, instructorcourse__instructor=instructor).exists()

def is_instructor_for_quiz(quiz, instructor):
    """Returns True if instructor is assigned to the course for this quiz."""
    return is_instructor_for_course(quiz.course, instructor)

def is_student_enrolled_in_course(course, student):
    """Returns True if student is enrolled in the course."""
    return Course.objects.filter(id=course.id, studentcourse__student=student).exists()

def is_student_enrolled_in_quiz(quiz, student):
    """Returns True if student is enrolled in the course for this quiz."""
    return is_student_enrolled_in_course(quiz.course, student)

OTP_LENGTH = 7
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_BLOCK_MINUTES = 30

def generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))

def create_or_update_otp(user):
    PasswordResetOTP.objects.filter(user=user).delete()
    otp = generate_otp()
    otp_hash = make_password(otp)
    now = timezone.now()
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    entry = PasswordResetOTP.objects.create(
        user=user,
        otp_hash=otp_hash,
        expires_at=expires_at,
    )
    return otp, entry

def send_otp_email(user, otp):
    subject = 'Your Password Reset OTP'
    message = f'Your OTP for password reset is: {otp}\nThis code will expire in {OTP_EXPIRY_MINUTES} minutes.'
    logging.debug(f"Sending OTP email to: {user.email} | OTP: {otp}")
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logging.debug(f"Email sent to {user.email}")
    except Exception as e:
        logging.error(f"Failed to send OTP email to {user.email}: {e}")
        raise

def check_otp_valid(user, otp):
    try:
        entry = PasswordResetOTP.objects.filter(user=user).latest('created_at')
    except PasswordResetOTP.DoesNotExist:
        return False, 'No OTP found.'
    now = timezone.now()
    if entry.is_blocked:
        if entry.last_failed_at and now < entry.last_failed_at + timedelta(minutes=OTP_BLOCK_MINUTES):
            return False, 'Too many failed attempts. Try again later.'
        else:
            entry.is_blocked = False
            entry.failed_attempts = 0
            entry.save()
    if now > entry.expires_at:
        return False, 'OTP expired.'
    if not check_password(otp, entry.otp_hash):
        entry.failed_attempts += 1
        entry.last_failed_at = now
        if entry.failed_attempts >= OTP_MAX_ATTEMPTS:
            entry.is_blocked = True
        entry.save()
        if entry.is_blocked:
            return False, 'Too many failed attempts. Try again later.'
        return False, f'Invalid OTP. {OTP_MAX_ATTEMPTS - entry.failed_attempts} attempts left.'
    entry.failed_attempts = 0
    entry.is_blocked = False
    entry.save()
    return True, 'OTP verified.'

def clear_otp(user):
    PasswordResetOTP.objects.filter(user=user).delete()
