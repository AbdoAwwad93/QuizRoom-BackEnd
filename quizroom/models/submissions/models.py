from django.db import models
from quizroom.models.users.models import CustomUser
from quizroom.models.quizzes.models import Quiz, Question

class StudentQuizSubmission(models.Model):
    # student should be a CustomUser with role='student'
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    submission_date = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    screen_recording_path = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        unique_together = (('student', 'quiz'),)

    def __str__(self):
        return f"Submission by {self.student} for {self.quiz}"

class StudentAnswer(models.Model):
    submission = models.ForeignKey(StudentQuizSubmission, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    points = models.IntegerField()

    class Meta:
        unique_together = (('submission', 'question'),)

    def __str__(self):
        return f"Answer to {self.question} in {self.submission}" 