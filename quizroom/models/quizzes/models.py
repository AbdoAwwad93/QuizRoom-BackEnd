from django.db import models
from ..courses.models import Course

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    week_number = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration = models.IntegerField(help_text='Duration in minutes')
    total_points = models.IntegerField()
    created_at = models.DateTimeField(null=True, blank=True,auto_now_add= True)
    updated_at = models.DateTimeField(null=True, blank=True,auto_now= False)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES)
    correct_answer = models.TextField(null=True, blank=True)
    points = models.IntegerField()

    def __str__(self):
        return self.question_text

class QuestionBank(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('course', 'question'),)

    def __str__(self):
        return f"{self.question} in {self.course} bank"

class QuizStatistics(models.Model):
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE)
    total_submissions = models.IntegerField()
    average_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    highest_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lowest_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Statistics for {self.quiz}"

class QuestionStatistics(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    total_answers = models.IntegerField()
    correct_answers = models.IntegerField()
    incorrect_answers = models.IntegerField()
    accuracy_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Statistics for {self.question}" 