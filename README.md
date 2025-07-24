# QuizRoom BackEnd

Backend for a student quiz management system, supporting both desktop and web clients, with full RESTful APIs for authentication, student/instructor management, course assignments, and more.

---

## 📑 Table of Contents
- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Sample Data](#sample-data)
- [Running the Server](#running-the-server)
- [Authentication](#authentication)
- [Student Management (Instructor Only)](#student-management-instructor-only)
  - [Quiz Management](#quiz-management-instructor-only)
  - [Course Management](#course-management-instructor-only)
  - [Quiz Endpoints](#quiz-endpoints)
  - [Student Endpoints](#student-endpoints)
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

---

### Student Management (Instructor Only)
1. **Create Student**
   - **POST** `/api/instructor/create-student/`
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
2. **List All Students Managed by Instructor**
   - **GET** `/api/instructor/students/`
   - Response:
     ```json
     [
       { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 }
     ]
     ```
3. **Assign Student to Instructor's Course**
   - **POST** `/api/instructor/students/<student_id>/assign-courses/`
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
4. **Update Student Profile**
   - **PATCH** `/api/instructor/students/<student_id>/update/`
   - Body:
     ```json
     { "name": "New Name", "email": "newemail@example.com", "password": "newpassword", "level": 2 }
     ```
   - Response:
     ```json
     { "student": { "id": 12, "email": "newemail@example.com", "name": "New Name", "level": 2 } }
     ```
5. **Remove Student from Instructor's Course**
   - **DELETE** `/api/instructor/students/<student_id>/remove/`
   - Response:
     ```json
     { "detail": "Student removed from your course." }
     ```
     or
     ```json
     { "detail": "Student was not assigned to your course." }
     ```

### Course Management (Instructor Only)
6. **List Instructor's Courses**
   - **GET** `/api/instructor/courses/`
   - Response:
     ```json
     [
       { "id": 1, "name": "Math 101", "code": "MATH101", "level": 2 }
     ]
     ```
7. **List Students in a Course**
   - **GET** `/api/instructor/courses/<course_id>/students/`
   - Response:
     ```json
     [
       { "id": 12, "email": "student@example.com", "name": "Student Name", "level": 2 }
     ]
     ```

### Quiz Management (Instructor Only)
8. **List All Quizzes for Instructor's Courses**
   - **GET** `/api/instructor/quizzes/`
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
9. **Create a Quiz** 
   - **POST** `/api/instructor/quizzes/`
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
  or
  ```json
  { "detail": "Instructor is not assigned to any course." }
  ```
#### 10. List All Questions in a Quiz
- **GET** `/api/instructor/quizzes/<quiz_id>/questions/`
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
  or
  ```json
  { "detail": "Quiz not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to view questions for this quiz." }
  ```
#### 11. Create Question for a Quiz
- **POST** `/api/instructor/quizzes/<quiz_id>/questions/create/`
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
  or
  ```json
  { "detail": "Quiz not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to add questions to this quiz." }
  ```

#### 12. Edit a Quiz
- **PATCH** `/api/instructor/quizzes/<quiz_id>/edit/`
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
  or
  ```json
  { "detail": "Quiz not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to edit this quiz." }
  ```
  or
  ```json
  { "detail": "No valid fields to update." }
  ```

#### 14. Edit a Quiz Question
- **PATCH** `/api/instructor/questions/<question_id>/edit/`
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
  or
  ```json
  { "detail": "Question not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to edit this question." }
  ```
  or
  ```json
  { "detail": "No valid fields to update." }
  ```

#### 15. Remove a Quiz Question
- **DELETE** `/api/instructor/questions/<question_id>/remove/`
- Response:
  ```json
  { "detail": "Question deleted successfully." }
  ```
  or
  ```json
  { "detail": "Question not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to remove this question." }
  ```

#### 16. Remove a Quiz
- **DELETE** `/api/instructor/quizzes/<quiz_id>/remove/`
- Response:
  ```json
  { "detail": "Quiz deleted successfully." }
  ```
  or
  ```json
  { "detail": "Quiz not found." }
  ```
  or
  ```json
  { "detail": "You do not have permission to delete this quiz." }
  ```


### Quiz Grading (Instructor Only)
17. **List Submissions for a Quiz**
   - **GET** `/api/instructor/quizzes/<quiz_id>/submissions/`
   - Response:
     ```json
     [
       {
         "id": 1,
         "student": 12,
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
18. **Retrieve a Submission with Answers**
   - **GET** `/api/instructor/submissions/<submission_id>/`
   - Response:
     ```json
     {
       "id": 1,
       "student": 12,
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
19. **Grade a Single Answer**
   - **PATCH** `/api/instructor/answers/<answer_id>/grade/`
   - Body:
     ```json
     { "points": 4, "feedback": "Almost correct." }
     ```
   - Response:
     ```json
     { "detail": "Answer graded successfully." }
     ```
20. **Set Overall Submission Feedback**
   - **PATCH** `/api/instructor/submissions/<submission_id>/feedback/`
   - Body:
     ```json
     { "feedback": "Excellent effort overall!" }
     ```
   - Response:
     ```json
     { "detail": "Submission feedback set." }
     ```
21. **Release All Grades/Feedback for a Quiz**
   - **POST** `/api/instructor/quizzes/<quiz_id>/release/`
   - Response:
     ```json
     { "detail": "3 submissions released to students." }
     ```



---
### Quiz Endpoints
1. **Quiz Details (with Questions)**
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

1. **List All Quizzes for Student**
   - **GET** `/api/student/quizzes/`
   - Returns all quizzes for all courses the student is enrolled in.
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

2. **List Current (Active) Quizzes for Student**
   - **GET** `/api/student/quizzes/current/`
   - Returns quizzes for enrolled courses that are currently active (by date).

3. **Retrieve Student's Quiz Submission (with Answers)**
   - **GET** `/api/student/quizzes/<quiz_id>/submission/`
   - Returns the student's submission for the specified quiz, including answers if submitted. If not submitted, returns `{"submission": null}`.
   - Response (if submission exists):

4. **List Student's Enrolled Courses**
   - **GET** `/api/student/courses/`
   - Returns a list of all courses the authenticated student is enrolled in.
   - Response:
     ```json
     [
       {
         "id": 1,
         "name": "Math 101",
         "code": "MATH101",
         "level": 2
       },
       {
         "id": 2,
         "name": "Physics 201",
         "code": "PHYS201",
         "level": 3
       }
     ]
     ```

     ```json
     {
       "id": 1,
       "student": 12,
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
   - Response (if no submission):
     ```json
     { "submission": null }
     ```

---
### Student Quiz Interaction

1. **List Questions for a Quiz (Student)**
   - **GET** `/api/student/quizzes/<quiz_id>/questions/`
   - Returns a list of questions for the specified quiz.
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

2. **Submit Answer for a Question**
   - **POST** `/api/student/quizzes/<quiz_id>/questions/<question_id>/answer/`
   - Body:
     ```json
     {
       "answer_text": "4"
     }
     ```
   - Submits the student's answer for the specified question.

3. **Submit Quiz**
   - **POST** `/api/student/quizzes/<quiz_id>/submit/`
   - Submits the entire quiz for grading.
   - Response:
     ```json
     {
       "detail": "Quiz submitted successfully."
     }
     ```

---
### Quiz Endpoints
1. **Quiz Details (with Questions)**
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

1. **List All Quizzes for Student**
   - **GET** `/api/student/quizzes/`
   - Returns all quizzes for all courses the student is enrolled in.
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

2. **List Current (Active) Quizzes for Student**
   - **GET** `/api/student/quizzes/current/`
   - Returns quizzes for enrolled courses that are currently active (by date).

3. **Retrieve Student's Quiz Submission (with Answers)**
   - **GET** `/api/student/quizzes/<quiz_id>/submission/`
   - Returns the student's submission for the specified quiz, including answers if submitted. If not submitted, returns `{"submission": null}`.
   - Response (if submission exists):

4. **List Student's Enrolled Courses**
   - **GET** `/api/student/courses/`
   - Returns a list of all courses the authenticated student is enrolled in.
   - Response:
     ```json
     [
       {
         "id": 1,
         "name": "Math 101",
         "code": "MATH101",
         "level": 2
       },
       {
         "id": 2,
         "name": "Physics 201",
         "code": "PHYS201",
         "level": 3
       }
     ]
     ```

     ```json
     {
       "id": 1,
       "student": 12,
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
   - Response (if no submission):
     ```json
     { "submission": null }
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
