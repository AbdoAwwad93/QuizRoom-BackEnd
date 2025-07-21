from django.core.management.base import BaseCommand
from django.db import transaction
from quizroom.models.users.models import CustomUser, StudentProfile

class Command(BaseCommand):
    help = "Generate sample students for FCAI Assiut"

    @transaction.atomic
    def handle(self, *args, **options):
        students_data = [
            {"name": "Omar Youssef", "email": "omar.youssef@student.fcai.au.edu.eg", "level": 1},
            {"name": "Laila Samir", "email": "laila.samir@student.fcai.au.edu.eg", "level": 2},
            {"name": "Mahmoud Fathy", "email": "mahmoud.fathy@student.fcai.au.edu.eg", "level": 3},
            {"name": "Nada Adel", "email": "nada.adel@student.fcai.au.edu.eg", "level": 1},
            {"name": "Youssef Tarek", "email": "youssef.tarek@student.fcai.au.edu.eg", "level": 4},
            {"name": "Menna Wael", "email": "menna.wael@student.fcai.au.edu.eg", "level": 2},
            {"name": "Ahmed Hossam", "email": "ahmed.hossam@student.fcai.au.edu.eg", "level": 3},
            {"name": "Salma Khaled", "email": "salma.khaled@student.fcai.au.edu.eg", "level": 4},
            {"name": "Mariam Mostafa", "email": "mariam.mostafa@student.fcai.au.edu.eg", "level": 1},
            {"name": "Kareem Hassan", "email": "kareem.hassan@student.fcai.au.edu.eg", "level": 2},
        ]

        self.stdout.write("Creating students and profiles...")
        for data in students_data:
            user, created = CustomUser.objects.get_or_create(
                email=data["email"],
                defaults={
                    "name": data["name"],
                    "role": "student",
                    "is_active": True
                }
            )
            if created:
                user.set_password("password123")
                user.save()
                self.stdout.write(f"Created student: {user.name}")
            else:
                self.stdout.write(f"Already exists: {user.name}")

            StudentProfile.objects.get_or_create(user=user, defaults={"level": data["level"]})
