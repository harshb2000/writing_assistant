# Writing Knowledge Graph Data Model

## Node Types

### Core Entities
- **Character**: People in your stories
- **Location**: Physical places, settings
- **Scene**: Individual scenes or chapters  
- **Story**: Complete stories or books
- **Theme**: Abstract concepts, themes, motifs
- **PlotPoint**: Key events, turning points
- **WorldElement**: World-building concepts (magic systems, cultures, etc.)

### Metadata Nodes
- **Tag**: General categorization
- **Timeline**: Temporal ordering
- **POV**: Point of view character for scenes

## Relationships

### Character Relationships
- Character -[KNOWS]-> Character
- Character -[RELATED_TO]-> Character (family, romantic, etc.)
- Character -[APPEARS_IN]-> Scene
- Character -[PROTAGONIST_OF]-> Story
- Character -[HAS_TRAIT]-> Tag

### Location Relationships  
- Location -[CONTAINS]-> Location (city contains buildings)
- Location -[SETTING_FOR]-> Scene
- Location -[PART_OF]-> Story
- Character -[LIVES_IN]-> Location

### Story Structure
- Scene -[PART_OF]-> Story
- Scene -[FOLLOWS]-> Scene (sequence)
- Scene -[TAKES_PLACE_IN]-> Location
- Scene -[INVOLVES]-> PlotPoint
- PlotPoint -[LEADS_TO]-> PlotPoint

### Thematic Connections
- Story -[EXPLORES]-> Theme
- Character -[EMBODIES]-> Theme
- Scene -[DEMONSTRATES]-> Theme

### Temporal
- Scene -[OCCURS_IN]-> Timeline
- PlotPoint -[HAPPENS_AT]-> Timeline

## Node Properties

### Character
- name: string
- description: text
- age: integer
- role: string (protagonist, antagonist, etc.)
- first_appearance: string (scene/story)

### Scene  
- title: string
- content: text (or file_path)
- word_count: integer
- pov_character: string
- summary: text
- status: string (draft, revised, final)

### Location
- name: string
- description: text
- type: string (city, building, room, etc.)
- significance: text

### Story
- title: string
- genre: string
- status: string
- summary: text
- word_count: integer

### PlotPoint
- title: string
- description: text
- importance: string (major, minor)
- type: string (conflict, resolution, twist, etc.)