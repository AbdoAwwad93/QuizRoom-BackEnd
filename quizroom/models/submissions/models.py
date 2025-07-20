from django.db import models
from quizroom.models.users.models import CustomUser
from quizroom.models.quizzes.models import Quiz, Question

class StudentQuizSubmission(models.Model):
    STATUS_CHOICES = [
        ('ungraded', 'Ungraded'),
        ('grading', 'Grading'),
        ('graded', 'Graded'),
        ('released', 'Released'),
    ]
    # student should be a CustomUser with role='student'
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Sum of awarded points for all answers, capped at quiz total_points.')
    screen_recording_path = models.CharField(max_length=500, null=True, blank=True)
    feedback = models.TextField(null=True, blank=True, help_text='Overall feedback for the submission from instructor.')
    graded_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when grading was completed.')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ungraded', help_text='Grading status of the submission.')

    class Meta:
        unique_together = (('student', 'quiz'),)

    def __str__(self):
        return f"Submission by {self.student} for {self.quiz}"

class StudentAnswer(models.Model):
    submission = models.ForeignKey(StudentQuizSubmission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    points = models.IntegerField(help_text='Points awarded for this answer (0 to question.points).')
    feedback = models.TextField(null=True, blank=True, help_text='Instructor feedback for this answer.')

    class Meta:
        unique_together = (('submission', 'question'),)

    def __str__(self):
        return f"Answer to {self.question} in {self.submission}"