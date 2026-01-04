"""
Initialize Users in MongoDB Atlas
Creates admin and sample student/teacher accounts
"""
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import hashlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# Admin credentials (must match Login.jsx)
ADMIN_EMAIL = "admin1@gmail.com"
ADMIN_PASSWORD = "admin1234"

def hash_password(password: str) -> str:
    """Hash password using SHA-256 (same as auth.py)"""
    return hashlib.sha256(password.encode()).hexdigest()

async def init_users():
    """Initialize users in MongoDB"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    users_collection = db["users"]
    
    print(" Connected to MongoDB Atlas")
    print(f" Database: {settings.MONGODB_DB_NAME}")
    
    # Note: Admin credentials are hardcoded in Login.jsx and auth.py
    print(f"\n Admin Credentials (Hardcoded):")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"   Note: Admin does NOT use database authentication")
    
    # Create sample students
    sample_students = [
        {
            "user_id": "STU0001",
            "name": "Rajesh Kumar",
            "email": "student1@test.com",
            "password": "student123",
            "class_level": 10
        },
        {
            "user_id": "STU0002",
            "name": "Priya Sharma",
            "email": "student2@test.com",
            "password": "student123",
            "class_level": 10
        },
        {
            "user_id": "STU0003",
            "name": "Amit Patel",
            "email": "student3@test.com",
            "password": "student123",
            "class_level": 9
        }
    ]
    
    print("\n Creating sample students...")
    
    for student_data in sample_students:
        existing = await users_collection.find_one({"email": student_data["email"]})
        
        if existing:
            print(f"     Student already exists: {student_data['email']}")
        else:
            password_hash = hash_password(student_data["password"])
            
            student = {
                "user_id": student_data["user_id"],
                "name": student_data["name"],
                "email": student_data["email"],
                "password_hash": password_hash,
                "role": "student",
                "class_level": student_data["class_level"],
                "is_active": True,
                "first_login": True,  # Students need to change password on first login
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(student)
            print(f"    Created: {student_data['name']} ({student_data['email']})")
            print(f"      Default Password: {student_data['password']}")
    
    # Create sample teachers
    sample_teachers = [
        {
            "user_id": "TCH0001",
            "name": "Dr. Ramesh Singh",
            "email": "teacher1@test.com",
            "password": "teacher123"
        },
        {
            "user_id": "TCH0002",
            "name": "Ms. Anita Desai",
            "email": "teacher2@test.com",
            "password": "teacher123"
        }
    ]
    
    print("\n Creating sample teachers...")
    
    for teacher_data in sample_teachers:
        existing = await users_collection.find_one({"email": teacher_data["email"]})
        
        if existing:
            print(f"     Teacher already exists: {teacher_data['email']}")
        else:
            password_hash = hash_password(teacher_data["password"])
            
            teacher = {
                "user_id": teacher_data["user_id"],
                "name": teacher_data["name"],
                "email": teacher_data["email"],
                "password_hash": password_hash,
                "role": "teacher",
                "class_level": None,
                "is_active": True,
                "first_login": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(teacher)
            print(f"    Created: {teacher_data['name']} ({teacher_data['email']})")
            print(f"      Default Password: {teacher_data['password']}")
    
    # Display summary
    total_users = await users_collection.count_documents({})
    print(f"\n Total users in database: {total_users}")
    
    # Create indexes
    try:
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("user_id", unique=True)
        print(" Created indexes on email and user_id fields")
    except Exception as e:
        print(f"ℹ  Indexes may already exist: {e}")
    
    client.close()
    print("\n User initialization complete!")
    print("\n" + "=" * 60)
    print(" LOGIN CREDENTIALS")
    print("=" * 60)
    print(f"Admin (Hardcoded):")
    print(f"   Email:    {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"   Role:     Admin (routes to /admin-dashboard)")
    print()
    print(f"Teachers (From Database):")
    for t in sample_teachers:
        print(f"   {t['email']} /  {t['password']}")
    print(f"   Role:     Teacher (routes to /staff-tests)")
    print()
    print(f"Students (From Database):")
    for s in sample_students:
        print(f"   {s['email']} /  {s['password']}")
    print(f"   Role:     Student (routes to /onboarding)")
    print("=" * 60)

if __name__ == "__main__":
    print(" Initializing Users in MongoDB Atlas...\n")
    asyncio.run(init_users())
