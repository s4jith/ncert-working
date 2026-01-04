"""
Database initialization script for MongoDB collections.
Run this to create collections and indexes for dashboard features.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_database():
    """
    Initialize MongoDB database with required collections and indexes.
    
    Collections created:
    1. users - User profiles with streak data
    2. user_activities - Daily activity logs for streak tracking
    3. notes - Student notes (already exists)
    4. evaluations - Test/assessment results (already exists)
    """
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client.ncert_learning
        
        logger.info("🔌 Connected to MongoDB Atlas")
        
        # ==================== USERS COLLECTION ====================
        logger.info("📋 Creating 'users' collection...")
        
        users_col = db["users"]
        
        # Create indexes for users
        await users_col.create_index("student_id", unique=True)
        await users_col.create_index("email")
        
        logger.info("✅ Created indexes for 'users' collection")
        logger.info("   - student_id (unique)")
        logger.info("   - email")
        
        # ==================== USER ACTIVITIES COLLECTION ====================
        logger.info("📋 Creating 'user_activities' collection...")
        
        activities_col = db["user_activities"]
        
        # Create compound index for activities (student_id + date)
        await activities_col.create_index([("student_id", 1), ("date", -1)])
        await activities_col.create_index("date")
        
        logger.info("✅ Created indexes for 'user_activities' collection")
        logger.info("   - student_id + date (compound)")
        logger.info("   - date")
        
        # ==================== NOTES COLLECTION (enhance existing) ====================
        logger.info("📋 Enhancing 'notes' collection...")
        
        notes_col = db["notes"]
        
        # Create indexes for notes
        await notes_col.create_index("student_id")
        await notes_col.create_index([("student_id", 1), ("subject", 1)])
        await notes_col.create_index([("student_id", 1), ("created_at", -1)])
        
        logger.info("✅ Created indexes for 'notes' collection")
        logger.info("   - student_id")
        logger.info("   - student_id + subject")
        logger.info("   - student_id + created_at (for recent notes)")
        
        # ==================== EVALUATIONS COLLECTION (enhance existing) ====================
        logger.info("📋 Enhancing 'evaluations' collection...")
        
        eval_col = db["evaluations"]
        
        # Create indexes for evaluations
        await eval_col.create_index("student_id")
        await eval_col.create_index([("student_id", 1), ("subject", 1)])
        await eval_col.create_index([("student_id", 1), ("created_at", -1)])
        
        logger.info("✅ Created indexes for 'evaluations' collection")
        logger.info("   - student_id")
        logger.info("   - student_id + subject")
        logger.info("   - student_id + created_at")
        
        # ==================== VERIFY COLLECTIONS ====================
        collections = await db.list_collection_names()
        logger.info(f"\n📊 Database Collections ({len(collections)}):")
        for col in sorted(collections):
            count = await db[col].count_documents({})
            logger.info(f"   - {col}: {count} documents")
        
        logger.info("\n✅ Database initialization complete!")
        logger.info("\nCollections ready:")
        logger.info("  ✓ users - User profiles and streak data")
        logger.info("  ✓ user_activities - Daily activity logs")
        logger.info("  ✓ notes - Student notes")
        logger.info("  ✓ evaluations - Test results")
        
        # Close connection
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def seed_sample_data():
    """
    Seed sample data for testing (optional).
    """
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client.ncert_learning
        
        logger.info("\n🌱 Seeding sample data...")
        
        # Sample user
        users_col = db["users"]
        sample_user = {
            "student_id": "test_user_001",
            "name": "Test Student",
            "email": "test@example.com",
            "class_level": 6,
            "preferred_subject": "Mathematics",
            "longest_streak": 5,
            "created_at": "2024-12-01"
        }
        
        await users_col.update_one(
            {"student_id": "test_user_001"},
            {"$set": sample_user},
            upsert=True
        )
        logger.info("✅ Created sample user: test_user_001")
        
        # Sample activities (last 7 days)
        from datetime import datetime, timedelta
        activities_col = db["user_activities"]
        
        today = datetime.utcnow()
        for i in range(7):
            date = today - timedelta(days=i)
            activity = {
                "student_id": "test_user_001",
                "date": date.strftime("%Y-%m-%d"),
                "hours": 1.5 + (i * 0.5) % 2,
                "last_updated": date
            }
            await activities_col.update_one(
                {"student_id": "test_user_001", "date": activity["date"]},
                {"$set": activity},
                upsert=True
            )
        
        logger.info("✅ Created 7 days of sample activities")
        
        client.close()
        logger.info("\n✅ Sample data seeded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Sample data seeding failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MongoDB Database Initialization")
    print("=" * 60)
    print()
    
    # Initialize database
    asyncio.run(initialize_database())
    
    # Ask if user wants to seed sample data
    print("\n" + "=" * 60)
    response = input("\n🌱 Do you want to seed sample data for testing? (y/n): ")
    
    if response.lower() in ["y", "yes"]:
        asyncio.run(seed_sample_data())
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
