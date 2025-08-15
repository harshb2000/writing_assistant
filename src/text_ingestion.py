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
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = WritingGraphDB()
        
    def parse_tags(self, text: str) -> List[Dict[str, str]]:
        """
        Parse @tag:value syntax from text to create custom objects.
        Examples: @power:hardening, @magic:fire, @skill:lockpicking
        """
        tag_pattern = r'@(\w+):(\w+)'
        matches = re.findall(tag_pattern, text)
        
        tags = []
        for category, value in matches:
            tags.append({
                "category": category,
                "value": value,
                "name": f"{category.title()}: {value.title()}"
            })
        
        return tags
    
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
        """Create entities in Neo4j database."""
        with self.db.driver.session() as session:
            # Create characters
            for char in entities.get("characters", []):
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"Processing file: {file_path}")
            print(f"Content length: {len(content)} characters")
            
            # Parse @tags first
            parsed_tags = self.parse_tags(content)
            
            # Extract entities and relationships
            context = f"This is content from the file '{file_path}'"
            if story_title:
                context += f" from the story '{story_title}'"
            
            extracted_data = self.extract_entities_and_relationships(content, context)
            
            # Add parsed tags to extracted data
            if parsed_tags:
                if "entities" not in extracted_data:
                    extracted_data["entities"] = {}
                extracted_data["entities"]["tags"] = extracted_data["entities"].get("tags", []) + parsed_tags
            
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
        
        # Add parsed tags to extracted data
        if parsed_tags:
            if "entities" not in extracted_data:
                extracted_data["entities"] = {}
            extracted_data["entities"]["tags"] = extracted_data["entities"].get("tags", []) + parsed_tags
        
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