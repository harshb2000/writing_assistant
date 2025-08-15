#!/usr/bin/env python3
"""
Content Organization Script: Automatically move drafts to appropriate directories
and ingest them into the Neo4j database.
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from text_ingestion import TextIngestionPipeline

class ContentOrganizer:
    def __init__(self, base_dir: str = "../content"):
        self.base_dir = Path(base_dir)
        self.drafts_dir = self.base_dir / "drafts"
        self.pipeline = TextIngestionPipeline()
        
        # Directory mapping based on content type
        self.type_dirs = {
            "character": self.base_dir / "characters",
            "location": self.base_dir / "locations", 
            "scene": self.base_dir / "scenes",
            "story": self.base_dir / "stories",
            "worldbuilding": self.base_dir / "worldbuilding",
            "theme": self.base_dir / "themes",
            "research": self.base_dir / "research"
        }
    
    def detect_content_type(self, file_path: Path) -> Tuple[str, Optional[str]]:
        """
        Analyze file content to determine what type it is and suggest a filename.
        Returns (content_type, suggested_filename)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for explicit type markers in frontmatter or headers
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            type_match = re.search(r'type:\s*(\w+)', frontmatter)
            if type_match:
                return type_match.group(1).lower(), None
        
        # Check for content type indicators
        content_lower = content.lower()
        
        # Character indicators
        if any(word in content_lower for word in ['character:', 'personality:', 'backstory:', 'appearance:']):
            return "character", None
            
        # Location indicators  
        if any(word in content_lower for word in ['location:', 'setting:', 'geography:', 'architecture:']):
            return "location", None
            
        # Scene indicators
        if any(word in content_lower for word in ['scene:', 'dialogue:', 'action:', 'pov:']):
            return "scene", None
            
        # Story indicators
        if any(word in content_lower for word in ['chapter', 'story:', 'plot:', 'narrative:']):
            return "story", None
            
        # Worldbuilding indicators
        if any(word in content_lower for word in ['magic system', 'world:', 'culture:', 'history:', 'religion:', 'technology:']):
            return "worldbuilding", None
            
        # Theme indicators
        if any(word in content_lower for word in ['theme:', 'motif:', 'symbolism:', 'meaning:']):
            return "theme", None
            
        # Research indicators
        if any(word in content_lower for word in ['research:', 'reference:', 'inspiration:', 'notes:']):
            return "research", None
        
        # Default to story if no clear type found
        return "story", None
    
    def extract_title_from_content(self, file_path: Path) -> Optional[str]:
        """Extract a title from the file content for naming."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for markdown headers
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean title for filename
            clean_title = re.sub(r'[^\w\s-]', '', title)
            clean_title = re.sub(r'\s+', '_', clean_title.strip())
            return clean_title.lower()
        
        # Look for frontmatter title
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            title_match = re.search(r'title:\s*(.+)', frontmatter)
            if title_match:
                title = title_match.group(1).strip().strip('"\'')
                clean_title = re.sub(r'[^\w\s-]', '', title)
                clean_title = re.sub(r'\s+', '_', clean_title.strip())
                return clean_title.lower()
        
        return None
    
    def generate_filename(self, original_path: Path, content_type: str) -> str:
        """Generate an appropriate filename based on content."""
        # Try to extract title from content
        title = self.extract_title_from_content(original_path)
        if title:
            return f"{title}.md"
        
        # Fall back to original filename
        return original_path.name
    
    def move_and_organize(self, file_path: Path, content_type: str, new_filename: str) -> Path:
        """Move file to appropriate directory and return new path."""
        target_dir = self.type_dirs.get(content_type, self.base_dir / "stories")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / new_filename
        
        # Handle filename conflicts
        counter = 1
        while target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        shutil.move(str(file_path), str(target_path))
        return target_path
    
    def process_draft(self, file_path: Path, story_title: str = None) -> Dict:
        """Process a single draft file: organize and ingest."""
        print(f"\n📝 Processing: {file_path.name}")
        
        # Detect content type
        content_type, suggested_filename = self.detect_content_type(file_path)
        print(f"🔍 Detected type: {content_type}")
        
        # Generate filename
        new_filename = suggested_filename or self.generate_filename(file_path, content_type)
        print(f"📂 Target filename: {new_filename}")
        
        # Move to appropriate directory
        new_path = self.move_and_organize(file_path, content_type, new_filename)
        print(f"✅ Moved to: {new_path}")
        
        # Ingest into Neo4j
        print("🔄 Ingesting into Neo4j...")
        result = self.pipeline.ingest_text_file(str(new_path), story_title)
        
        return {
            "original_path": str(file_path),
            "new_path": str(new_path),
            "content_type": content_type,
            "filename": new_filename,
            "ingestion_result": result
        }
    
    def process_all_drafts(self, story_title: str = None) -> List[Dict]:
        """Process all files in the drafts directory."""
        if not self.drafts_dir.exists():
            print(f"❌ Drafts directory not found: {self.drafts_dir}")
            return []
        
        draft_files = list(self.drafts_dir.glob("*.md"))
        if not draft_files:
            print("📭 No draft files found to process.")
            return []
        
        print(f"🎯 Found {len(draft_files)} draft files to process")
        
        results = []
        for file_path in draft_files:
            try:
                result = self.process_draft(file_path, story_title)
                results.append(result)
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                results.append({
                    "original_path": str(file_path),
                    "error": str(e)
                })
        
        return results
    
    def show_summary(self, results: List[Dict]):
        """Show a summary of processed files."""
        print("\n" + "="*60)
        print("📊 PROCESSING SUMMARY")
        print("="*60)
        
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        
        print(f"✅ Successfully processed: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")
        
        if successful:
            print("\n📂 Organized files:")
            for result in successful:
                print(f"  {result['content_type']}: {result['filename']}")
        
        if failed:
            print("\n❌ Failed files:")
            for result in failed:
                print(f"  {Path(result['original_path']).name}: {result['error']}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Organize draft files and ingest into Neo4j")
    parser.add_argument("--story", help="Story title for ingestion context")
    parser.add_argument("--file", help="Process specific file instead of all drafts")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    
    args = parser.parse_args()
    
    organizer = ContentOrganizer()
    
    if args.file:
        # Process single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        if not args.dry_run:
            result = organizer.process_draft(file_path, args.story)
            organizer.show_summary([result])
        else:
            content_type, _ = organizer.detect_content_type(file_path)
            filename = organizer.generate_filename(file_path, content_type)
            print(f"Would move {file_path.name} to {content_type}/{filename}")
    else:
        # Process all drafts
        if not args.dry_run:
            results = organizer.process_all_drafts(args.story)
            organizer.show_summary(results)
        else:
            draft_files = list(organizer.drafts_dir.glob("*.md"))
            print(f"Would process {len(draft_files)} files:")
            for file_path in draft_files:
                content_type, _ = organizer.detect_content_type(file_path)
                filename = organizer.generate_filename(file_path, content_type)
                print(f"  {file_path.name} -> {content_type}/{filename}")
    
    organizer.pipeline.db.close()


if __name__ == "__main__":
    main()