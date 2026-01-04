"""
Script to set up namespace-based subject-wise architecture in Pinecone.

This script:
1. Creates ONE master index: ncert-all-subjects
2. Uses namespaces for each subject (mathematics, physics, chemistry, etc.)
3. Provides better performance and stays within free tier limits

Namespaces:
- mathematics (Classes 5-12)
- physics (Classes 9-12)
- chemistry (Classes 9-12)
- biology (Classes 9-12)
- social-science (Classes 5-10)
- english (Classes 5-12)
- hindi (Classes 5-12)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MASTER_INDEX_NAME = "ncert-all-subjects"

SUBJECT_NAMESPACES = {
    "mathematics": {"classes": "5-12", "description": "Mathematics content"},
    "physics": {"classes": "9-12", "description": "Physics content"},
    "chemistry": {"classes": "9-12", "description": "Chemistry content"},
    "biology": {"classes": "9-12", "description": "Biology content"},
    "social-science": {"classes": "5-10", "description": "Social Science content"},
    "english": {"classes": "5-12", "description": "English content"},
    "hindi": {"classes": "5-12", "description": "Hindi content"}
}


def setup_namespace_architecture():
    """Set up namespace-based subject architecture."""
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        logger.info("="*70)
        logger.info("🚀 Setting Up Namespace-Based Subject Architecture")
        logger.info("="*70)
        
        # Check existing indexes
        existing_indexes = [index.name for index in pc.list_indexes()]
        logger.info(f"\n📋 Current indexes: {len(existing_indexes)}")
        for idx in existing_indexes:
            logger.info(f"   - {idx}")
        
        # Check if master index exists
        if MASTER_INDEX_NAME in existing_indexes:
            logger.info(f"\n✅ Master index '{MASTER_INDEX_NAME}' already exists")
            index = pc.Index(MASTER_INDEX_NAME)
        else:
            logger.info(f"\n📦 Creating master index: {MASTER_INDEX_NAME}")
            
            # Check if we need to delete an old index
            if len(existing_indexes) >= 5:
                logger.warning(f"\n⚠️  Reached index limit (5). Consider deleting unused indexes:")
                logger.warning("   - ncert-learning-rag (OLD chapter-based)")
                logger.warning("   - intel-working (if not needed)")
                logger.warning("\nRun: python scripts/cleanup_old_indexes.py")
                return
            
            # Create master index
            pc.create_index(
                name=MASTER_INDEX_NAME,
                dimension=768,  # Gemini text-embedding-004
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info("✅ Master index created!")
            
            # Wait for index to be ready
            logger.info("⏳ Waiting for index to initialize...")
            time.sleep(15)
            
            index = pc.Index(MASTER_INDEX_NAME)
        
        # Display namespace information
        logger.info(f"\n{'='*70}")
        logger.info("📚 Subject Namespaces Configuration")
        logger.info(f"{'='*70}")
        
        for namespace, config in SUBJECT_NAMESPACES.items():
            logger.info(f"\n   Namespace: {namespace}")
            logger.info(f"   Classes: {config['classes']}")
            logger.info(f"   Description: {config['description']}")
        
        # Check index stats
        logger.info(f"\n{'='*70}")
        logger.info("📊 Index Status")
        logger.info(f"{'='*70}")
        
        stats = index.describe_index_stats()
        logger.info(f"\nIndex: {MASTER_INDEX_NAME}")
        logger.info(f"Total vectors: {stats.get('total_vector_count', 0)}")
        logger.info(f"Dimension: 768")
        logger.info(f"Metric: cosine")
        
        # Show namespace stats
        namespaces = stats.get('namespaces', {})
        if namespaces:
            logger.info(f"\nExisting namespaces: {len(namespaces)}")
            for ns_name, ns_stats in namespaces.items():
                logger.info(f"   - {ns_name}: {ns_stats.get('vector_count', 0)} vectors")
        else:
            logger.info("\nNo vectors uploaded yet. Namespaces will be created when data is uploaded.")
        
        # Success summary
        logger.info(f"\n{'='*70}")
        logger.info("✅ Setup Complete!")
        logger.info(f"{'='*70}")
        logger.info(f"\n📝 Architecture:")
        logger.info(f"   Index: {MASTER_INDEX_NAME}")
        logger.info(f"   Namespaces: {len(SUBJECT_NAMESPACES)} subjects")
        logger.info(f"   Approach: One index + namespaces (optimal!)")
        
        logger.info(f"\n🎯 Next Steps:")
        logger.info("   1. Run data migration script to populate namespaces")
        logger.info("   2. Update backend to use namespace queries")
        logger.info("   3. Test cross-class learning")
        
        logger.info(f"\n💡 Benefits:")
        logger.info("   ✅ Stays within free tier (5 index limit)")
        logger.info("   ✅ Faster queries (single connection)")
        logger.info("   ✅ Easier management")
        logger.info("   ✅ Unlimited namespaces")
        logger.info("   ✅ Better for progressive learning")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    logger.info("Starting namespace-based setup...\n")
    setup_namespace_architecture()
