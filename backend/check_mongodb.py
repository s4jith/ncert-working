"""Check MongoDB book records"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.mongo import db
from app.core.config import settings

# Get all books
books = list(db.books.find({}))
print(f'\n📚 Total books in MongoDB: {len(books)}\n')

if books:
    print('Books found:')
    for book in books[:20]:  # Show first 20
        title = book.get('title', 'N/A')
        subject = book.get('subject', 'N/A')
        class_level = book.get('class_level', 'N/A')
        chapter = book.get('chapter_number', 'N/A')
        embeddings_status = book.get('embeddings_generated', False)
        
        print(f'  • {title}')
        print(f'    Subject: {subject} | Class: {class_level} | Chapter: {chapter}')
        print(f'    Embeddings: {"✓" if embeddings_status else "✗"}')
        print()
else:
    print('❌ No books found in MongoDB!')
    print('⚠️  But you have 49,421 vectors in Pinecone "mathematics" namespace')
    print('This means the data exists in Pinecone but not in MongoDB.')
    print('\nYou need to either:')
    print('1. Re-upload the books through the Book Management page')
    print('2. Create MongoDB records for existing Pinecone data')
