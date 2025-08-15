#!/usr/bin/env python3
"""
LLM-powered text ingestion pipeline for extracting writing entities and relationships.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from neo4j_connector import WritingGraphDB

load_dotenv()

@dataclass
class Entity:
    name: str
    type: str  # Character, Location, Scene, Theme, etc.
    properties: Dict[str, Any]

@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    relationship_type: str
    properties: Dict[str, Any] = None

class TextIngestionPipeline:
    def __init__(self, testing_mode: bool = False, track_sources: bool = True):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = WritingGraphDB()
        self.testing_mode = testing_mode
        self.track_sources = track_sources
        self.current_source_file = None
        
        if self.testing_mode:
            print("🧪 TESTING MODE: Entities will be marked for easy cleanup")
    
    def _add_tracking_fields(self, base_query: str) -> str:
        """Add source tracking and test marker fields to a Cypher query."""
        query = base_query
        
        # Add source tracking
        if self.track_sources and self.current_source_file:
            query += ",\n                        _source_file = $source_file"
        
        # Add test markers
        if self.testing_mode:
            query += ",\n                        _test_marker = true,\n                        _test_timestamp = datetime()"
        
        return query
    
    def _get_base_params(self, **params) -> Dict[str, Any]:
        """Get parameters including tracking fields."""
        result = dict(params)
        if self.track_sources and self.current_source_file:
            result["source_file"] = self.current_source_file
        return result
    
    def reingest_file(self, file_path: str, story_title: str = None):
        """Reingest a file by temporarily using test mode for easy cleanup."""
        print(f"🔄 REINGESTING file: {file_path}")
        print("💡 Using test mode for safe reingestion - will clean up after")
        
        # First, ingest in test mode
        old_testing_mode = self.testing_mode
        self.testing_mode = True
        
        try:
            # Ingest with test markers
            result = self.ingest_text_file(file_path, story_title)
            
            # If successful, clean up test entities and re-ingest normally
            print("🧹 Cleaning up test run...")
            self.db.cleanup_test_entities()
            
            print("📝 Re-ingesting normally...")
            self.testing_mode = False
            result = self.ingest_text_file(file_path, story_title)
            
            return result
            
        finally:
            # Restore original testing mode
            self.testing_mode = old_testing_mode
        
    def parse_tags(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse @tag:value syntax from text to create appropriate entities.
        Examples: @character:Soren creates Character, @power:hardening creates Tag
        """
        tag_pattern = r'@(\w+):([A-Za-z_]+)'
        matches = re.findall(tag_pattern, text)
        
        # Map categories to proper entity types
        entity_mapping = {
            "character": "characters",
            "location": "locations", 
            "scene": "scenes",
            "theme": "themes",
            "story": "stories"
        }
        
        parsed_entities = {
            "characters": [],
            "locations": [],
            "scenes": [],
            "themes": [], 
            "stories": [],
            "tags": []
        }
        
        for category, value in matches:
            if category.lower() in entity_mapping:
                # Create proper entity type
                entity_type = entity_mapping[category.lower()]
                
                if entity_type == "characters":
                    parsed_entities["characters"].append({
                        "name": value,
                        "description": f"Character mentioned via @{category}:{value}",
                        "role": "unknown"
                    })
                elif entity_type == "locations":
                    parsed_entities["locations"].append({
                        "name": value,
                        "description": f"Location mentioned via @{category}:{value}",
                        "type": "unknown"
                    })
                elif entity_type == "scenes":
                    parsed_entities["scenes"].append({
                        "title": value,
                        "summary": f"Scene mentioned via @{category}:{value}"
                    })
                elif entity_type == "themes":
                    parsed_entities["themes"].append({
                        "name": value,
                        "description": f"Theme mentioned via @{category}:{value}"
                    })
                elif entity_type == "stories":
                    parsed_entities["stories"].append({
                        "title": value,
                        "summary": f"Story mentioned via @{category}:{value}"
                    })
            else:
                # Create tag for non-entity categories (power, skill, magic, etc.)
                parsed_entities["tags"].append({
                    "category": category,
                    "value": value,
                    "name": f"{category.title()}: {value.title()}",
                    "description": f"Tagged as @{category}:{value}"
                })
        
        return parsed_entities
    
    def extract_entities_and_relationships(self, text: str, context: str = "") -> Dict[str, Any]:
        """
        Use LLM to extract entities and relationships from text.
        """
        prompt = f"""
You are an expert at analyzing creative writing to extract entities and relationships for a knowledge graph.

Context: {context}

Text to analyze:
{text}

Extract the following from this text and return as JSON:

1. Characters: People mentioned in the text
2. Locations: Places, settings, buildings, rooms, etc.
3. Scenes: If this represents a scene, extract scene info
4. Themes: Abstract concepts, motifs, or themes explored
5. Plot Points: Key events, conflicts, or story developments
6. Tags: Custom tags in @category:value format (like @power:hardening, @magic:fire)
7. Relationships: Connections between entities

Return in this exact JSON format:
{{
    "entities": {{
        "characters": [
            {{
                "name": "Character Name",
                "description": "Brief description",
                "age": null or number,
                "role": "protagonist/antagonist/supporting/etc",
                "traits": ["trait1", "trait2"]
            }}
        ],
        "locations": [
            {{
                "name": "Location Name", 
                "type": "city/building/room/etc",
                "description": "Description of the place"
            }}
        ],
        "scenes": [
            {{
                "title": "Scene Title",
                "summary": "Brief summary",
                "setting": "Where it takes place",
                "mood": "emotional tone"
            }}
        ],
        "themes": [
            {{
                "name": "Theme Name",
                "description": "What this theme represents"
            }}
        ],
        "plot_points": [
            {{
                "title": "Event Title",
                "description": "What happens",
                "importance": "major/minor",
                "type": "conflict/resolution/twist/etc"
            }}
        ],
        "tags": [
            {{
                "category": "power/magic/skill/etc",
                "value": "specific_ability",
                "name": "Display Name",
                "description": "What this represents"
            }}
        ]
    }},
    "relationships": [
        {{
            "from": "Entity 1",
            "to": "Entity 2", 
            "type": "KNOWS/LIVES_IN/APPEARS_IN/EXPLORES/etc",
            "description": "Description of relationship"
        }}
    ]
}}

Only extract entities and relationships that are clearly present in the text. Be accurate and conservative.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing creative writing text to extract entities and relationships for a knowledge graph database."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response (sometimes LLM includes extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print("No valid JSON found in LLM response")
                return {"entities": {}, "relationships": []}
                
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return {"entities": {}, "relationships": []}
    
    def create_entities_in_neo4j(self, entities: Dict[str, List[Dict]]):
        """Create entities in Neo4j database with deduplication."""
        with self.db.driver.session() as session:
            # Create characters
            for char in entities.get("characters", []):
                if self.testing_mode:
                    query = """
                    MERGE (c:Character {name: $name})
                    SET c.description = $description,
                        c.age = $age,
                        c.role = $role,
                        c.traits = $traits,
                        c._test_marker = true,
                        c._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (c:Character {name: $name})
                    SET c.description = $description,
                        c.age = $age,
                        c.role = $role,
                        c.traits = $traits
                    """
                session.run(query, 
                    name=char["name"],
                    description=char.get("description", ""),
                    age=char.get("age"),
                    role=char.get("role", ""),
                    traits=char.get("traits", [])
                )
            
            # Create locations
            for loc in entities.get("locations", []):
                if self.testing_mode:
                    query = """
                    MERGE (l:Location {name: $name})
                    SET l.type = $type,
                        l.description = $description,
                        l._test_marker = true,
                        l._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (l:Location {name: $name})
                    SET l.type = $type,
                        l.description = $description
                    """
                session.run(query,
                    name=loc["name"],
                    type=loc.get("type", ""),
                    description=loc.get("description", "")
                )
            
            # Create scenes
            for scene in entities.get("scenes", []):
                if self.testing_mode:
                    query = """
                    MERGE (s:Scene {title: $title})
                    SET s.summary = $summary,
                        s.setting = $setting,
                        s.mood = $mood,
                        s._test_marker = true,
                        s._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (s:Scene {title: $title})
                    SET s.summary = $summary,
                        s.setting = $setting,
                        s.mood = $mood
                    """
                session.run(query,
                    title=scene["title"],
                    summary=scene.get("summary", ""),
                    setting=scene.get("setting", ""),
                    mood=scene.get("mood", "")
                )
            
            # Create themes
            for theme in entities.get("themes", []):
                if self.testing_mode:
                    query = """
                    MERGE (t:Theme {name: $name})
                    SET t.description = $description,
                        t._test_marker = true,
                        t._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (t:Theme {name: $name})
                    SET t.description = $description
                    """
                session.run(query,
                    name=theme["name"],
                    description=theme.get("description", "")
                )
            
            # Create plot points
            for plot in entities.get("plot_points", []):
                if self.testing_mode:
                    query = """
                    MERGE (p:PlotPoint {title: $title})
                    SET p.description = $description,
                        p.importance = $importance,
                        p.type = $type,
                        p._test_marker = true,
                        p._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (p:PlotPoint {title: $title})
                    SET p.description = $description,
                        p.importance = $importance,
                        p.type = $type
                    """
                session.run(query,
                    title=plot["title"],
                    description=plot.get("description", ""),
                    importance=plot.get("importance", ""),
                    type=plot.get("type", "")
                )
            
            # Create tags
            for tag in entities.get("tags", []):
                if self.testing_mode:
                    query = """
                    MERGE (t:Tag {name: $name})
                    SET t.category = $category,
                        t.value = $value,
                        t.description = $description,
                        t._test_marker = true,
                        t._test_timestamp = datetime()
                    """
                else:
                    query = """
                    MERGE (t:Tag {name: $name})
                    SET t.category = $category,
                        t.value = $value,
                        t.description = $description
                    """
                session.run(query,
                    name=tag["name"],
                    category=tag.get("category", ""),
                    value=tag.get("value", ""),
                    description=tag.get("description", "")
                )
    
    def create_relationships_in_neo4j(self, relationships: List[Dict]):
        """Create relationships in Neo4j database."""
        with self.db.driver.session() as session:
            for rel in relationships:
                # Dynamic relationship creation
                query = f"""
                MATCH (a), (b)
                WHERE a.name = $from_name OR a.title = $from_name
                AND (b.name = $to_name OR b.title = $to_name)
                MERGE (a)-[r:{rel['type']}]->(b)
                SET r.description = $description
                """
                try:
                    session.run(query,
                        from_name=rel["from"],
                        to_name=rel["to"],
                        description=rel.get("description", "")
                    )
                except Exception as e:
                    print(f"Error creating relationship {rel}: {e}")
    
    def ingest_text_file(self, file_path: str, story_title: str = None):
        """
        Ingest a text file and extract entities/relationships.
        """
        try:
            # Set current source file for tracking
            self.current_source_file = file_path
            
            print(f"Processing file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"Content length: {len(content)} characters")
            
            # Parse @tags first
            parsed_tags = self.parse_tags(content)
            
            # Extract entities and relationships
            context = f"This is content from the file '{file_path}'"
            if story_title:
                context += f" from the story '{story_title}'"
            
            extracted_data = self.extract_entities_and_relationships(content, context)
            
            # Merge parsed tag entities with LLM extracted entities
            if parsed_tags:
                if "entities" not in extracted_data:
                    extracted_data["entities"] = {}
                
                # Merge each entity type, avoiding duplicates
                for entity_type, entities in parsed_tags.items():
                    if entities:  # Only process if there are entities
                        existing_entities = extracted_data["entities"].get(entity_type, [])
                        
                        # Deduplicate by name/title
                        existing_names = set()
                        if entity_type in ["characters", "locations", "themes"]:
                            existing_names = {e.get("name", "").lower() for e in existing_entities}
                        elif entity_type in ["scenes", "stories"]:
                            existing_names = {e.get("title", "").lower() for e in existing_entities}
                        elif entity_type == "tags":
                            existing_names = {e.get("name", "").lower() for e in existing_entities}
                        
                        # Add new entities that don't already exist
                        for entity in entities:
                            identifier = ""
                            if entity_type in ["characters", "locations", "themes"]:
                                identifier = entity.get("name", "").lower()
                            elif entity_type in ["scenes", "stories"]:
                                identifier = entity.get("title", "").lower()
                            elif entity_type == "tags":
                                identifier = entity.get("name", "").lower()
                            
                            if identifier and identifier not in existing_names:
                                existing_entities.append(entity)
                                existing_names.add(identifier)
                        
                        extracted_data["entities"][entity_type] = existing_entities
            
            print("Extracted entities:")
            for entity_type, entities in extracted_data["entities"].items():
                print(f"  {entity_type}: {len(entities)} items")
                for entity in entities:
                    print(f"    - {entity.get('name', entity.get('title', 'Unknown'))}")
            
            print(f"Extracted relationships: {len(extracted_data['relationships'])} items")
            
            # Create in Neo4j
            self.create_entities_in_neo4j(extracted_data["entities"])
            self.create_relationships_in_neo4j(extracted_data["relationships"])
            
            print("✅ Successfully ingested into Neo4j!")
            
            return extracted_data
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None
    
    def ingest_text_content(self, content: str, title: str = "Untitled", story_title: str = None):
        """
        Ingest raw text content and extract entities/relationships.
        """
        print(f"Processing content: {title}")
        print(f"Content length: {len(content)} characters")
        
        # Parse @tags first
        parsed_tags = self.parse_tags(content)
        
        context = f"This is content titled '{title}'"
        if story_title:
            context += f" from the story '{story_title}'"
        
        extracted_data = self.extract_entities_and_relationships(content, context)
        
        # Merge parsed tag entities with LLM extracted entities
        if parsed_tags:
            if "entities" not in extracted_data:
                extracted_data["entities"] = {}
            
            # Merge each entity type, avoiding duplicates
            for entity_type, entities in parsed_tags.items():
                if entities:  # Only process if there are entities
                    existing_entities = extracted_data["entities"].get(entity_type, [])
                    
                    # Deduplicate by name/title
                    existing_names = set()
                    if entity_type in ["characters", "locations", "themes"]:
                        existing_names = {e.get("name", "").lower() for e in existing_entities}
                    elif entity_type in ["scenes", "stories"]:
                        existing_names = {e.get("title", "").lower() for e in existing_entities}
                    elif entity_type == "tags":
                        existing_names = {e.get("name", "").lower() for e in existing_entities}
                    
                    # Add new entities that don't already exist
                    for entity in entities:
                        identifier = ""
                        if entity_type in ["characters", "locations", "themes"]:
                            identifier = entity.get("name", "").lower()
                        elif entity_type in ["scenes", "stories"]:
                            identifier = entity.get("title", "").lower()
                        elif entity_type == "tags":
                            identifier = entity.get("name", "").lower()
                        
                        if identifier and identifier not in existing_names:
                            existing_entities.append(entity)
                            existing_names.add(identifier)
                    
                    extracted_data["entities"][entity_type] = existing_entities
        
        print("Extracted entities:")
        for entity_type, entities in extracted_data["entities"].items():
            if entities:
                print(f"  {entity_type}: {len(entities)} items")
                for entity in entities:
                    print(f"    - {entity.get('name', entity.get('title', 'Unknown'))}")
        
        print(f"Extracted relationships: {len(extracted_data['relationships'])} items")
        
        # Create in Neo4j
        self.create_entities_in_neo4j(extracted_data["entities"])
        self.create_relationships_in_neo4j(extracted_data["relationships"])
        
        print("✅ Successfully ingested into Neo4j!")
        
        return extracted_data


def main():
    """Test the ingestion pipeline with sample text."""
    pipeline = TextIngestionPipeline()
    
    # Test with sample scene text
    sample_text = """
    Alice Chen stared at the glowing monitor in her cramped TechCorp cubicle. The code patterns she'd discovered were unlike anything she'd seen before—hidden algorithms that seemed to track user behavior in ways that violated every privacy policy the company claimed to follow.
    
    She picked up her phone and texted her best friend Sarah Kim: "Coffee at Binary Cafe? I found something big."
    
    Twenty minutes later, Alice sat across from Sarah at their favorite corner table. The cafe was buzzing with the usual crowd of programmers and startup founders, laptops open, the sound of espresso machines providing a familiar backdrop.
    
    "You look worried," Sarah observed, stirring sugar into her latte.
    
    "I am worried," Alice replied, lowering her voice. "Remember that new analytics system Marcus Webb's team deployed last month? I think it's doing more than just tracking page views."
    """
    
    result = pipeline.ingest_text_content(
        content=sample_text,
        title="Discovery at TechCorp",
        story_title="The Algorithm Conspiracy"
    )
    
    print("\n" + "="*50)
    print("Sample extraction completed!")
    print("Check your Neo4j Browser to see the new entities and relationships.")


if __name__ == "__main__":
    main()