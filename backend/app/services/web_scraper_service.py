"""
Web Scraper Service
Automatically scrapes educational content to enrich student learning.
"""

from sentence_transformers import SentenceTransformer
from app.db.mongo import pinecone_web_db
import logging
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

# Note: These packages need to be installed
# pip install googlesearch-python requests beautifulsoup4 lxml

try:
    from googlesearch import search
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_ENABLED = True
except ImportError:
    SCRAPING_ENABLED = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("⚠️ Web scraping dependencies not installed")
    logger_temp.warning("Install: pip install googlesearch-python requests beautifulsoup4 lxml")

logger = logging.getLogger(__name__)


class WebScraperService:
    """
    Service for scraping educational content from trusted sources.
    Enriches student answers with web-based explanations and examples.
    """
    
    def __init__(self):
        """Initialize web scraper with embedding model."""
        self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.enabled = SCRAPING_ENABLED
        
        # Trusted educational sources
        self.trusted_sources = [
            "khanacademy.org",
            "en.wikipedia.org",
            "mathsisfun.com",
            "britannica.com",
            "byjus.com",
            "toppr.com",
            "teachoo.com",
            "cuemath.com",
            "vedantu.com"
        ]
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Cache to avoid re-scraping
        self.scraped_topics = set()
        
        if self.enabled:
            logger.info("✅ Web Scraper Service initialized")
        else:
            logger.warning("⚠️ Web Scraper Service disabled (missing dependencies)")
    
    def scrape_topic(
        self,
        subject: str,
        topic: str,
        class_level: int,
        max_sources: int = 3
    ) -> bool:
        """
        Scrape web content for a specific topic.
        
        Args:
            subject: Subject name (Mathematics, Physics, etc.)
            topic: Specific topic to search for
            class_level: Student's class level
            max_sources: Maximum number of sources to scrape
        
        Returns:
            True if content was scraped and stored successfully
        """
        if not self.enabled:
            logger.debug("Web scraping disabled - skipping")
            return False
        
        try:
            # Check cache
            cache_key = f"{subject}_{topic}_{class_level}"
            if cache_key in self.scraped_topics:
                logger.debug(f"Topic already scraped: {cache_key}")
                return True
            
            # Build search query
            search_query = f"{subject} {topic} for class {class_level} NCERT explained"
            logger.info(f"🌐 Scraping web content for: {search_query}")
            
            # Search Google
            urls = self._search_google(search_query, max_sources)
            
            if not urls:
                logger.warning(f"No search results found for: {topic}")
                return False
            
            # Scrape and store content from each URL
            stored_count = 0
            for url in urls:
                if self._scrape_and_store(url, subject, topic, class_level):
                    stored_count += 1
            
            # Add to cache
            if stored_count > 0:
                self.scraped_topics.add(cache_key)
                logger.info(f"✅ Scraped and stored content from {stored_count} sources")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to scrape topic '{topic}': {e}")
            return False
    
    def _search_google(self, query: str, max_results: int) -> List[str]:
        """
        Search Google and return URLs from trusted sources.
        
        Args:
            query: Search query
            max_results: Maximum number of URLs to return
        
        Returns:
            List of URLs from trusted sources
        """
        try:
            urls = []
            
            # Search Google
            for url in search(query, num_results=max_results * 3, sleep_interval=1):
                # Check if URL is from trusted source
                if any(source in url for source in self.trusted_sources):
                    urls.append(url)
                    
                    if len(urls) >= max_results:
                        break
            
            logger.debug(f"Found {len(urls)} URLs from trusted sources")
            return urls
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    def _scrape_and_store(
        self,
        url: str,
        subject: str,
        topic: str,
        class_level: int
    ) -> bool:
        """
        Scrape content from a URL and store in Pinecone.
        
        Args:
            url: URL to scrape
            subject: Subject name
            topic: Topic name
            class_level: Student's class level
        
        Returns:
            True if content was scraped and stored successfully
        """
        try:
            # Fetch page content
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else topic
            
            # Remove script and style tags
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Clean text
            text_content = self._clean_text(text_content)
            
            # Check relevance
            if not self._is_content_relevant(text_content, topic):
                logger.debug(f"Content not relevant: {url}")
                return False
            
            # Chunk content
            chunks = self._chunk_content(text_content, chunk_size=500, overlap=50)
            
            if not chunks:
                logger.debug(f"No content extracted from: {url}")
                return False
            
            # Store chunks in Pinecone
            stored = self._store_chunks(
                chunks=chunks,
                url=url,
                title=title_text,
                subject=subject,
                topic=topic,
                class_level=class_level
            )
            
            if stored:
                logger.info(f"✅ Stored {len(chunks)} chunks from: {url[:50]}...")
            
            return stored
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?()\-\'\"]+', '', text)
        
        # Remove very short lines
        lines = text.split('\n')
        lines = [line for line in lines if len(line.strip()) > 20]
        
        return '\n'.join(lines).strip()
    
    def _is_content_relevant(self, content: str, topic: str) -> bool:
        """
        Check if scraped content is relevant to the topic.
        
        Args:
            content: Extracted text content
            topic: Topic name
        
        Returns:
            True if content is relevant
        """
        if not content or len(content) < 200:
            return False
        
        content_lower = content.lower()
        topic_lower = topic.lower()
        
        # Check if topic keywords appear
        topic_words = topic_lower.split()
        matches = sum(1 for word in topic_words if word in content_lower)
        
        # Require at least 50% of topic words to appear
        return matches >= len(topic_words) * 0.5
    
    def _chunk_content(
        self,
        content: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Split content into overlapping chunks.
        
        Args:
            content: Text content to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n')
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Keep last part for overlap
                words = current_chunk.split()
                overlap_words = words[-overlap:] if len(words) > overlap else words
                current_chunk = ' '.join(overlap_words) + ' '
            
            current_chunk += para + ' '
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Filter out very short chunks
        chunks = [c for c in chunks if len(c) > 100]
        
        return chunks
    
    def _store_chunks(
        self,
        chunks: List[str],
        url: str,
        title: str,
        subject: str,
        topic: str,
        class_level: int
    ) -> bool:
        """
        Store chunks in Pinecone web content index.
        
        Args:
            chunks: List of text chunks
            url: Source URL
            title: Page title
            subject: Subject name
            topic: Topic name
            class_level: Student's class level
        
        Returns:
            True if stored successfully
        """
        try:
            vectors = []
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embedding_model.encode(chunk).tolist()
                
                # Create unique ID
                url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
                vector_id = f"web_{subject.lower()}_{topic.lower()}_{url_hash}_chunk{i}"
                
                # Create metadata
                metadata = {
                    "text": chunk[:1000],  # Limit length
                    "subject": subject,
                    "topic": topic.lower(),
                    "class": str(class_level),
                    "source_url": url[:500],
                    "title": title[:200],
                    "scrape_date": datetime.now().isoformat(),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                
                vectors.append((vector_id, embedding, metadata))
            
            # Upsert to Pinecone (namespace = subject)
            pinecone_web_db.index.upsert(
                vectors=vectors,
                namespace=subject.lower()
            )
            
            logger.debug(f"Stored {len(vectors)} vectors in {subject} namespace")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store chunks: {e}")
            return False
    
    def should_scrape(
        self,
        existing_chunks: int,
        threshold: int = 5
    ) -> bool:
        """
        Determine if web scraping should be triggered.
        
        Args:
            existing_chunks: Number of chunks retrieved from textbook
            threshold: Minimum chunks needed to skip scraping
        
        Returns:
            True if scraping should be triggered
        """
        return existing_chunks < threshold and self.enabled
    
    def get_scraping_stats(self) -> Dict:
        """
        Get web scraping statistics.
        
        Returns:
            Dictionary with scraping stats
        """
        return {
            "enabled": self.enabled,
            "cached_topics": len(self.scraped_topics),
            "trusted_sources": len(self.trusted_sources)
        }


# Global instance
web_scraper_service = WebScraperService()
