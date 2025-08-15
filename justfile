# Writing Knowledge Graph System - Command Shortcuts
# Run `just` to see available commands

# Default recipe lists all available commands
default:
    @echo "📝 Writing Knowledge Graph System"
    @echo "================================="
    @echo ""
    @echo "✍️  Writing Commands:"
    @echo "  just new-draft NAME      - Create new draft file"
    @echo "  just new-character NAME  - Create character template"
    @echo "  just new-location NAME   - Create location template"  
    @echo "  just new-scene NAME      - Create scene template"
    @echo "  just list-drafts         - Show all draft files"
    @echo "  just edit FILE           - Open file in editor"
    @echo ""
    @echo "📂 Content Management:"
    @echo "  just finalize            - Process all drafts"
    @echo "  just process FILE        - Process specific file"
    @echo "  just preview             - Preview what would be organized"
    @echo "  just status              - Show content summary"
    @echo ""
    @echo "💬 Querying:"
    @echo "  just query               - Start interactive assistant"
    @echo "  just ask QUESTION        - Ask single question"
    @echo "  just stats               - Show database statistics"
    @echo ""
    @echo "🔧 System:"
    @echo "  just setup               - Install dependencies"
    @echo "  just test-db             - Test Neo4j connection"
    @echo "  just activate            - Activate virtual environment"

# Setup and installation
setup:
    @echo "🔧 Setting up writing environment..."
    python3 -m venv writing_env
    ./writing_env/bin/pip install -r src/requirements.txt
    @echo "✅ Setup complete! Run 'just activate' to start"

# Activate virtual environment  
activate:
    @echo "💡 Run: source writing_env/bin/activate"

# Writing commands
new-draft name:
    @echo "📝 Creating new draft: {{name}}"
    @mkdir -p content/drafts
    @echo "# {{name}}" > content/drafts/{{name}}.md
    @echo "" >> content/drafts/{{name}}.md
    @echo "Write your content here..." >> content/drafts/{{name}}.md
    @echo "✅ Created: content/drafts/{{name}}.md"
    @echo "💡 Tip: Use @power:ability or @skill:name for special abilities"

new-character name:
    @echo "👥 Creating character template: {{name}}"
    @mkdir -p content/drafts
    @echo "# {{name}} - Character Profile" > content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Character:** Brief description and role in the story" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Personality:** Key traits, motivations, and quirks" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Backstory:** Important history and background" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Appearance:** Physical description" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Abilities:**" >> content/drafts/{{name}}_character.md
    @echo "- @skill:ability_name - Description" >> content/drafts/{{name}}_character.md
    @echo "- @power:special_power - Description" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Goals:** What they want to achieve" >> content/drafts/{{name}}_character.md
    @echo "" >> content/drafts/{{name}}_character.md
    @echo "**Relationships:** Connections to other characters" >> content/drafts/{{name}}_character.md
    @echo "✅ Created: content/drafts/{{name}}_character.md"

new-location name:
    @echo "🌍 Creating location template: {{name}}"
    @mkdir -p content/drafts
    @echo "# {{name}}" > content/drafts/{{name}}_location.md
    @echo "" >> content/drafts/{{name}}_location.md
    @echo "**Location:** Type and general description" >> content/drafts/{{name}}_location.md
    @echo "" >> content/drafts/{{name}}_location.md
    @echo "**Architecture/Geography:** Physical details and layout" >> content/drafts/{{name}}_location.md
    @echo "" >> content/drafts/{{name}}_location.md
    @echo "**Atmosphere:** Mood, feeling, and ambiance of the place" >> content/drafts/{{name}}_location.md
    @echo "" >> content/drafts/{{name}}_location.md
    @echo "**Notable Features:**" >> content/drafts/{{name}}_location.md
    @echo "- Important areas or landmarks" >> content/drafts/{{name}}_location.md
    @echo "- Hidden secrets or special properties" >> content/drafts/{{name}}_location.md
    @echo "" >> content/drafts/{{name}}_location.md
    @echo "**Significance:** Role in the story and why it matters" >> content/drafts/{{name}}_location.md
    @echo "✅ Created: content/drafts/{{name}}_location.md"

new-scene name:
    @echo "🎬 Creating scene template: {{name}}"
    @mkdir -p content/drafts
    @echo "# Scene: {{name}}" > content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "**Scene:** Brief summary of what happens" >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "**Setting:** Where and when this takes place" >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "**POV:** Point of view character" >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "**Mood:** Emotional tone and atmosphere" >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "## Content" >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "Write your scene content here..." >> content/drafts/{{name}}_scene.md
    @echo "" >> content/drafts/{{name}}_scene.md
    @echo "## Notes" >> content/drafts/{{name}}_scene.md
    @echo "- Important plot points" >> content/drafts/{{name}}_scene.md
    @echo "- Character development" >> content/drafts/{{name}}_scene.md
    @echo "- Foreshadowing or connections" >> content/drafts/{{name}}_scene.md
    @echo "✅ Created: content/drafts/{{name}}_scene.md"

