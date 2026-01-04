"""
Database connections for MongoDB Atlas and Pinecone Vector Database.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


# ==================== MONGODB ATLAS ====================

class MongoDB:
    """MongoDB Atlas connection manager."""
    
    def __init__(self):
        self.client = None  # AsyncIOMotorClient instance
        self.db = None
    
    async def connect(self):
        """Initialize MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client.ncert_learning
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB Atlas successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database."""
        return self.db[collection_name]


# Global MongoDB instance (Async)
mongodb = MongoDB()


# ==================== SYNCHRONOUS MONGODB (for auth.py and admin) ====================

class SyncMongoDB:
    """
    Synchronous MongoDB client for routes that need blocking operations.
    Used by auth.py and admin_dashboard.py for user management.
    """
    
    def __init__(self):
        self._client = None
        self._db = None
    
    @property
    def client(self):
        """Lazy initialization of MongoDB client."""
        if self._client is None:
            self._client = MongoClient(settings.MONGO_URI)
            self._db = self._client.ncert_learning_db
            logger.info("Sync MongoDB client initialized")
        return self._client
    
    @property
    def db(self):
        """Get the database instance."""
        if self._db is None:
            self.client  # Initialize client
        return self._db
    
    @property
    def users(self):
        """Get users collection."""
        return self.db.users
    
    @property
    def support_tickets(self):
        """Get support tickets collection."""
        return self.db.support_tickets
    
    @property
    def student_counters(self):
        """Get student counters collection for ID generation."""
        return self.db.student_counters
    
    @property
    def tests(self):
        """Get tests collection for test management."""
        return self.db.tests
    
    @property
    def test_submissions(self):
        """Get test submissions collection."""
        return self.db.test_submissions
    
    @property
    def notifications(self):
        """Get notifications collection."""
        return self.db.notifications
    
    @property
    def books(self):
        """Get books collection for book management."""
        return self.db.books
    
    @property
    def book_chapters(self):
        """Get book chapters collection."""
        return self.db.book_chapters
    
    def get_collection(self, name: str):
        """Get a collection by name."""
        return self.db[name]
    
    def close(self):
        """Close the connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Sync MongoDB client closed")


# Global Sync MongoDB instance
db = SyncMongoDB()


# ==================== PINECONE VECTOR DATABASE ====================

class PineconeDB:
    """Pinecone Vector Database connection manager."""
    
    def __init__(self):
        self.pc = None
        self.index = None
    
    def connect(self):
        """Initialize Pinecone connection."""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Connect to existing index
            self.index = self.pc.Index(
                name=settings.PINECONE_INDEX,
                host=settings.PINECONE_HOST
            )
            
            # Test connection by getting index stats
            stats = self.index.describe_index_stats()
            logger.info(f"Connected to Pinecone successfully")
            logger.info(f"Index: {settings.PINECONE_INDEX}")
            logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            logger.warning("Pinecone connection failed - RAG features will not work")
            logger.warning("Please check PINECONE_HOST in .env file")
            logger.warning("Get correct host from: https://app.pinecone.io/")
            # Don't raise - allow server to start without Pinecone
    
    def query(self, vector: list[float], top_k: int = 5, filter: dict = None):
        """
        Query Pinecone index with a vector.
        
        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter (e.g., {"class": 6, "subject": "Geography"})
        
        Returns:
            Query results from Pinecone
        """
        try:
            # Check if index is connected, reconnect if needed
            if not self.index:
                logger.warning("Pinecone index not connected, attempting to reconnect...")
                self.connect()
                if not self.index:
                    raise Exception("Failed to reconnect to Pinecone")
            
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
            return results
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            # Try to reconnect once
            try:
                logger.info("Attempting to reconnect to Pinecone...")
                self.connect()
                if self.index:
                    results = self.index.query(
                        vector=vector,
                        top_k=top_k,
                        filter=filter,
                        include_metadata=True
                    )
                    logger.info("Reconnection successful, query completed")
                    return results
            except Exception as reconnect_error:
                logger.error(f"Reconnection failed: {reconnect_error}")
            raise
    
    def upsert(self, vectors: list[tuple]):
        """
        Upsert vectors into Pinecone index.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
        """
        try:
            self.index.upsert(vectors=vectors)
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            raise


