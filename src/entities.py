"""Domain entities used by the Streamlit/DAL layer."""
from dataclasses import dataclass
from datetime import date


@dataclass
class Employee:
    employee_id: str
    first_name: str
    last_name: str
    email: str
    gender: str
    age: int
    department_id: int
    role: str
    salary: float
    hire_date: date
    status: str = "Active"


@dataclass
class Project:
    project_id: str
    project_name: str
    description: str
    start_date: date
    end_date: date | None
    status: str


@dataclass
class Review:
    review_id: str
    employee_id: str
    project_id: str
    review_date: date
    rating: int
    review_score: float
    comments: str
