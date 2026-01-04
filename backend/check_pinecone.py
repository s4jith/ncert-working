"""Check Pinecone metadata"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from pinecone import Pinecone

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(name=settings.PINECONE_MASTER_INDEX, host=settings.PINECONE_MASTER_HOST)

# Get stats
stats = index.describe_index_stats()
namespaces = stats.get('namespaces', {})
print(f'\n📊 Pinecone Stats:')
print(f'Total vectors: {stats.get("total_vector_count", 0)}')
print(f'Namespaces: {list(namespaces.keys())}')

# Query each namespace
for ns_name, ns_info in namespaces.items():
    print(f'\n📁 Namespace: {ns_name} ({ns_info.get("vector_count", 0)} vectors)')
    
    # Query to get sample metadata
    result = index.query(namespace=ns_name, vector=[0.0]*768, top_k=5, include_metadata=True)
    
    print('Sample metadata:')
    for match in result.get('matches', [])[:3]:
        vec_id = match.get('id', 'N/A')
        metadata = match.get('metadata', {})
        print(f'  ID: {vec_id}')
        print(f'  class_level: {metadata.get("class_level", "NOT FOUND")}')
        print(f'  chapter_number: {metadata.get("chapter_number", "NOT FOUND")}')
        print(f'  subject: {metadata.get("subject", "NOT FOUND")}')
        print(f'  All keys: {list(metadata.keys())}')
        print()
