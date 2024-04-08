from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

# MongoDB setup
client = AsyncIOMotorClient("mongodb+srv://amanbhatt02:aman2001@cluster0.ey10qw7.mongodb.net")
db = client.library_management
students_collection = db.get_collection("students")

class Address(BaseModel):
    city: str
    country: str

class Student(BaseModel):
    name: str
    age: int
    address: Address

class StudentInDB(Student):
    id: str

# API to create a student in the system
@app.post("/students", response_model=StudentInDB, status_code=status.HTTP_201_CREATED)
async def create_student(student: Student):
    try:
        student_dict = student.dict()
        result = await students_collection.insert_one(student_dict)
        return {"id": str(result.inserted_id), **student_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating student")

# An API to find a list of students with optional filters
@app.get("/students", response_model=List[StudentInDB], status_code=status.HTTP_200_OK)
async def list_students(country: Optional[str] = Query(None), age: Optional[int] = Query(None)):
    try:
        query = {}
        if country:
            query["address.country"] = country
        if age:
            query["age"] = {"$gte": age}
        students = await students_collection.find(query).to_list(length=None)
        return [{"id": str(student["_id"]), **student} for student in students]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error listing students")

# get student data according to id provided
@app.get("/students/{id}", response_model=StudentInDB)
async def fetch_student(id: str = Path(...)):
    try:
        student = await students_collection.find_one({"_id": ObjectId(id)})
        if student:
            return {"id": str(student["_id"]), **student}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching student")

# update student data according to id provided
@app.patch("/students/{id}", response_model=StudentInDB)
async def update_student(id: str, student: Student):
    try:
        updated_student = await students_collection.find_one_and_update({"_id": ObjectId(id)}, {"$set": student.dict()}, return_document=True)
        if updated_student:
            return {"id": str(updated_student["_id"]), **updated_student}
        else:
            raise HTTPException(status_code=404, detail="Student not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating student")

# delete student data according to id provided
@app.delete("/students/{id}", status_code=status.HTTP_200_OK)
async def delete_student(id: str):
    try:
        result = await students_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return {"message": "Student deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting student")
