# 📝 Writing Knowledge Graph System

An intelligent writing system that combines Neo4j graph database with LLM-powered content organization and natural language querying. Write your stories, characters, and world-building in markdown, then query everything conversationally.

## 🚀 Quick Start

1. **Setup environment:**
   ```bash
   source writing_env/bin/activate
   ```

2. **Start writing:**
   ```bash
   just new-draft "my-character-idea"
   ```

3. **Organize and ingest:**
   ```bash
   just finalize
   ```

4. **Query your knowledge:**
   ```bash
   just query
   ```

## 📁 Project Structure

```
├── content/
│   ├── drafts/          # ✍️  Write everything here first
│   ├── characters/      # 👥 Character profiles
│   ├── locations/       # 🌍 Settings and places
│   ├── scenes/          # 🎬 Individual scenes/chapters
│   ├── stories/         # 📚 Main story files
│   ├── worldbuilding/   # ⚡ Magic systems, cultures
│   ├── themes/          # 🎭 Thematic explorations
│   └── research/        # 📖 Reference materials
├── src/
│   ├── neo4j_connector.py   # 🔌 Database interface
│   ├── text_ingestion.py    # 🤖 LLM-powered content extraction
│   ├── writing_assistant.py # 💬 Natural language query interface
│   ├── organize_content.py  # 📂 Auto-organization script
│   └── requirements.txt     # 📦 Python dependencies
├── database/
│   ├── data_model.md        # 📊 Neo4j database schema
│   └── sample_queries.cypher # 📝 Example Cypher queries
├── justfile            # ⚡ Command shortcuts
└── README.md           # 📖 Documentation
```

## 🏗️ Core Features

### 📝 Smart Content Organization
- **Auto-detection**: Files are automatically categorized based on content
- **@Tag System**: Use `@power:hardening`, `@skill:lockpicking` syntax for abilities
- **Relationship Mapping**: Characters, locations, and scenes are automatically linked

### 🧠 LLM-Powered Extraction
- **Entity Recognition**: Automatically identifies characters, locations, themes
- **Relationship Discovery**: Finds connections between story elements
- **Tag Processing**: Converts `@category:value` syntax into queryable objects

### 💬 Natural Language Queries
- Ask questions like "Who are Alice's friends?" or "What magic systems exist?"
- Powered by GPT-4 with Cypher query generation
- Contextual understanding of your story world

## ⚡ Quick Commands (using `just`)

### Writing Workflow
```bash
just new-draft "character-name"     # Create new draft file
just new-character "Alice Chen"     # Create character template
just new-location "TechCorp"        # Create location template
just new-scene "discovery"          # Create scene template

just list-drafts                    # Show all draft files
just edit "filename"                # Open file in default editor
```

### Content Management
```bash
just finalize                       # Process all drafts → organized folders → Neo4j
just process "filename.md"          # Process specific file
just preview                        # Dry-run: see what would be organized

just status                         # Show content summary
just backup                         # Backup current content
```

### Querying & Analysis
```bash
just query                          # Start interactive assistant
just quick-query "your question"    # Single question mode
just stats                          # Show database statistics
```

### Development & Maintenance
```bash
just setup                          # Install dependencies
just test-db                        # Test Neo4j connection
just reset-db                       # Clear database (careful!)
just export                         # Export knowledge graph
```

## 📋 Writing Templates

### Character Template
```markdown
# Character Name

**Character:** Brief description and role

**Personality:** Key traits and motivations

**Backstory:** Important history and background

**Appearance:** Physical description

**Abilities:** 
- @skill:ability_name
- @power:special_power

**Goals:** What they want to achieve

**Relationships:**
- Connection to other characters
```

### Location Template
```markdown
# Location Name

**Location:** Type and general description

**Architecture/Geography:** Physical details

**Atmosphere:** Mood and feeling of the place

**Notable Features:**
- Important areas or landmarks
- Hidden secrets

**Significance:** Role in the story
```

### Magic System Template
```markdown
# Magic System: System Name

**World:** Setting and context

**Rules:**
1. How the magic works
2. Limitations and costs
3. Who can use it

**Abilities:**
- @magic:fire - Description
- @power:telepathy - Description

**Integration:** How it affects the world/story
```

## 🏷️ Tag System

Use `@category:value` syntax anywhere in your writing:

### Categories
- `@power:hardening` - Supernatural abilities
- `@skill:lockpicking` - Learned abilities  
- `@magic:fire` - Magical powers
- `@trait:immortal` - Character traits
- `@tech:neural_interface` - Technology
- `@culture:elven` - Cultural elements

### Examples
```markdown
Alice has @power:hardening that activates under stress.
Marcus learned @skill:meditation to control his @power:telepathy.
The artifact grants @magic:time_manipulation.
```

## 💾 Database Schema

### Node Types
- **Character**: People in your story
- **Location**: Places and settings
- **Scene**: Individual scenes/chapters
- **Story**: Main story containers
- **Theme**: Abstract concepts
- **PlotPoint**: Key events
- **Tag**: @category:value objects

### Relationships
- Character -[:APPEARS_IN]-> Scene
- Character -[:KNOWS]-> Character
- Character -[:HAS]-> Tag
- Scene -[:TAKES_PLACE_IN]-> Location
- Scene -[:PART_OF]-> Story

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key
```

### Dependencies
- Python 3.8+
- Neo4j Database
- OpenAI API access
- `just` command runner

## 🎯 Workflow Examples

### Starting a New Story
```bash
# Create story outline
just new-draft "story-outline"

# Create main characters
just new-character "protagonist"
just new-character "antagonist"

# Build the world
just new-location "main-setting"
just new-draft "magic-system"

# Write scenes
just new-scene "opening-scene"
just new-scene "climax"

# Organize everything
just finalize

# Query your world
just quick-query "Who are the main characters?"
```

### Daily Writing Session
```bash
# Check what you have
just status
just list-drafts

# Write new content
just new-draft "chapter-3"
# ... write content ...

# Process when ready
just process "chapter-3.md"

# Query for inspiration
just quick-query "What themes am I exploring?"
just quick-query "Which characters haven't interacted yet?"
```

## 🐛 Troubleshooting

### Common Issues
1. **Neo4j Connection Failed**: Check database is running and credentials in `.env`
2. **OpenAI API Error**: Verify API key in `.env` file
3. **File Not Found**: Check file paths are relative to project root
4. **EOF Error**: Fixed in writing_assistant.py with proper exception handling

### Logs and Debugging
```bash
just test-db              # Test database connection
just stats               # Check database health
python writing_assistant.py  # Manual assistant mode
```

## 🤝 Contributing

This is a personal writing system, but feel free to:
- Adapt the code for your own projects
- Suggest improvements for the workflow
- Share interesting query patterns

## 📄 License

MIT License - Feel free to use and modify for your own writing projects.

---

**Happy Writing!** 📚✨

> "The best way to find out if you can trust somebody is to trust them." - Your story characters, probably