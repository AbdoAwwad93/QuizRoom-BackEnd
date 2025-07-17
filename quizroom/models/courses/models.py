from django.db import models
from quizroom.models.users.models import CustomUser
from rest_framework.fields import MaxValueValidator, MinValueValidator

class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    level = models.IntegerField(validators=[MaxValueValidator(4), MinValueValidator(1)])

    def __str__(self):
        return f"{self.code} - {self.name}"

class InstructorCourse(models.Model):
    # instructor should be a CustomUser with role='instructor'
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='instructor_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('instructor', 'course'),)

    def __str__(self):
        return f"{self.instructor} teaches {self.course}"

class StudentCourse(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    # student should be a CustomUser with role='student'
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = (('student', 'course'),)

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"