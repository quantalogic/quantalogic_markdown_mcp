"""
Section ID Generator - Human-readable section identifiers.

This module provides a new approach to generating section IDs that are:
- Human-readable and semantic
- Stable across document edits
- Collision-resistant through intelligent resolution
- Better than hash-based IDs for user experience
"""

import re
import unicodedata
from typing import List, Optional, Set
from .safe_editor_types import SectionReference


class SectionIDGenerator:
    """
    Generates human-readable section IDs with intelligent collision resolution.
    
    Features:
    - Converts titles to URL-friendly slugs
    - Handles duplicate titles with smart collision resolution
    - Supports hierarchical context for disambiguation
    - Falls back gracefully for edge cases
    """
    
    def __init__(self):
        """Initialize the section ID generator."""
        self._used_ids: Set[str] = set()
    
    def generate_section_id(self, title: str, level: int, line_start: int, 
                           existing_sections: List[SectionReference]) -> str:
        """
        Generate a human-readable section ID with collision resolution.
        
        Args:
            title: The section heading text
            level: The heading level (1-6)
            line_start: The 0-indexed line number (used as fallback only)
            existing_sections: List of existing sections for collision detection
            
        Returns:
            A unique, human-readable section ID
        """
        # Build set of existing IDs for collision detection
        existing_ids = {section.id for section in existing_sections}
        
        # Step 1: Create base slug from title
        base_slug = self._create_slug(title)
        
        # Step 2: Try base slug first
        if base_slug and base_slug not in existing_ids:
            return base_slug
            
        # Step 3: Smart collision resolution
        return self._resolve_collision(base_slug, title, level, line_start, existing_sections, existing_ids)
    
    def _create_slug(self, title: str) -> str:
        """
        Create URL-friendly slug from title.
        
        Args:
            title: The section title
            
        Returns:
            A clean, URL-friendly slug
        """
        if not title or not title.strip():
            return ""
            
        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', title)
        
        # Convert to lowercase
        slug = slug.lower()
        
        # Replace common punctuation and spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars except word chars, spaces, hyphens
        slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces and multiple hyphens with single hyphen
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Limit length intelligently
        if len(slug) > 50:
            # Try to cut at word boundary
            truncated = slug[:50]
            last_hyphen = truncated.rfind('-')
            if last_hyphen > 20:  # Only use word boundary if it's not too short
                slug = truncated[:last_hyphen]
            else:
                slug = truncated.rstrip('-')
        
        return slug or "section"  # Fallback for empty slugs
    
    def _resolve_collision(self, base_slug: str, title: str, level: int, 
                          line_start: int, existing_sections: List[SectionReference], 
                          existing_ids: Set[str]) -> str:
        """
        Intelligently resolve ID collisions using multiple strategies.
        
        Args:
            base_slug: The base slug that collided
            title: Original section title
            level: Section level
            line_start: Line number (for fallback)
            existing_sections: All existing sections
            existing_ids: Set of existing IDs for fast lookup
            
        Returns:
            A unique section ID
        """
        # Strategy 1: Add hierarchical context if available
        hierarchical_id = self._try_hierarchical_context(base_slug, level, existing_sections, existing_ids)
        if hierarchical_id:
            return hierarchical_id
            
        # Strategy 2: Add semantic suffixes based on title context
        semantic_id = self._try_semantic_suffix(base_slug, title, existing_ids)
        if semantic_id:
            return semantic_id
            
        # Strategy 3: Numeric suffix (traditional approach)
        numeric_id = self._try_numeric_suffix(base_slug, existing_ids)
        if numeric_id:
            return numeric_id
            
        # Strategy 4: Fallback to position-based ID (last resort)
        return self._fallback_id(title, level, line_start)
    
    def _try_hierarchical_context(self, base_slug: str, level: int, 
                                 existing_sections: List[SectionReference], 
                                 existing_ids: Set[str]) -> Optional[str]:
        """
        Try to create unique ID using hierarchical context.
        
        Args:
            base_slug: The base slug
            level: Current section level
            existing_sections: All existing sections
            existing_ids: Set of existing IDs
            
        Returns:
            Unique ID with hierarchical context, or None if not possible
        """
        # Find the most recent parent section (lower level number)
        parent_section = None
        for section in reversed(existing_sections):
            if section.level < level:
                parent_section = section
                break
        
        if parent_section:
            # Create hierarchical ID
            parent_slug = self._extract_base_slug(parent_section.id)
            
            # Handle empty base slugs
            if not base_slug or base_slug == "section":
                candidate = f"{parent_slug}-section"
            else:
                candidate = f"{parent_slug}-{base_slug}"
            
            # Ensure it's not too long
            if len(candidate) <= 60 and candidate not in existing_ids:
                return candidate
        
        return None
    
    def _try_semantic_suffix(self, base_slug: str, title: str, existing_ids: Set[str]) -> Optional[str]:
        """
        Try to add semantic suffixes based on title content.
        
        Args:
            base_slug: The base slug
            title: Original title
            existing_ids: Set of existing IDs
            
        Returns:
            Unique ID with semantic suffix, or None if not possible
        """
        # Extract meaningful words from title that aren't in base slug
        words = re.findall(r'\b\w{3,}\b', title.lower())  # Words with 3+ characters
        
        # Skip common words
        skip_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'will', 'can', 'how', 'what', 'when', 'where', 'why'}
        
        for word in reversed(words):  # Try words from end first (often more specific)
            if word not in skip_words and word not in base_slug:
                candidate = f"{base_slug}-{word}"
                if len(candidate) <= 60 and candidate not in existing_ids:
                    return candidate
        
        return None
    
    def _try_numeric_suffix(self, base_slug: str, existing_ids: Set[str]) -> Optional[str]:
        """
        Try numeric suffixes as fallback.
        
        Args:
            base_slug: The base slug
            existing_ids: Set of existing IDs
            
        Returns:
            Unique ID with numeric suffix, or None if too many attempts
        """
        for counter in range(2, 21):  # Try up to 20 variations
            candidate = f"{base_slug}-{counter}"
            if candidate not in existing_ids:
                return candidate
        
        return None  # Too many collisions, fall back to hash
    
    def _fallback_id(self, title: str, level: int, line_start: int) -> str:
        """
        Generate fallback ID when all else fails.
        
        Args:
            title: Section title
            level: Section level
            line_start: Line number
            
        Returns:
            A guaranteed unique ID
        """
        import hashlib
        import time
        
        # Include timestamp to ensure uniqueness
        content = f"{title}:{level}:{line_start}:{time.time()}"
        hash_value = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"section-{hash_value}"
    
    def _extract_base_slug(self, section_id: str) -> str:
        """
        Extract the base slug from a section ID (remove numeric suffixes).
        
        Args:
            section_id: A section ID that might have numeric suffix
            
        Returns:
            The base slug part
        """
        # Remove common numeric suffixes like "-2", "-3", etc.
        match = re.match(r'^(.+)-\d+$', section_id)
        if match:
            return match.group(1)
        
        # If it's a hash-based ID, return just "section" as base
        if section_id.startswith('section-') and len(section_id) == 16:  # "section-" + 8 chars
            return "section"
        
        return section_id
    
    def clear_cache(self):
        """Clear the internal cache of used IDs."""
        self._used_ids.clear()


# Global instance for use throughout the application
section_id_generator = SectionIDGenerator()
