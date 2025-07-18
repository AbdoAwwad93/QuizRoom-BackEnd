from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .permissions import IsInstructor
from quizroom.models.courses.models import Course
from quizroom.models.quizzes.models import Quiz, Question
from .serializers import QuestionCreateSerializer, QuestionSerializer

class InstructorQuizQuestionCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request, quiz_id):
        instructor = request.user
        quiz = Quiz.objects.filter(id=quiz_id).first()
        if not quiz:
            return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not Course.objects.filter(id=quiz.course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to add questions to this quiz.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = Question.objects.create(
            quiz=quiz,
            question_text=serializer.validated_data['question_text'],
            question_type='short_answer',
            correct_answer=None,
            points=serializer.validated_data['points'],
        )
        return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)

class InstructorQuizQuestionListView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, quiz_id):
        instructor = request.user
        quiz = Quiz.objects.filter(id=quiz_id).first()
        if not quiz:
            return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not Course.objects.filter(id=quiz.course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to view questions for this quiz.'}, status=status.HTTP_403_FORBIDDEN)
        questions = Question.objects.filter(quiz=quiz)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

class InstructorQuizQuestionEditRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]

    def patch(self, request, question_id):
        instructor = request.user
        question = Question.objects.filter(id=question_id).first()
        if not question:
            return Response({'detail': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)
        quiz = question.quiz
        if not Course.objects.filter(id=quiz.course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to edit this question.'}, status=status.HTTP_403_FORBIDDEN)
        allowed_fields = ['question_text', 'points']
        data = request.data
        updated = False
        for field in allowed_fields:
            if field in data:
                setattr(question, field, data[field])
                updated = True
        if updated:
            question.save()
            return Response(QuestionSerializer(question).data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'No valid fields to update.'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, question_id):
        instructor = request.user
        question = Question.objects.filter(id=question_id).first()
        if not question:
            return Response({'detail': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)
        quiz = question.quiz
        if not Course.objects.filter(id=quiz.course.id, instructorcourse__instructor=instructor).exists():
            return Response({'detail': 'You do not have permission to remove this question.'}, status=status.HTTP_403_FORBIDDEN)
        question.delete()
        return Response({'detail': 'Question deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
