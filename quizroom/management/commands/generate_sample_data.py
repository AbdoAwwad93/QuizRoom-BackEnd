from django.core.management.base import BaseCommand
from django.db import transaction
from quizroom.models import CustomUser, InstructorProfile, Course, InstructorCourse

class Command(BaseCommand):
    help = "Generate sample instructors and courses for FCAI Assiut"

    @transaction.atomic
    def handle(self, *args, **options):
        instructors_data = [
            {"name": "Ahmed Salem", "email": "ahmed.salem@fcai.au.edu.eg"},
            {"name": "Fatma Ali", "email": "fatma.ali@fcai.au.edu.eg"},
            {"name": "Mohamed Kamel", "email": "mohamed.kamel@fcai.au.edu.eg"},
            {"name": "Sara Hassan", "email": "sara.hassan@fcai.au.edu.eg"},
            {"name": "Tamer Abdelrahman", "email": "tamer.abdelrahman@fcai.au.edu.eg"},
            {"name": "Eman Gaber", "email": "eman.gaber@fcai.au.edu.eg"},
            {"name": "Khaled Amin", "email": "khaled.amin@fcai.au.edu.eg"},
            {"name": "Asmaa Nabil", "email": "asmaa.nabil@fcai.au.edu.eg"},
            {"name": "Hany Sobhy", "email": "hany.sobhy@fcai.au.edu.eg"},
            {"name": "Marwa Youssef", "email": "marwa.youssef@fcai.au.edu.eg"},
        ]

        courses_data = [
            {"name": "Introduction to Computer Science", "code": "CS101", "level": 1},
            {"name": "Digital Logic Design", "code": "IT102", "level": 1},
            {"name": "Data Structures", "code": "CS201", "level": 2},
            {"name": "Operating Systems", "code": "IT202", "level": 2},
            {"name": "Database Systems", "code": "CS301", "level": 3},
            {"name": "Computer Networks", "code": "IT302", "level": 3},
            {"name": "Artificial Intelligence", "code": "CS401", "level": 4},
            {"name": "Network Security", "code": "IT402", "level": 4},
        ]

        self.stdout.write("🔧 Creating instructors and profiles...")
        instructors = []
        for data in instructors_data:
            user, created = CustomUser.objects.get_or_create(
                email=data["email"],
                defaults={
                    "name": data["name"],
                    "role": "instructor",
                    "is_active": True
                }
            )
            if created:
                user.set_password("password123")
                user.save()
                self.stdout.write(f"Created instructor: {user.name}")
            else:
                self.stdout.write(f"Already exists: {user.name}")

            InstructorProfile.objects.get_or_create(user=user)
            instructors.append(user)

        self.stdout.write("Creating courses...")
        courses = []
        for data in courses_data:
            course, created = Course.objects.get_or_create(**data)
            if created:
                self.stdout.write(f"Created course: {course.code} - {course.name}")
            courses.append(course)

        self.stdout.write("Linking instructors to courses...")
        for i, course in enumerate(courses):
            instructor = instructors[i % len(instructors)]
            InstructorCourse.objects.get_or_create(instructor=instructor, course=course)
            self.stdout.write(f"{instructor.name} assigned to {course.code}")

        self.stdout.write(self.style.SUCCESS("Sample data created successfully."))
