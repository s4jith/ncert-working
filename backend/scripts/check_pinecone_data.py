"""
Check what data exists in Pinecone
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pinecone import Pinecone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("ncert-all-subjects")

def check_data():
    """Check what data exists in Pinecone."""
    
    logger.info("Checking Pinecone data...")
    
    # Get index stats
    stats = index.describe_index_stats()
    logger.info(f"\nIndex Stats: {stats}")
    
    # Try querying mathematics namespace
    try:
        results = index.query(
            namespace="mathematics",
            vector=[0.1] * 768,
            top_k=10,
            include_metadata=True
        )
        
        logger.info(f"\nFound {len(results.matches)} results in 'mathematics' namespace")
        
        if results.matches:
            # Show sample metadata
            sample = results.matches[0].metadata
            logger.info(f"\nSample metadata fields: {sample.keys()}")
            logger.info(f"Sample data:")
            for key, value in sample.items():
                if key != "text":  # Skip long text field
                    logger.info(f"  {key}: {value}")
            
            # Check what classes exist
            classes = set()
            chapters = set()
            for match in results.matches:
                if "class" in match.metadata:
                    classes.add(match.metadata["class"])
                if "chapter" in match.metadata:
                    chapters.add(match.metadata["chapter"])
            
            logger.info(f"\nClasses found: {sorted(classes)}")
            logger.info(f"Chapters found: {sorted(chapters)}")
    
    except Exception as e:
        logger.error(f"Error querying: {e}")

if __name__ == "__main__":
    check_data()