list-drafts:
    @echo "📋 Draft files:"
    @find content/drafts -name "*.md" 2>/dev/null | sort || echo "No draft files found"

edit file:
    @echo "✏️  Opening {{file}}..."
    @if [ -f "{{file}}" ]; then \
        open "{{file}}"; \
    elif [ -f "content/drafts/{{file}}" ]; then \
        open "content/drafts/{{file}}"; \
    elif [ -f "content/drafts/{{file}}.md" ]; then \
        open "content/drafts/{{file}}.md"; \
    else \
        echo "❌ File not found: {{file}}"; \
        echo "💡 Try: just list-drafts"; \
    fi

# Content management
finalize:
    @echo "📂 Processing all drafts and ingesting into Neo4j..."
    source writing_env/bin/activate && cd src && python organize_content.py --story "Your Story"

process file:
    @echo "📄 Processing: {{file}}"
    source writing_env/bin/activate && cd src && python organize_content.py --file "../{{file}}" --story "Your Story"

preview:
    @echo "👀 Preview: What would be organized"
    source writing_env/bin/activate && cd src && python organize_content.py --dry-run

status:
    @echo "📊 Content Summary:"
    @echo "=================="
    @echo "📝 Drafts: $(find content/drafts -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "👥 Characters: $(find content/characters -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "🌍 Locations: $(find content/locations -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "🎬 Scenes: $(find content/scenes -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "📚 Stories: $(find content/stories -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "⚡ Worldbuilding: $(find content/worldbuilding -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "🎭 Themes: $(find content/themes -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    @echo "📖 Research: $(find content/research -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"

# Querying commands
query:
    @echo "💬 Starting interactive writing assistant..."
    source writing_env/bin/activate && cd src && python writing_assistant.py

ask question:
    @echo "🤔 Asking: {{question}}"
    source writing_env/bin/activate && cd src && python -c "from writing_assistant import WritingAssistant; assistant = WritingAssistant(); assistant.ask('{{question}}'); assistant.db.close()"

stats:
    @echo "📈 Database Statistics:"
    @source writing_env/bin/activate && cd src && python -c "from neo4j_connector import WritingGraphDB; db = WritingGraphDB(); print('Connection test:', db.test_connection()); db.close()"

# System commands
test-db:
    @echo "🔌 Testing Neo4j connection..."
    source writing_env/bin/activate && cd src && python -c "from neo4j_connector import WritingGraphDB; db = WritingGraphDB(); print(db.test_connection()); db.close()"

reset-db:
    @echo "⚠️  WARNING: This will delete ALL data in the Neo4j database!"
    @echo "This action cannot be undone. Type 'DELETE' to confirm:"
    @read -p "Confirm: " confirm && [ "$$confirm" = "DELETE" ] && source writing_env/bin/activate && cd src && python -c "from neo4j_connector import WritingGraphDB; db = WritingGraphDB(); session = db.driver.session(); session.run('MATCH (n) DETACH DELETE n'); print('Database cleared'); db.close()" || echo "Cancelled"

backup:
    @echo "💾 Creating backup..."
    @mkdir -p backups
    @tar -czf "backups/content_backup_$(date +%Y%m%d_%H%M%S).tar.gz" content/
    @echo "✅ Backup created in backups/ directory"

export:
    @echo "📤 Exporting knowledge graph..."
    @mkdir -p exports
    @source writing_env/bin/activate && cd src && python -c "print('Export functionality needs to be implemented')"

# Quick recipes for common workflows
new-story story_name:
    @echo "📚 Starting new story: {{story_name}}"
    just new-draft "{{story_name}}_outline"
    just new-character "protagonist"
    just new-location "main_setting"
    @echo "✅ Created story starter files. Edit them and run 'just finalize' when ready."

writing-session:
    @echo "✍️  Starting writing session..."
    just status
    @echo ""
    @echo "💡 Quick commands:"
    @echo "  just new-draft 'name' - Start writing"
    @echo "  just finalize - Process drafts"  
    @echo "  just query - Ask questions"

# Development helpers (hidden from main menu)
_clean:
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -delete

_lint:
    source writing_env/bin/activate && python -m flake8 *.py --max-line-length=120