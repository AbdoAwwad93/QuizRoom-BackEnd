# QuizRoom BackEnd

Backend for a student quiz management system, supporting both desktop and web clients, with full RESTful APIs for authentication, student/instructor management, course assignments, and more.

---

## 📑 Table of Contents
- [Getting Started](#-getting-started)
- [Create and Activate a Virtual Environment](#2-create-and-activate-a-virtual-environment)
- [Install Dependencies](#3-install-dependencies)
- [Configure Environment Variables](#4-configure-environment-variables)
- [Apply Migrations](#5-apply-migrations)
- [Generate Sample Data](#6-generate-sample-data)
- [Authentication](#️-authentication)
- [Student Management (Instructor Only)](#student-management-instructor-only)
- [Quiz Management (Instructor Only)](#quiz-management-instructor-only)
- [Course Management (Instructor Only)](#course-management-instructor-only)
- [Quiz Grading (Instructor Only)](#quiz-grading-instructor-only)
- [Quiz Endpoints](#quiz-endpoints)
- [Student Endpoints](#student-endpoints)
- [Student Quiz Interaction](#student-quiz-interaction)
---
## 🚀 Getting Started

### 1. Clone the Repository
```sh
git clone <repo-url>
cd QuizRoom-BackEnd
```

### 2. Create and Activate a Virtual Environment
```sh
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root directory with your database credentials:
```
DB_NAME=quizroom_db
DB_USER=quizroom_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Apply Migrations
```bash
python manage.py migrate
```

### 6. Generate Sample Data
To populate the database with sample data, run:
```bash
python manage.py generate_sample_data
```
This will create:
- Sample instructors, courses
- **IMPORTANT:** The default password for all instructors is **`password123`**

### 6b. Generate Student Sample Data
To create sample students for development/testing, run:
```bash
python manage.py generate_student_data
```
This will create:
- 10 sample student users (role: student) with levels 1–4
- **IMPORTANT:** The default password for all students is **`password123`**

### 7. Run the Server
```bash
python manage.py runserver
```
---

## 🛡️ Authentication
- Uses JWT (JSON Web Token) for secure authentication.
- When you log in, you receive two tokens:
  - **Access Token:** Used to authenticate all API requests. Include it in the `Authorization` header:
    ```
    Authorization: Bearer <access_token>
    ```
    ⚠️ **Note:** For testing purposes, the access token in this project is valid for 1 year (default is 5 minutes in production). This is configured in `settings.py` under `SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']`.
  - **Refresh Token:** Used to obtain a new access token when the old one expires. 
- To refresh your access token, use the `/api/auth/refresh/` endpoint with your refresh token.

---

## 📚 API Endpoints

### Authentication
- **POST** `/api/auth/login/`
  - Body: `{ "email": "user@example.com", "password": "yourpassword" }`
  - Response: `{ "user": {...}, "refresh": "...", "access": "..." }`
- **POST** `/api/auth/refresh/`
  - Body: `{ "refresh": "<refresh_token>" }`
  - Response: `{ "access": "..." }`
- **POST** `/api/auth/verify/`
  - Body: `{ "token": "<any_token>" }`
  - Response: Validity info

### Student Management (Instructor Only)
- **Create Student**
   - **POST** `/api/instructor/create-student/`
   - Description: Create a new student and assign them to the instructor's course.
   - Body:
     ```json
     {
       "email": "student@example.com",
       "name": "Student Name",
       "password": "studentpassword",
       "level": 2
     }
     ```
   - Response:
     ```json
     { "student": { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 } }
     ```
- **List All Students Managed by Instructor**
   - **GET** `/api/instructor/students/`
   - Description: Retrieve a list of all students managed by the authenticated instructor.
   - Response:
     ```json
     [
       { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 }
     ]
     ```
- **List All Students in the System (Instructor Only)**
   - **GET** `/api/instructor/students/all/`
   - Description: Retrieve a list of all students in the system (not just those managed by the instructor). Requires instructor authentication.
   - Response:
     ```json
     [
       { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 }
     ]
     ```
- **Assign Student to Instructor's Course**
   - **POST** `/api/instructor/students/<student_id>/assign-courses/`
   - Description: Assign an existing student to the instructor's course.
   - Body:
     ```json
     {}
     ```
   - Response:
     ```json
     { "detail": "Student assigned to your course successfully." }
     ```
     or
     ```json
     { "detail": "Student is already assigned to your course." }
     ```
- **Update Student Profile**
   - **PATCH** `/api/instructor/students/<student_id>/update/`
   - Description: Update the profile information (name, email, password, level) for a student.
   - Body:
     ```json
     { "name": "New Name", "email": "newemail@example.com", "password": "newpassword", "level": 2 }
     ```
   - Response:
     ```json
     { "student": { "id": 12, "email": "newemail@example.com", "name": "New Name", "level": 2 } }
     ```
- **Remove Student from Instructor's Course**
   - **DELETE** `/api/instructor/students/<student_id>/remove/`
   - Description: Remove a student from the instructor's course.
   - Response:
     ```json
     { "detail": "Student removed from your course." }
     ```
     or
     ```json
     { "detail": "Student was not assigned to your course." }
     ```

### Course Management (Instructor Only)
- **List Instructor's Courses**
   - **GET** `/api/instructor/courses/`
   - Description: Retrieve a list of all courses managed by the authenticated instructor.
   - Response:
     ```json
     [
       { "id": 1, "name": "Math 101", "code": "MATH101", "level": 2 }
     ]
     ```
- **List Students in a Course**
   - **GET** `/api/instructor/courses/<course_id>/students/`
   - Description: Retrieve a list of all students enrolled in a specific course managed by the instructor.
   - Response:
     ```json
     [
       { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 }
     ]
     ```

### Quiz Management (Instructor Only)
- **List All Quizzes for Instructor's Courses**
   - **GET** `/api/instructor/quizzes/`
   - Description: Retrieve all quizzes created for courses managed by the instructor.
   - Response:
     ```json
     [
       {
         "id": 5,
         "title": "Quiz2",
         "course_id": 1,
         "course_name": "Math 101",
         "week_number": 1,
         "start_date": "2025-07-20T09:00:00+03:00",
         "end_date": "2025-07-20T10:00:00+03:00",
         "duration": 60,
         "total_points": 100,
         "created_at": "2025-07-18T04:30:16.318838+03:00",
         "updated_at": "2025-07-18T05:29:03.000000+03:00"
       }
     ]
     ```
- **Create a Quiz** 
   - **POST** `/api/instructor/quizzes/`
   - Description: Create a new quiz for the instructor's course.
   - Body:
     ```json
     {
       "title": "Quiz2",
       "week_number": 1,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100,
       "questions": [
         {"question_text": "What is 2+2?", "points": 10},
         {"question_text": "Name a primary color.", "points": 5}
       ]
     }
     ```
   - Response:
     ```json
     {
       "id": 5,
       "title": "Quiz2",
       "course_id": 1,
       "course_name": "Math 101",
       "week_number": 1,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100,
       "created_at": "2025-07-18T04:30:16.318838+03:00",
       "updated_at": "2025-07-18T05:29:03.000000+03:00"
     }
     ```
   
- **List All Questions in a Quiz**
   - **GET** `/api/instructor/quizzes/<quiz_id>/questions/`
   - Description: Retrieve all questions for a specific quiz managed by the instructor.
   - Response:
     ```json
     [
       {
         "id": 1,
         "quiz": 5,
         "question_text": "What is 2 + 2?",
         "question_type": "short_answer",
         "correct_answer": null,
         "points": 5
       }
     ]
     ```
- **Create Question for a Quiz**
   - **POST** `/api/instructor/quizzes/<quiz_id>/questions/create/`
   - Description: Add a new question to a specific quiz.
   - Body:
     ```json
     {
       "question_text": "What is 2 + 2?",
       "points": 5
     }
     ```
   - Response:
     ```json
     {
       "id": 1,
       "quiz": 5,
       "question_text": "What is 2 + 2?",
       "question_type": "short_answer",
       "correct_answer": null,
       "points": 5
     }
     ```
- **Edit a Quiz**
   - **PATCH** `/api/instructor/quizzes/<quiz_id>/edit/`
   - Description: Update details of an existing quiz (title, dates, duration, etc.).
   - Body (any subset of fields):
     ```json
     {
       "title": "Updated Quiz Title",
       "week_number": 2,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100
     }
     ```
   - Response:
     ```json
     {
       "id": 5,
       "title": "Updated Quiz Title",
       "course_id": 1,
       "course_name": "Math 101",
       "week_number": 2,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100,
       "created_at": "2025-07-18T04:30:16.318838+03:00",
       "updated_at": "2025-07-18T05:29:03.000000+03:00"
     }
     ```
- **Edit a Quiz Question**
   - **PATCH** `/api/instructor/questions/<question_id>/edit/`
   - Description: Update the text or points of a specific quiz question.
   - Body:
     ```json
     {
       "question_text": "What is the capital of France?",
       "points": 10
     }
     ```
   - Response:
     ```json
     {
       "id": 2,
       "quiz": 5,
       "question_text": "What is the capital of France?",
       "question_type": "short_answer",
       "correct_answer": null,
       "points": 10
     }
     ```
- **Remove a Quiz Question**
   - **DELETE** `/api/instructor/questions/<question_id>/remove/`
   - Description: Delete a question from a quiz.
   - Response:
     ```json
     { "detail": "Question deleted successfully." }
     ```
- **Remove a Quiz**
   - **DELETE** `/api/instructor/quizzes/<quiz_id>/remove/`
   - Description: Delete a quiz from the instructor's course.
   - Response:
     ```json
     { "detail": "Quiz deleted successfully." }
     ```

### Quiz Grading (Instructor Only)
- **List Submissions for a Quiz**
   - **GET** `/api/instructor/quizzes/<quiz_id>/submissions/`
   - Description: List all student submissions for a specific quiz for grading.
   - Response:
     ```json
     [
       {
         "id": 1,
         "student": 12,
         "student_name": "Student Name",
         "quiz": 5,
         "submission_date": "2025-07-20T12:00:00+03:00",
         "grade": 95,
         "feedback": "Great work!",
         "graded_at": "2025-07-20T15:00:00+03:00",
         "status": "graded",
         "answers": [ ... ]
       }
     ]
     ```
- **Retrieve a Submission with Answers**
   - **GET** `/api/instructor/submissions/<submission_id>/`
   - Description: Retrieve a specific student's quiz submission, including all answers and grading details.
   - Response:
     ```json
     {
       "id": 1,
       "student": 12,
       "student_name": "Student Name",
       "quiz": 5,
       "submission_date": "2025-07-20T12:00:00+03:00",
       "grade": 95,
       "feedback": "Great work!",
       "graded_at": "2025-07-20T15:00:00+03:00",
       "status": "graded",
       "answers": [
         {
           "id": 101,
           "question": 10,
           "answer_text": "4",
           "points": 5,
           "feedback": "Correct!"
         }
       ]
     }
     ```
- **Grade All Answers in a Submission**
    - **PATCH** `/api/instructor/submissions/<submission_id>/grade/`
    - Description: Grade all answers for a student's quiz submission in one request.
    - Body:
      ```json
      {
        "answers": [
          { "answer_id": 101, "points": 5, "feedback": "Good!" },
          { "answer_id": 102, "points": 3, "feedback": "Partial credit." }
        ]
      }
      ```
    - Response:
      ```json
      { "detail": "All answers graded successfully." }
      ```
- **Edit Grade/Feedback for a Single Answer**
    - **PATCH** `/api/instructor/answers/<answer_id>/edit-grade/`
    - Description: Edit the grade and feedback for a single answer.
    - Body:
      ```json
      { "points": 4, "feedback": "Almost correct." }
      ```
    - Response:
      ```json
      { "detail": "Answer graded successfully." }
      ```
- **Edit Overall Submission Feedback**
    - **PATCH** `/api/instructor/submissions/<submission_id>/edit-feedback/`
    - Description: Edit the overall feedback for a student's quiz submission after grading.
    - Body:
      ```json
      { "feedback": "Excellent effort overall!" }
      ```
    - Response:
      ```json
      { "detail": "Submission feedback set." }
      ```
- **Release All Grades/Feedback for a Quiz**
    - **POST** `/api/instructor/quizzes/<quiz_id>/release/`
    - Description: Release all graded submissions for a quiz, making grades and feedback visible to students.
    - Response:
      ```json
      { "detail": "3 submissions released to students." }
      ```

### Quiz Endpoints
- **Quiz Details (with Questions)**
   - **GET** `/api/quiz/<quiz_id>/`
   - Returns quiz details and a list of all questions for that quiz.
   - Response:
     ```json
     {
       "id": 5,
       "title": "Quiz2",
       "course_id": 1,
       "course_name": "Math 101",
       "week_number": 1,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100,
       "created_at": "2025-07-18T04:30:16.318838+03:00",
       "updated_at": "2025-07-18T05:29:03.000000+03:00",
       "questions": [
         {
           "id": 1,
           "quiz": 5,
           "question_text": "What is 2 + 2?",
           "question_type": "short_answer",
           "correct_answer": null,
           "points": 5
         }
       ]
     }
---
### Student Endpoints

- **List All Quizzes for Student**
   - **GET** `/api/student/quizzes/`
   - Description: Retrieve all quizzes for all courses the authenticated student is enrolled in.
   - Response:
     ```json
     [
       {
         "id": 5,
         "title": "Quiz2",
         "course_id": 1,
         "course_name": "Math 101",
         "week_number": 1,
         "start_date": "2025-07-20T09:00:00+03:00",
         "end_date": "2025-07-20T10:00:00+03:00",
         "duration": 60,
         "total_points": 100,
         "created_at": "2025-07-18T04:30:16.318838+03:00",
         "updated_at": "2025-07-18T05:29:03.000000+03:00"
       }
     ]
     ```

- **List Current (Active) Quizzes for Student**
   - **GET** `/api/student/quizzes/current/`
   - Description: Retrieve quizzes for enrolled courses that are currently active (by date).

- **Retrieve Student's Quiz Submission (with Answers)**
   - **GET** `/api/student/quizzes/<quiz_id>/submission/`
   - Description: Retrieve the authenticated student's submission for a quiz, including all answers and feedback if released. Returns `{"submission": null}` if not submitted.
   - Response (if submission exists):
     ```json
     {
       "submission_id": 1,
       "quiz_id": 5,
       "status": "graded",
       "questions": [
         {
           "question_id": 1,
           "question_text": "What is 2 + 2?",
           "answer_text": "4",
           "points": 5,
           "feedback": "Correct!"
         }
       ],
       "grade": 95,
       "feedback": "Great work!",
       "graded_at": "2025-07-20T15:00:00+03:00"
     }
     ```

- **List Student's Enrolled Courses**
   - **GET** `/api/student/courses/`
   - Description: Retrieve a list of all courses the authenticated student is enrolled in, including instructor names.
   - Response:
     ```json
     [
       {
         "id": 1,
         "name": "Math 101",
         "code": "MATH101",
         "level": 2,
         "instructor_name": "Mohamed"
       },
       {
         "id": 2,
         "name": "Physics 201",
         "code": "PHYS201",
         "level": 3
       }
     ]
     ```

---
### Student Quiz Interaction

- **List Questions for a Quiz (Student)**
   - **GET** `/api/student/quizzes/<quiz_id>/questions/`
   - Description: Retrieve all questions for a quiz available to the authenticated student.
   - Response:
     ```json
     [
       {
         "id": 101,
         "text": "What is 2+2?",
         "question_type": "multiple_choice",
         "choices": ["1", "2", "3", "4"]
       }
     ]
     ```

- **Submit Answer for a Question**
   - **POST** `/api/student/quizzes/<quiz_id>/questions/<question_id>/answer/`
   - Description: Submit an answer for a specific question in a quiz.
   - Body:
     ```json
     {
       "answer_text": "4"
     }
     ```

- **Submit Quiz**
   - **POST** `/api/student/quizzes/<quiz_id>/submit/`
   - Description: Submit all answers for a quiz in bulk for grading and finalization.
   - Body:
     ```json
      {
        "answers": [
          {"question_id": 1, "answer_text": "Answer for Q1"},
          {"question_id": 2, "answer_text": "Answer for Q2"},
          ...
        ]
      }
    ```
   - Response:
     ```json
     {
       "detail": "Quiz submitted successfully."
     }
     ```

---
### Quiz Endpoints
- **Quiz Details (with Questions)**
   - **GET** `/api/quiz/<quiz_id>/`
   - Returns quiz details and a list of all questions for that quiz.
   - Response:
     ```json
     {
       "id": 5,
       "title": "Quiz2",
       "course_id": 1,
       "course_name": "Math 101",
       "week_number": 1,
       "start_date": "2025-07-20T09:00:00+03:00",
       "end_date": "2025-07-20T10:00:00+03:00",
       "duration": 60,
       "total_points": 100,
       "created_at": "2025-07-18T04:30:16.318838+03:00",
       "updated_at": "2025-07-18T05:29:03.000000+03:00",
       "questions": [
         {
           "id": 1,
           "quiz": 5,
           "question_text": "What is 2 + 2?",
           "question_type": "short_answer",
           "correct_answer": null,
           "points": 5
         }
       ]
     }
     ```
---
## 🔒 Permissions & Roles
- **Students**: Can only access endpoints meant for students (to be implemented).
- **Instructors**: Can only access instructor endpoints (enforced by custom permission).

---

## 🧑‍💻 Development Notes
- All endpoints return JSON.
- All errors are returned with appropriate HTTP status codes and messages.

---