# Global Pinecone instance (textbook content)
pinecone_db = PineconeDB()


# ==================== PINECONE WEB CONTENT DATABASE ====================

class PineconeWebDB:
    """Pinecone Vector Database for web-scraped content (DeepDive mode)."""
    
    def __init__(self):
        self.pc = None
        self.index = None
    
    def connect(self):
        """Initialize Pinecone web content connection."""
        try:
            # Initialize Pinecone (reuse same API key)
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Connect to web content index
            self.index = self.pc.Index(
                name=settings.PINECONE_WEB_INDEX,
                host=settings.PINECONE_WEB_HOST
            )
            
            # Test connection
            stats = self.index.describe_index_stats()
            logger.info(f"Connected to Pinecone Web Content DB successfully")
            logger.info(f"Index: {settings.PINECONE_WEB_INDEX}")
            logger.info(f"Total web vectors: {stats.get('total_vector_count', 0)}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone Web DB: {e}")
            logger.warning("Web content DB connection failed - DeepDive mode will use textbook only")
            # Don't raise - allow server to start without web content DB
    
    def query(self, vector: list[float], top_k: int = 5, filter: dict = None):
        """
        Query Pinecone web content index with a vector.
        
        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter
        
        Returns:
            Query results from Pinecone
        """
        try:
            # Check if index is connected, reconnect if needed
            if not self.index:
                logger.warning("Pinecone web index not connected, attempting to reconnect...")
                self.connect()
                if not self.index:
                    raise Exception("Failed to reconnect to Pinecone Web DB")
            
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
            return results
        except Exception as e:
            logger.error(f"Pinecone web query failed: {e}")
            # Try to reconnect once
            try:
                logger.info("Attempting to reconnect to Pinecone Web DB...")
                self.connect()
                if self.index:
                    results = self.index.query(
                        vector=vector,
                        top_k=top_k,
                        filter=filter,
                        include_metadata=True
                    )
                    logger.info("Web DB reconnection successful, query completed")
                    return results
            except Exception as reconnect_error:
                logger.error(f"Web DB reconnection failed: {reconnect_error}")
            raise
    
    def upsert(self, vectors: list[tuple]):
        """
        Upsert vectors into Pinecone web content index.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
        """
        try:
            self.index.upsert(vectors=vectors)
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone Web Content DB")
        except Exception as e:
            logger.error(f"Pinecone web content upsert failed: {e}")
            raise


# Global Pinecone Web Content instance
pinecone_web_db = PineconeWebDB()


# ==================== PINECONE LLM CONTENT DATABASE ====================

