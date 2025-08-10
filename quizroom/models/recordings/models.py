from django.db import models
from quizroom.models.quizzes.models import Quiz
from quizroom.models.users.models import CustomUser

class VideoChunk(models.Model):
    """
    Tracks individual video chunks uploaded by students during a quiz.
    These are temporary records that exist before the final video is merged.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='video_chunks')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='video_chunks')
    sequence_number = models.IntegerField(help_text='The order of this chunk in the video sequence')
    chunk_path = models.CharField(max_length=500, help_text='Path to the chunk in storage')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField(help_text='Size of the chunk in bytes')
    is_processed = models.BooleanField(default=False, help_text='Whether this chunk has been merged into the final video')

    class Meta:
        unique_together = ('quiz', 'student', 'sequence_number')
        ordering = ['sequence_number']
        indexes = [
            models.Index(fields=['quiz', 'student', 'is_processed']),
        ]

    def __str__(self):
        return f"Chunk {self.sequence_number} for {self.student} in {self.quiz}"
