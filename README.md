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
- [Statistics Endpoints](#statistics-endpoints)
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

### 3b. API Pagination Settings
All list endpoints in this API are paginated by default using Django REST Framework's `PageNumberPagination`.

- **Default page size:** 10 items per page
- **How to request a specific page:**
  - Use the `?page=<number>` query parameter, e.g. `/api/student/submissions/?page=2`
- **Paginated response format:**
  ```json
  {
    "count": 42,
    "next": "http://localhost:8000/api/student/submissions/?page=2",
    "previous": null,
    "results": [
      { /*first page of*/ }
    ]
  }
  ```
- **To change the default page size:** Edit `PAGE_SIZE` in `quizroom_backend/settings.py` under the `REST_FRAMEWORK` section.

All frontend and API consumers should expect this paginated response format for any endpoint returning a list of objects.

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
    ⚠️ **Note:** The access token in this project is valid for 5 minutes. This is configured in `settings.py` under `SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']`.
  - **Refresh Token:** Used to obtain a new access token when the old one expires. 
- To refresh your access token, use the `/api/auth/refresh/` endpoint with your refresh token.

---

## 📚 API Endpoints

### Authentication
- **POST** `/api/auth/student-login/`
  - Body: `{ "email": "student@example.com", "password": "yourpassword" }`
  - Description: Login endpoint for students only. Only users with the student role can authenticate here.
  - Response (success):
    ```json
    { "user": { ... }, "refresh": "...", "access": "..." }
    ```
  - Response (invalid credentials or not a student):
    ```json
    { "detail": "Invalid credentials." }
    ```

- **POST** `/api/auth/instructor-login/`
  - Body: `{ "email": "instructor@example.com", "password": "yourpassword" }`
  - Description: Login endpoint for instructors only. Only users with the instructor role can authenticate here.
  - Response (success):
    ```json
    { "user": { ... }, "refresh": "...", "access": "..." }
    ```
  - Response (invalid credentials or not an instructor):
    ```json
    { "detail": "Invalid credentials." }
    ```
- **POST** `/api/auth/refresh/`
  - Body: `{ "refresh": "<refresh_token>" }`
  - Response: `{ "access": "..." }`
- **POST** `/api/auth/logout/`
  - Body: `{ "refresh": "<refresh_token>" }`
  - Description: Blacklists the provided refresh token, logging the user out from this session/device.
  - Response (success):
    ```json
    { "detail": "Logout successful." }
    ```
  - Response (error):
    ```json
    { "detail": "Refresh token is required." }
    ```
    or
    ```json
    { "detail": "Invalid or expired token." }
    ```
- **POST** `/api/auth/verify/`
  - Body: `{ "token": "<any_token>" }`
  - Response: Validity info

---

### Password Reset

- **POST** `/api/auth/request-password-reset/`
  - Description: Initiate password reset by requesting an OTP to be sent to the user's email.
  - Body:
    ```json
    { "email": "user@example.com" }
    ```
  - Response:
    ```json
    { "detail": "If this email exists, an OTP has been sent." }
    ```

- **POST** `/api/auth/verify-otp/`
  - Description: Verify the OTP sent to the user's email.
  - Body:
    ```json
    { "email": "user@example.com", "otp": "1234567" }
    ```
  - Response (success):
    ```json
    { "detail": "OTP verified successfully." }
    ```
  - Response (failure):
    ```json
    { "detail": "Invalid or expired OTP." }
    ```

- **POST** `/api/auth/reset-password/`
  - Description: Reset password using the OTP sent to the user's email.
  - Body:
    ```json
    { "email": "user@example.com", "otp": "1234567", "new_password": "NewPassword123!" }
    ```
  - Response (success):
    ```json
    { "detail": "Password has been reset." }
    ```
  - Response (failure):
    ```json
    { "detail": "Password reset failed." }
    ```

  - **Security Notes:**
    - OTP is valid for 10 minutes.
    - After 5 failed attempts, OTP entry is blocked for 30 minutes.
    - Password must be at least 8 characters.

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
           "question_id": 10,
           "question_text": "What is 2 + 2?",
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
     ```
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
   - Response:
     ```json
     [
    {
      "id": 12,
      "title": "Algebra Midterm",
      "course_id": 3,
      "course_name": "Algebra 101",
      "week_number": 6,
      "start_date": "2025-07-20T09:00:00Z",
      "end_date": "2025-07-29T23:59:00Z",
      "duration": 60,
      "total_points": 100,
      "created_at": "2025-07-01T10:00:00Z",
      "updated_at": "2025-07-10T12:00:00Z",
      "submitted": true
    },
    {
      "id": 15,
      "title": "Geometry Quiz",
      "course_id": 3,
      "course_name": "Algebra 101",
      "week_number": 7,
      "start_date": "2025-07-25T08:00:00Z",
      "end_date": "2025-07-30T23:59:00Z",
      "duration": 45,
      "total_points": 50,
      "created_at": "2025-07-15T09:30:00Z",
      "updated_at": "2025-07-20T11:00:00Z",
      "submitted": false
    }
  ]
  ```
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

- **List All Student Submissions**
   - **GET** `/api/student/submissions/`
   - Description: Retrieve all quiz submissions for the authenticated student
   - Response:
     ```json
     [
       {
         "id": 12,
         "student": 7,
         "student_name": "Ahmed Ali",
         "quiz": 5,
         "quiz_title": "Quiz2",
         "course_name": "Math 101",
         "submission_date": "2025-07-20T09:45:00+03:00",
         "grade": 85,
         "feedback": "Good job! Review question 3.",
         "graded_at": "2025-07-21T10:00:00+03:00",
         "status": "graded",
         "answers": [
           {
             "id": 201,
             "question_id": 1,
             "question_text": "What is 2+2",
             "answer_text": "42",
             "points": 10,
             "feedback": "Correct"
           }
         ]
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

### Statistics Endpoints

#### Instructor Statistics

- **GET** `/api/instructor/statistics/summary/`
  - Description: Returns the total number of quizzes the instructor owns, the number of students in their courses, and the number of student submissions for their quizzes.
  - Response:
    ```json
    {
      "total_quizzes": 8,
      "total_students": 53,
      "total_submissions": 211
    }
    ```

- **GET** `/api/instructor/statistics/quiz-scores/<quiz_id>/`
  - Description: Returns average, highest, and lowest scores for the specified quiz.
  - Response:
    ```json
    {
      "quiz_id": 5,
      "quiz_title": "Quiz2",
      "average_score": 82.5,
      "highest_score": 95,
      "lowest_score": 60
    }
    ```

- **GET** `/api/instructor/statistics/submission-rates/<quiz_id>/`
  - Description: Shows which students submitted or did not submit for a given quiz.
  - Response:
    ```json
    {
      "quiz_id": 5,
      "quiz_title": "Quiz2",
      "submitted_students": [
        { "id": 12, "email": "student1@example.com", "name": "Student One" }
      ],
      "not_submitted_students": [
        { "id": 13, "email": "student2@example.com", "name": "Student Two" }
      ]
    }
    ```

- **GET** `/api/instructor/statistics/grade-distribution/<quiz_id>/`
  - Description: Returns grade distribution (histogram) for a quiz. **The bins and range labels are dynamically generated based on the quiz's total points. For example, a 100-point quiz will use 10-point bins (0-9, 10-19, ..., 90-100), but a 40-point quiz will use 4-point bins (0-3, 4-7, ..., 36-40) and so on.**
  - Response (example for a 100-point quiz):
    ```json
    {
      "quiz_id": 5,
      "quiz_title": "Quiz2",
      "grade_distribution": {
        "0-9": 0,
        "10-19": 0,
        "20-29": 0,
        "30-39": 0,
        "40-49": 1,
        "50-59": 2,
        "60-69": 4,
        "70-79": 6,
        "80-89": 8,
        "90-100": 3
      }
    }
    ```
  - Response (example for a 40-point quiz):
    ```json
    {
      "quiz_id": 7,
      "quiz_title": "Quiz4",
      "grade_distribution": {
        "0-3": 0,
        "4-7": 1,
        "8-11": 0,
        "12-15": 2,
        "16-19": 0,
        "20-23": 3,
        "24-27": 1,
        "28-31": 1,
        "32-35": 0,
        "36-40": 2
      }
    }
    ```

- **GET** `/api/instructor/statistics/student-progress/`
  - Description: For each student in the course, shows number of completed and pending quizzes.
  - Response:
    ```json
    {
      "course_id": 1,
      "course_name": "Math 101",
      "student_progress": [
        { "student_id": 12, "student_name": "Student One", "completed_quizzes": 3, "pending_quizzes": 1 },
        { "student_id": 13, "student_name": "Student Two", "completed_quizzes": 2, "pending_quizzes": 2 }
      ]
    }
    ```

#### Student Statistics
- **GET** `/api/student/statistics/performance-summary/<course_id>/`
  - Description: Returns the student’s average score and ranking in the course.
  - Response:
    ```json
    {
      "course_id": 1,
      "course_name": "Math 101",
      "average_score": 85.0,
      "ranking": 2,
      "total_students": 25
    }
    ```


## 🔒 Permissions & Roles
- **Students**: Can only access endpoints meant for students (to be implemented).
- **Instructors**: Can only access instructor endpoints (enforced by custom permission).

---

## 🧑‍💻 Development Notes
- All endpoints return JSON.
- All errors are returned with appropriate HTTP status codes and messages.

---
