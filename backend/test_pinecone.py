"""Test MongoDB books data"""
from app.db.mongo import db

books = list(db.books.find({}).limit(10))
print(f"Found {len(books)} books in MongoDB")
for book in books:
    print(f"  - {book.get('title')}: class {book.get('class_level')}, chapter {book.get('chapter_number')}")
    print(f"    Subject: {book.get('subject')}")
    print(f"    PDF URL: {book.get('pdf_url')}")
    print(f"    Has embeddings: {book.get('has_embeddings')}")
    print()