class PineconeLLMDB:
    """Pinecone Vector Database for storing LLM-generated answers."""
    
    def __init__(self):
        self.pc = None
        self.index = None
    
    def connect(self):
        """Initialize Pinecone LLM content connection."""
        try:
            # Initialize Pinecone (reuse same API key)
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if LLM index exists, if not we'll note it in logs
            if settings.PINECONE_LLM_HOST:
                # Connect to LLM content index
                self.index = self.pc.Index(
                    name=settings.PINECONE_LLM_INDEX,
                    host=settings.PINECONE_LLM_HOST
                )
                
                # Test connection
                stats = self.index.describe_index_stats()
                logger.info(f"✅ Connected to Pinecone LLM Content DB successfully")
                logger.info(f"Index: {settings.PINECONE_LLM_INDEX}")
                logger.info(f"Total LLM vectors: {stats.get('total_vector_count', 0)}")
            else:
                logger.warning("⚠️ PINECONE_LLM_HOST not configured - LLM storage disabled")
                logger.warning("To enable: Create 'ncert-llm' index (768 dim) and add PINECONE_LLM_HOST to .env")
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone LLM DB: {e}")
            logger.warning("LLM content DB connection failed - LLM storage will be disabled")
            # Don't raise - allow server to start without LLM DB
    
    def store_llm_response(
        self,
        vector_id: str,
        question: str,
        answer: str,
        subject: str,
        topic: str,
        class_level: int,
        embedding: list[float],
        quality_score: float = 0.9
    ):
        """
        Store LLM-generated answer with metadata.
        
        Args:
            vector_id: Unique identifier for the vector
            question: Student's question
            answer: LLM-generated answer
            subject: Subject name (Mathematics, Physics, etc.)
            topic: Specific topic (algebra, trigonometry, etc.)
            class_level: Student's class (6, 7, 8, etc.)
            embedding: Question embedding vector (768 dimensions)
            quality_score: Answer quality score (0-1)
        """
        try:
            if not self.index:
                logger.warning("LLM DB not connected - skipping storage")
                return False
            
            from datetime import datetime
            
            metadata = {
                "question": question[:1000],  # Limit length
                "answer": answer[:2000],  # Limit length
                "subject": subject,
                "topic": topic.lower(),
                "class": str(class_level),
                "quality_score": quality_score,
                "created_date": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            # Upsert to Pinecone (namespace = subject)
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)],
                namespace=subject.lower()
            )
            
            logger.info(f"✅ Stored LLM answer: {vector_id} in {subject} namespace")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store LLM response: {e}")
            return False
    
    def query(self, vector: list[float], subject: str, top_k: int = 3, filter: dict = None):
        """
        Query Pinecone LLM content index with a vector.
        
        Args:
            vector: Query embedding vector
            subject: Subject namespace to query
            top_k: Number of results to return
            filter: Additional metadata filter
        
        Returns:
            Query results from Pinecone
        """
        try:
            if not self.index:
                logger.debug("LLM DB not connected - returning empty results")
                return {"matches": []}
            
            results = self.index.query(
                namespace=subject.lower(),
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
            return results
            
        except Exception as e:
            logger.error(f"Pinecone LLM query failed: {e}")
            return {"matches": []}
    
    def increment_usage(self, vector_id: str, subject: str):
        """Increment usage counter for a stored answer."""
        try:
            if not self.index:
                return
            
            # Fetch current metadata
            fetch_result = self.index.fetch(ids=[vector_id], namespace=subject.lower())
            if vector_id in fetch_result.get('vectors', {}):
                vector_data = fetch_result['vectors'][vector_id]
                metadata = vector_data.get('metadata', {})
                
                # Increment usage count
                metadata['usage_count'] = metadata.get('usage_count', 0) + 1
                
                # Update vector
                self.index.upsert(
                    vectors=[(vector_id, vector_data['values'], metadata)],
                    namespace=subject.lower()
                )
                
                logger.debug(f"Incremented usage count for {vector_id}")
                
        except Exception as e:
            logger.error(f"Failed to increment usage count: {e}")


# Global Pinecone LLM Content instance
pinecone_llm_db = PineconeLLMDB()


# ==================== SUBJECT-WISE PINECONE DATABASES (NEW ARCHITECTURE) ====================

class SubjectWisePineconeDB:
    """
    Subject-wise Pinecone database manager for progressive learning.
    Supports cross-class queries and prerequisite-based retrieval.
    """
    
    def __init__(self):
        self.pc = None
        self.indexes = {}
        self.subject_config = {
            "Mathematics": {
                "index_name": settings.PINECONE_MATH_INDEX,
                "host": settings.PINECONE_MATH_HOST,
                "classes": ["5", "6", "7", "8", "9", "10", "11", "12"]
            },
            "Physics": {
                "index_name": settings.PINECONE_PHYSICS_INDEX,
                "host": settings.PINECONE_PHYSICS_HOST,
                "classes": ["9", "10", "11", "12"]
            },
            "Chemistry": {
                "index_name": settings.PINECONE_CHEMISTRY_INDEX,
                "host": settings.PINECONE_CHEMISTRY_HOST,
                "classes": ["9", "10", "11", "12"]
            },
            "Biology": {
                "index_name": settings.PINECONE_BIOLOGY_INDEX,
                "host": settings.PINECONE_BIOLOGY_HOST,
                "classes": ["9", "10", "11", "12"]
            },
            "Social Science": {
                "index_name": settings.PINECONE_SOCIAL_INDEX,
                "host": settings.PINECONE_SOCIAL_HOST,
                "classes": ["5", "6", "7", "8", "9", "10"]
            },
            "English": {
                "index_name": settings.PINECONE_ENGLISH_INDEX,
                "host": settings.PINECONE_ENGLISH_HOST,
                "classes": ["5", "6", "7", "8", "9", "10", "11", "12"]
            },
            "Hindi": {
                "index_name": settings.PINECONE_HINDI_INDEX,
                "host": settings.PINECONE_HINDI_HOST,
                "classes": ["5", "6", "7", "8", "9", "10", "11", "12"]
            }
        }
    
    def connect(self):
        """Initialize all subject-wise Pinecone connections."""
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Connect to each subject index
            for subject, config in self.subject_config.items():
                try:
                    index = self.pc.Index(
                        name=config["index_name"],
                        host=config["host"]
                    )
                    
                    # Test connection
                    stats = index.describe_index_stats()
                    self.indexes[subject] = index
                    
                    logger.info(f"✅ Connected to {subject} index")
                    logger.info(f"   Classes: {', '.join(config['classes'])}")
                    logger.info(f"   Vectors: {stats.get('total_vector_count', 0)}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to connect to {subject} index: {e}")
                    self.indexes[subject] = None
            
            logger.info(f"📚 Subject-wise DB: {len([i for i in self.indexes.values() if i])} subjects connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize subject-wise Pinecone: {e}")
    
    def get_index(self, subject: str):
        """
        Get Pinecone index for a specific subject.
        
        Args:
            subject: Subject name (e.g., "Mathematics", "Physics")
        
        Returns:
            Pinecone index or None if not connected
        """
        return self.indexes.get(subject)
    
    def query_subject(
        self,
        subject: str,
        vector: list[float],
        class_filter: list[str] = None,
        top_k: int = 10,
        additional_filters: dict = None
    ):
        """
        Query a subject-specific index with optional class filtering.
        
        Args:
            subject: Subject name
            vector: Query embedding vector
            class_filter: List of class levels to search (e.g., ["9", "10", "11"])
            top_k: Number of results to return
            additional_filters: Additional metadata filters
        
        Returns:
            Query results from Pinecone
        """
        index = self.get_index(subject)
        if not index:
            logger.error(f"Index for {subject} not available")
            return {"matches": []}
        
        try:
            # Build metadata filter
            filter_dict = {}
            
            if class_filter:
                filter_dict["class"] = {"$in": class_filter}
            
            if additional_filters:
                filter_dict.update(additional_filters)
            
            # Query with filter
            results = index.query(
                vector=vector,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Query failed for {subject}: {e}")
            return {"matches": []}
    
    def query_progressive(
        self,
        subject: str,
        vector: list[float],
        student_class: str,
        mode: str = "quick",
        top_k: int = 10
    ):
        """
        Progressive learning query: includes current class + prerequisites.
        
        Args:
            subject: Subject name
            vector: Query embedding
            student_class: Student's current class
            mode: Query mode (quick/deepdive)
            top_k: Results per class level
        
        Returns:
            Combined results from multiple class levels
        """
        index = self.get_index(subject)
        if not index:
            return {"matches": [], "progressive_results": {}}
        
        try:
            student_class_int = int(student_class)
            
            # Determine class range based on mode
            if mode == "quick":
                # Quick mode: Current class + immediate previous
                classes_to_search = [
                    student_class,
                    str(max(5, student_class_int - 1))
                ]
            else:  # deepdive mode
                # DeepDive: All prerequisite classes
                available_classes = self.subject_config.get(subject, {}).get("classes", [])
                classes_to_search = [
                    c for c in available_classes 
                    if int(c) <= student_class_int
                ]
            
            logger.info(f"🔍 Progressive query for {subject}: {', '.join(classes_to_search)}")
            
            # Query each class level
            progressive_results = {}
            all_matches = []
            
            for class_level in classes_to_search:
                results = self.query_subject(
                    subject=subject,
                    vector=vector,
                    class_filter=[class_level],
                    top_k=5 if mode == "quick" else 10
                )
                
                matches = results.get("matches", [])
                if matches:
                    progressive_results[class_level] = matches
                    all_matches.extend(matches)
                    logger.info(f"   Class {class_level}: {len(matches)} results")
            
            # Sort all matches by score
            all_matches.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            return {
                "matches": all_matches[:top_k],
                "progressive_results": progressive_results,
                "classes_searched": classes_to_search
            }
            
        except Exception as e:
            logger.error(f"Progressive query failed: {e}")
            return {"matches": [], "progressive_results": {}}
    
    def get_available_subjects(self):
        """Get list of subjects with active connections."""
        return [subject for subject, index in self.indexes.items() if index is not None]
    
    def get_subject_classes(self, subject: str):
        """Get list of available classes for a subject."""
        return self.subject_config.get(subject, {}).get("classes", [])


# Global Subject-Wise Pinecone instance
subject_wise_db = SubjectWisePineconeDB()


# ==================== NAMESPACE-BASED PINECONE DATABASE (PRODUCTION) ====================

class NamespaceDB:
    """
    Namespace-based Pinecone database for progressive multi-class learning.
    Uses one master index with subject-specific namespaces.
    
    Architecture:
    - Master Index: ncert-all-subjects
    - Namespaces: mathematics, physics, chemistry, biology, social-science, english, hindi
    - Each namespace contains content for all relevant classes
    """
    
    def __init__(self):
        self.pc = None
        self.index = None
        
        # Subject to namespace mapping
        self.subject_namespaces = {
            "Mathematics": "mathematics",
            "Physics": "physics",
            "Chemistry": "chemistry",
            "Biology": "biology",
            "Social Science": "social-science",
            "English": "english",
            "Hindi": "hindi"
        }
        
        # Class ranges for each subject
        self.subject_classes = {
            "Mathematics": list(range(5, 13)),  # 5-12
            "Physics": list(range(9, 13)),      # 9-12
            "Chemistry": list(range(9, 13)),    # 9-12
            "Biology": list(range(9, 13)),      # 9-12
            "Social Science": list(range(5, 11)), # 5-10
            "English": list(range(5, 13)),      # 5-12
            "Hindi": list(range(5, 13))         # 5-12
        }
    
    def connect(self):
        """Initialize connection to master Pinecone index."""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Connect to master index
            self.index = self.pc.Index(
                name=settings.PINECONE_MASTER_INDEX,
                host=settings.PINECONE_MASTER_HOST
            )
            
            # Test connection and get stats
            stats = self.index.describe_index_stats()
            
            logger.info("="*60)
            logger.info("📚 Connected to Master Index (Namespace Architecture)")
            logger.info(f"   Index: {settings.PINECONE_MASTER_INDEX}")
            logger.info(f"   Total vectors: {stats.get('total_vector_count', 0)}")
            
            # Show namespace stats
            namespaces = stats.get('namespaces', {})
            if namespaces:
                logger.info(f"   Active namespaces: {len(namespaces)}")
                for ns_name, ns_stats in namespaces.items():
                    logger.info(f"      • {ns_name}: {ns_stats.get('vector_count', 0)} vectors")
            else:
                logger.info("   No data uploaded yet - namespaces will be created on upload")
            
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Failed to connect to master index: {e}")
            logger.warning("Namespace DB connection failed - progressive learning unavailable")
    
    def get_namespace(self, subject: str) -> str:
        """
        Get namespace name for a subject.
        
        Args:
            subject: Subject name (e.g., "Mathematics", "Social Science")
        
        Returns:
            Namespace string (e.g., "mathematics", "social-science")
        """
        return self.subject_namespaces.get(subject, subject.lower().replace(" ", "-"))
    
    def get_prerequisite_classes(self, student_class: int, subject: str, mode: str = "quick") -> list[str]:
        """
        Determine which classes to search based on student's class and mode.
        
        Args:
            student_class: Student's current class (5-12)
            subject: Subject name
            mode: Query mode ("quick" or "deepdive")
        
        Returns:
            List of class strings to search
        """
        available_classes = self.subject_classes.get(subject, [])
        
        if mode == "quick":
            # Quick mode: Current class + immediate previous
            classes = [student_class]
            if student_class > min(available_classes):
                classes.append(student_class - 1)
        else:  # deepdive mode
            # DeepDive: All classes up to current
            classes = [c for c in available_classes if c <= student_class]
        
        return [str(c) for c in classes]
    
    def query(
        self,
        vector: list[float],
        subject: str,
        class_filter: list[str] = None,
        top_k: int = 10,
        additional_filters: dict = None
    ):
        """
        Query subject namespace with optional class filtering.
        
        Args:
            vector: Query embedding vector
            subject: Subject name (e.g., "Mathematics", "Physics")
            class_filter: List of class levels to search (e.g., ["9", "10", "11"])
            top_k: Number of results to return
            additional_filters: Additional metadata filters
        
        Returns:
            Query results from Pinecone
        """
        if not self.index:
            logger.error("Namespace DB not connected")
            return {"matches": []}
        
        try:
            namespace = self.get_namespace(subject)
            
            # Build metadata filter
            filter_dict = {}
            
            if class_filter:
                if len(class_filter) == 1:
                    filter_dict["class"] = class_filter[0]
                else:
                    filter_dict["class"] = {"$in": class_filter}
            
            if additional_filters:
                filter_dict.update(additional_filters)
            
            # Query with namespace
            results = self.index.query(
                vector=vector,
                namespace=namespace,
                top_k=top_k,
                filter=filter_dict if filter_dict else None,
                include_metadata=True
            )
            
            logger.info(f"📖 Queried namespace '{namespace}' with classes {class_filter}: {len(results.get('matches', []))} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Namespace query failed for {subject}: {e}")
            # Try to reconnect
            try:
                logger.info("Attempting to reconnect...")
                self.connect()
                if self.index:
                    results = self.index.query(
                        vector=vector,
                        namespace=self.get_namespace(subject),
                        top_k=top_k,
                        filter=filter_dict if filter_dict else None,
                        include_metadata=True
                    )
                    logger.info("Reconnection successful, query completed")
                    return results
            except Exception as reconnect_error:
                logger.error(f"Reconnection failed: {reconnect_error}")
            return {"matches": []}
    
    def query_progressive(
        self,
        vector: list[float],
        subject: str,
        student_class: int,
        mode: str = "quick",
        top_k: int = 10
    ):
        """
        Progressive learning query: retrieves content from multiple class levels.
        
        Args:
            vector: Query embedding
            subject: Subject name
            student_class: Student's current class
            mode: Query mode ("quick" or "deepdive")
            top_k: Total results to return
        
        Returns:
            Dictionary with combined results and progressive breakdown
        """
        if not self.index:
            logger.error("Namespace DB not connected")
            return {"matches": [], "progressive_results": {}, "classes_searched": []}
        
        try:
            # Determine classes to search
            classes_to_search = self.get_prerequisite_classes(student_class, subject, mode)
            
            logger.info(f"🎓 Progressive query for {subject} (Student: Class {student_class}, Mode: {mode})")
            logger.info(f"   Searching classes: {', '.join(classes_to_search)}")
            
            # Query with multi-class filter
            results = self.query(
                vector=vector,
                subject=subject,
                class_filter=classes_to_search,
                top_k=top_k
            )
            
            # Organize results by class for progressive explanation
            progressive_results = {}
            for match in results.get("matches", []):
                class_level = match.get("metadata", {}).get("class", "unknown")
                if class_level not in progressive_results:
                    progressive_results[class_level] = []
                progressive_results[class_level].append(match)
            
            logger.info(f"   Found content from {len(progressive_results)} class levels")
            for class_level in sorted(progressive_results.keys()):
                logger.info(f"      Class {class_level}: {len(progressive_results[class_level])} chunks")
            
            return {
                "matches": results.get("matches", []),
                "progressive_results": progressive_results,
                "classes_searched": classes_to_search
            }
            
        except Exception as e:
            logger.error(f"Progressive query failed: {e}")
            return {"matches": [], "progressive_results": {}, "classes_searched": []}
    
    def upsert(self, vectors: list[tuple], subject: str):
        """
        Upsert vectors into subject namespace.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            subject: Subject name (determines namespace)
        """
        if not self.index:
            logger.error("Namespace DB not connected")
            return
        
        try:
            namespace = self.get_namespace(subject)
            self.index.upsert(vectors=vectors, namespace=namespace)
            logger.info(f"✅ Upserted {len(vectors)} vectors to namespace '{namespace}'")
        except Exception as e:
            logger.error(f"Upsert failed for {subject}: {e}")
            raise
    
    def get_available_subjects(self):
        """Get list of all configured subjects."""
        return list(self.subject_namespaces.keys())
    
    def get_subject_info(self, subject: str):
        """Get information about a subject."""
        return {
            "subject": subject,
            "namespace": self.get_namespace(subject),
            "classes": self.subject_classes.get(subject, [])
        }


# Global Namespace DB instance (PRODUCTION)
namespace_db = NamespaceDB()


# ==================== DATABASE INITIALIZATION ====================

async def init_databases():
    """Initialize all database connections."""
    logger.info("Initializing database connections...")
    
    # Connect to MongoDB
    await mongodb.connect()
    
    # Connect to Legacy Pinecone (textbook content) - will be deprecated
    logger.info("\n⚠️  Legacy DB (will be deprecated):")
    pinecone_db.connect()
    
    # Connect to Pinecone Web Content DB
    pinecone_web_db.connect()
    
    # Connect to Pinecone LLM Content DB (NEW)
    pinecone_llm_db.connect()
    
    # Connect to NEW Namespace-Based DB (PRODUCTION)
    logger.info("\n🚀 Connecting to Production Namespace Architecture:")
    namespace_db.connect()
    
    logger.info("\n✅ All databases initialized successfully")


async def close_databases():
    """Close all database connections."""
    logger.info("Closing database connections...")
    await mongodb.close()
    logger.info("All databases closed")


# ==================== HELPER FUNCTIONS ====================

def get_notes_collection():
    """Get notes collection from MongoDB."""
    return mongodb.get_collection("notes")


def get_evaluations_collection():
    """Get evaluations collection from MongoDB."""
    return mongodb.get_collection("evaluations")


def get_assessments_collection():
    """Get assessments collection from MongoDB."""
    return mongodb.get_collection("assessments")


def get_quiz_results_collection():
    """Get quiz results collection from MongoDB."""
    return mongodb.get_collection("quiz_results")


def get_question_sets_collection():
    """Get question sets collection from MongoDB."""
    return mongodb.get_collection("question_sets")


def get_assessment_attempts_collection():
    """Get assessment attempts collection from MongoDB."""
    return mongodb.get_collection("assessment_attempts")


def get_user_activities_collection():
    """Get user activities collection from MongoDB (for streak tracking)."""
    return mongodb.get_collection("user_activities")


def get_users_collection():
    """Get users collection from MongoDB (for user profiles)."""
    return mongodb.get_collection("users")
