# Student Management API

A beginner-friendly backend internship project for managing student records with **Python, FastAPI, and SQLite**.

## Features

- Create, list, view, update, and delete student records (CRUD)
- SQLite database persistence
- Student fields: unique ID, name, date of birth, email, phone, course, address, enrollment date
- Filter students by name or course
- Request validation and clear errors for missing records or duplicate email addresses
- Interactive API documentation at `/docs`

## Requirements

- Python 3.10 or newer
- Internet connection for the initial package installation

## Setup

### 1. Open the project folder

Open `StudentManagementAPI` in VS Code.

### 2. Create and activate a virtual environment (recommended)

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the API

```bash
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/docs> in your browser to test the endpoints. The `students.db` database file is created automatically the first time the app starts.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Welcome message |
| POST | `/students` | Create a student |
| GET | `/students` | List students |
| GET | `/students?name=An` | Filter by name |
| GET | `/students?course=CSE` | Filter by course |
| GET | `/students/{student_id}` | Get one student |
| PUT | `/students/{student_id}` | Replace all student fields |
| PATCH | `/students/{student_id}` | Update selected fields |
| DELETE | `/students/{student_id}` | Delete a student |

## Sample request: create a student

In `/docs`, open `POST /students`, click **Try it out**, and use dummy data like:

```json
{
  "name": "Ananya Rao",
  "date_of_birth": "2005-04-12",
  "email": "ananya.demo@example.com",
  "phone": "9000000001",
  "course": "CSE",
  "address": "Hyderabad",
  "enrollment_date": "2025-08-01"
}
```

The response contains the automatically generated `student_id`. Use that ID to view, update, or delete the record.

## Example PATCH request

For `PATCH /students/1`:

```json
{
  "course": "CSE - AI and ML"
}
```

Use the actual student ID returned by your API.

## Important notes

- Use dummy student information for demonstrations. Do not upload real students' personal data.
- Do not commit passwords, API keys, or secrets.
- This is a learning project. Before production use, add authentication, authorization, rate limiting, and deployment hardening.
- The optional Ollama AI extension is not included because the assignment states the core CRUD application is sufficient.

## Suggested GitHub repository description

`Student records CRUD REST API built with Python, FastAPI, and SQLite for an internship project.`

## Before submission

- [ ] Run the application locally.
- [ ] Test create, read, update, and delete in `/docs`.
- [ ] Confirm a record remains after restarting the server.
- [ ] Take screenshots of successful API tests if requested.
- [ ] Upload the source code and README to your GitHub repository.
- [ ] Submit your GitHub repository URL through the channel specified by your trainer.
