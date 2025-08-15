#!/usr/bin/env python3
"""
Neo4j connector for the writing knowledge graph system.
"""

from neo4j import GraphDatabase
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WritingGraphDB:
    def __init__(self, uri=None, username=None, password=None):
        """
        Initialize connection to Neo4j database.
        Uses environment variables from .env file if parameters not provided.
        """
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
    
    def test_connection(self):
        """Test if we can connect to the database."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful!' as message")
                return result.single()["message"]
        except Exception as e:
            return f"Connection failed: {str(e)}"
    
    def get_all_characters(self) -> List[Dict[str, Any]]:
        """Get all characters from the database."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Character)
                RETURN c.name as name, c.age as age, c.role as role, c.description as description
                ORDER BY c.name
            """)
            return [dict(record) for record in result]
    
    def get_character_scenes(self, character_name: str) -> List[Dict[str, Any]]:
        """Get all scenes a character appears in."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Character {name: $name})-[:APPEARS_IN]->(s:Scene)
                RETURN s.title as scene_title, s.summary as summary, s.word_count as word_count
                ORDER BY s.title
            """, name=character_name)
            return [dict(record) for record in result]
    
    def get_character_relationships(self, character_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for a character."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c1:Character {name: $name})-[r]-(c2:Character)
                RETURN c2.name as related_character, type(r) as relationship_type
                ORDER BY c2.name
            """, name=character_name)
            return [dict(record) for record in result]
    
    def get_story_overview(self, story_title: str) -> Dict[str, Any]:
        """Get comprehensive overview of a story."""
        with self.driver.session() as session:
            # Get story details
            story_result = session.run("""
                MATCH (s:Story {title: $title})
                RETURN s.title as title, s.genre as genre, s.status as status, s.summary as summary
            """, title=story_title)
            story = dict(story_result.single()) if story_result.peek() else {}
            
            # Get characters
            char_result = session.run("""
                MATCH (c:Character)-[:APPEARS_IN]->(scene:Scene)-[:PART_OF]->(s:Story {title: $title})
                RETURN DISTINCT c.name as name, c.role as role
                ORDER BY c.name
            """, title=story_title)
            characters = [dict(record) for record in char_result]
            
            # Get locations
            loc_result = session.run("""
                MATCH (l:Location)<-[:TAKES_PLACE_IN]-(scene:Scene)-[:PART_OF]->(s:Story {title: $title})
                RETURN DISTINCT l.name as name, l.type as type
                ORDER BY l.name
            """, title=story_title)
            locations = [dict(record) for record in loc_result]
            
            # Get scenes
            scene_result = session.run("""
                MATCH (scene:Scene)-[:PART_OF]->(s:Story {title: $title})
                RETURN scene.title as title, scene.summary as summary, scene.word_count as word_count, scene.status as status
                ORDER BY scene.title
            """, title=story_title)
            scenes = [dict(record) for record in scene_result]
            
            return {
                "story": story,
                "characters": characters,
                "locations": locations,
                "scenes": scenes
            }
    
    def search_by_keyword(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search for keyword across all text fields."""
        with self.driver.session() as session:
            # Search characters
            char_result = session.run("""
                MATCH (c:Character)
                WHERE toLower(c.name) CONTAINS toLower($keyword) 
                   OR toLower(c.description) CONTAINS toLower($keyword)
                RETURN c.name as name, c.description as description, 'Character' as type
            """, keyword=keyword)
            characters = [dict(record) for record in char_result]
            
            # Search locations
            loc_result = session.run("""
                MATCH (l:Location)
                WHERE toLower(l.name) CONTAINS toLower($keyword) 
                   OR toLower(l.description) CONTAINS toLower($keyword)
                RETURN l.name as name, l.description as description, 'Location' as type
            """, keyword=keyword)
            locations = [dict(record) for record in loc_result]
            
            # Search scenes
            scene_result = session.run("""
                MATCH (s:Scene)
                WHERE toLower(s.title) CONTAINS toLower($keyword) 
                   OR toLower(s.summary) CONTAINS toLower($keyword)
                RETURN s.title as name, s.summary as description, 'Scene' as type
            """, keyword=keyword)
            scenes = [dict(record) for record in scene_result]
            
            return {
                "characters": characters,
                "locations": locations,
                "scenes": scenes
            }
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags from the database."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                RETURN t.name as name, t.category as category, t.value as value, t.description as description
                ORDER BY t.category, t.value
            """)
            return [dict(record) for record in result]
    
    def get_tags_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all tags in a specific category."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                WHERE toLower(t.category) = toLower($category)
                RETURN t.name as name, t.category as category, t.value as value, t.description as description
                ORDER BY t.value
            """, category=category)
            return [dict(record) for record in result]


def main():
    """Test the Neo4j connection and basic queries."""
    print("Connecting to Neo4j...")
    db = WritingGraphDB()  # Uses .env file automatically
    
    # Test connection
    print(db.test_connection())
    
    # Get all characters
    print("\n=== All Characters ===")
    characters = db.get_all_characters()
    for char in characters:
        print(f"- {char['name']} ({char['role']}): {char['description']}")
    
    # Get character scenes
    if characters:
        first_char = characters[0]['name']
        print(f"\n=== Scenes for {first_char} ===")
        scenes = db.get_character_scenes(first_char)
        for scene in scenes:
            print(f"- {scene['scene_title']}: {scene['summary']} ({scene['word_count']} words)")
    
    # Get story overview
    print("\n=== Story Overview ===")
    overview = db.get_story_overview("The Algorithm Conspiracy")
    if overview['story']:
        story = overview['story']
        print(f"Title: {story['title']}")
        print(f"Genre: {story['genre']}")
        print(f"Status: {story['status']}")
        print(f"Summary: {story['summary']}")
        print(f"Characters: {len(overview['characters'])}")
        print(f"Locations: {len(overview['locations'])}")
        print(f"Scenes: {len(overview['scenes'])}")
    
    # Search test
    print("\n=== Search for 'Alice' ===")
    results = db.search_by_keyword("Alice")
    for category, items in results.items():
        if items:
            print(f"{category.capitalize()}:")
            for item in items:
                print(f"  - {item['name']}")
    
    db.close()
    print("\nConnection closed.")


if __name__ == "__main__":
    main()