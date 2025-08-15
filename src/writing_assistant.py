#!/usr/bin/env python3
"""
Writing Assistant: Natural language query interface for the writing knowledge graph.
"""

import os
import re
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv
from neo4j_connector import WritingGraphDB

load_dotenv()

class WritingAssistant:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db = WritingGraphDB()
        
    def generate_cypher_query(self, natural_language_question: str) -> str:
        """
        Convert natural language question to Cypher query using LLM.
        """
        prompt = f"""
You are an expert at converting natural language questions about creative writing into Neo4j Cypher queries.

The database schema includes these node types:
- Character (name, description, age, role, traits)
- Location (name, type, description)
- Scene (title, summary, setting, mood, word_count, status, pov_character)
- Story (title, genre, status, summary)
- Theme (name, description)
- PlotPoint (title, description, importance, type)
- Tag (name, category, value, description) - represents @tag:value syntax like @power:hardening

Common relationships:
- Character -[:APPEARS_IN]-> Scene
- Character -[:KNOWS]-> Character
- Character -[:LIVES_IN]-> Location
- Character -[:HAS]-> Tag (for abilities, powers, skills)
- Scene -[:TAKES_PLACE_IN]-> Location
- Scene -[:PART_OF]-> Story
- Scene -[:FOLLOWS]-> Scene
- Story -[:EXPLORES]-> Theme
- Character -[:EMBODIES]-> Theme
- Tag -[:BELONGS_TO]-> Character (reverse of HAS)

Question: {natural_language_question}

Convert this to a Cypher query. Return ONLY the Cypher query, no explanation:
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at converting natural language to Cypher queries. Return only valid Cypher syntax."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            cypher_query = response.choices[0].message.content.strip()
            # Clean up the response to get just the query
            cypher_query = re.sub(r'^```cypher\s*', '', cypher_query)
            cypher_query = re.sub(r'^```\s*', '', cypher_query)
            cypher_query = re.sub(r'\s*```$', '', cypher_query)
            
            return cypher_query
            
        except Exception as e:
            print(f"Error generating Cypher query: {e}")
            return ""
    
    def execute_cypher_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        try:
            with self.db.driver.session() as session:
                result = session.run(cypher_query)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    def format_results(self, results: List[Dict[str, Any]], question: str) -> str:
        """
        Format query results into a natural language response.
        """
        if not results:
            return "I didn't find any results for that question."
        
        # Let LLM format the results naturally
        results_text = str(results)
        
        prompt = f"""
Question: {question}

Query Results: {results_text}

Format these query results into a natural, conversational response that answers the original question. 
Be concise but informative. If there are multiple results, organize them clearly.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful writing assistant. Format database query results into natural, conversational responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback to simple formatting
            formatted = f"Found {len(results)} results:\n"
            for i, result in enumerate(results, 1):
                formatted += f"{i}. {result}\n"
            return formatted
    
    def ask(self, question: str) -> str:
        """
        Main interface: ask a natural language question about your writing.
        """
        print(f"\n🤔 Question: {question}")
        
        # Generate Cypher query
        cypher_query = self.generate_cypher_query(question)
        print(f"🔍 Generated query: {cypher_query}")
        
        if not cypher_query:
            return "I couldn't understand that question. Try rephrasing it."
        
        # Execute query
        results = self.execute_cypher_query(cypher_query)
        
        # Format response
        response = self.format_results(results, question)
        print(f"💭 Answer: {response}")
        
        return response
    
    def get_story_insights(self, story_title: str = None) -> str:
        """Get high-level insights about a story."""
        if story_title:
            story_filter = f"{{title: '{story_title}'}}"
        else:
            story_filter = ""
        
        insights = []
        
        # Get basic stats
        with self.db.driver.session() as session:
            # Character count
            char_result = session.run(f"""
                MATCH (c:Character)-[:APPEARS_IN]->(s:Scene)-[:PART_OF]->(story:Story {story_filter})
                RETURN count(DISTINCT c) as character_count, story.title as title
            """)
            char_data = char_result.single()
            if char_data:
                insights.append(f"📚 {char_data['title'] or 'Your writing'} has {char_data['character_count']} characters")
            
            # Scene count and word count
            scene_result = session.run(f"""
                MATCH (s:Scene)-[:PART_OF]->(story:Story {story_filter})
                RETURN count(s) as scene_count, sum(s.word_count) as total_words, story.title as title
            """)
            scene_data = scene_result.single()
            if scene_data:
                insights.append(f"📝 {scene_data['scene_count']} scenes with {scene_data['total_words'] or 0} total words")
            
            # Most connected character
            popular_char = session.run(f"""
                MATCH (c:Character)-[:APPEARS_IN]->(s:Scene)-[:PART_OF]->(story:Story {story_filter})
                WITH c, count(s) as scene_count
                ORDER BY scene_count DESC
                LIMIT 1
                RETURN c.name as name, scene_count
            """)
            char_data = popular_char.single()
            if char_data:
                insights.append(f"🌟 {char_data['name']} appears in {char_data['scene_count']} scenes")
        
        return "\n".join(insights)
    
    def suggest_questions(self) -> List[str]:
        """Suggest interesting questions the user might ask."""
        return [
            "Who are the main characters in my story?",
            "Which characters appear together most often?",
            "What locations are used in my story?",
            "Show me the scene sequence",
            "Which themes am I exploring?",
            "Who are Alice's connections?",
            "What scenes take place at Binary Cafe?",
            "Which characters haven't interacted yet?",
            "What plot points need development?",
            "Show me character relationship networks"
        ]


def interactive_mode():
    """Run the assistant in interactive mode."""
    assistant = WritingAssistant()
    
    print("🎭 Welcome to your Writing Knowledge Graph Assistant!")
    print("Ask me questions about your characters, plots, scenes, and more.\n")
    
    # Show initial insights
    print("📊 Story Overview:")
    print(assistant.get_story_insights())
    
    print("\n💡 Try asking questions like:")
    suggestions = assistant.suggest_questions()
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"   {i}. {suggestion}")
    
    print("\nType 'quit' to exit, 'help' for more suggestions.\n")
    
    while True:
        try:
            question = input("❓ Ask me anything: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Happy writing!")
                break
            elif question.lower() == 'help':
                print("\n💡 Suggested questions:")
                for i, suggestion in enumerate(assistant.suggest_questions(), 1):
                    print(f"   {i}. {suggestion}")
                continue
            elif not question:
                continue
            
            assistant.ask(question)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Happy writing!")
            break
        except EOFError:
            print("\n👋 Happy writing!")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    assistant.db.close()


def main():
    """Test the assistant with sample questions."""
    assistant = WritingAssistant()
    
    # Test some sample questions
    test_questions = [
        "Who are all the characters in my story?",
        "Which scenes does Alice appear in?",
        "What locations are in The Algorithm Conspiracy?",
        "Show me character relationships"
    ]
    
    print("🎭 Testing Writing Assistant\n")
    
    for question in test_questions:
        assistant.ask(question)
        print("-" * 50)
    
    assistant.db.close()


if __name__ == "__main__":
    # Uncomment the line below to run in interactive mode
    interactive_mode()
    # main()  # Use this for testing