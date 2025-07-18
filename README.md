# QuizRoom BackEnd

A production-grade backend for a student quiz management system, supporting both desktop and web clients, with full RESTful APIs for authentication, student/instructor management, course assignments, and more.

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
Create a `.env` file in the `quizroom_backend` directory with your database credentials:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Apply Migrations
```sh
python manage.py migrate
```

### 6. Run the Server
```sh
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

### **Authentication**
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

### **Instructor APIs** *(require instructor login)*

#### 1. Create Student
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
- Response: `{ "student": { ... } }`

#### 2. Assign Student to Instructor's Course
- **POST** `/api/instructor/students/<student_id>/assign-courses/`
- Body: `{}`
- Response: Success or already assigned message

#### 3. List Instructor's Courses
- **GET** `/api/instructor/courses/`
- Response: List of courses assigned to the instructor

#### 4. List Students in a Course
- **GET** `/api/instructor/courses/<course_id>/students/`
- Response: List of students assigned to the given course (if the instructor manages it)

#### 5. List All Students Managed by Instructor
- **GET** `/api/instructor/students/`
- Response: List of all students assigned to the instructor's course (for now, one course)

#### 6. Remove Student from Instructor's Course
- **DELETE** `/api/instructor/students/<student_id>/remove/`
- Response: Success message if removed, or not found if the student was not assigned

#### 7. Update Student Profile
- **PATCH** `/api/instructor/students/<student_id>/update/`
- Body: `{ "name": "New Name", "email": "newemail@example.com" }` (either or both fields)
- Response: Updated student object or error message

#### 8. List All Quizzes for Instructor's Courses
- **GET** `/api/instructor/quizzes/`
- Response: List of quizzes for all courses managed by the instructor

---

## 🔒 Permissions & Roles
- **Students**: Can only access endpoints meant for students (to be implemented).
- **Instructors**: Can only access instructor endpoints (enforced by custom permission).

---

## 🧑‍💻 Development Notes
- All endpoints return JSON.
- All errors are returned with appropriate HTTP status codes and messages.

---
