from quizroom.models.courses.models import Course

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
