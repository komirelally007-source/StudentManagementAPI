from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT NOT NULL
            )
        """)
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Student Management API",
    description="A beginner-friendly student records CRUD API using FastAPI and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=25)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=25)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    name: str
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: date


def row_to_student(row):
    return dict(row)


@app.get("/", tags=["General"])
def home():
    return {
        "message": "Welcome to the Student Management API",
        "documentation": "/docs",
        "available_endpoints": [
            "POST /students",
            "GET /students",
            "GET /students/{student_id}",
            "PUT /students/{student_id}",
            "PATCH /students/{student_id}",
            "DELETE /students/{student_id}",
        ],
    }


@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(student: StudentCreate):
    enrollment_date = student.enrollment_date or date.today()
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO students
                   (name, date_of_birth, email, phone, course, address, enrollment_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    student.name,
                    student.date_of_birth.isoformat(),
                    str(student.email),
                    student.phone,
                    student.course,
                    student.address,
                    enrollment_date.isoformat(),
                ),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM students WHERE student_id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this email already exists")
    return row_to_student(row)


@app.get("/students", response_model=list[StudentResponse], tags=["Students"])
def list_students(
    name: Optional[str] = Query(default=None, description="Filter by part of a student's name"),
    course: Optional[str] = Query(default=None, description="Filter by course"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    sql = "SELECT * FROM students WHERE 1=1"
    params = []
    if name:
        sql += " AND name LIKE ?"
        params.append(f"%{name}%")
    if course:
        sql += " AND course LIKE ?"
        params.append(f"%{course}%")
    sql += " ORDER BY student_id LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_student(row) for row in rows]


@app.get("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def get_student(student_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return row_to_student(row)


@app.put("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate):
    enrollment_date = student.enrollment_date or date.today()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT student_id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Student not found")
        try:
            conn.execute(
                """UPDATE students SET name=?, date_of_birth=?, email=?, phone=?,
                   course=?, address=?, enrollment_date=? WHERE student_id=?""",
                (
                    student.name, student.date_of_birth.isoformat(), str(student.email),
                    student.phone, student.course, student.address,
                    enrollment_date.isoformat(), student_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="A student with this email already exists")
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    return row_to_student(row)


@app.patch("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def update_student(student_id: int, student: StudentUpdate):
    changes = student.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"])
    for key, value in list(changes.items()):
        if isinstance(value, date):
            changes[key] = value.isoformat()

    allowed_fields = {
        "name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"
    }
    assignments = ", ".join(f"{key} = ?" for key in changes if key in allowed_fields)
    values = [changes[key] for key in changes if key in allowed_fields]
    values.append(student_id)

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT student_id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Student not found")
        try:
            conn.execute(
                f"UPDATE students SET {assignments} WHERE student_id = ?", values
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="A student with this email already exists")
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    return row_to_student(row)


@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM students WHERE student_id = ?", (student_id,)
        )
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": f"Student {student_id} deleted successfully"}
