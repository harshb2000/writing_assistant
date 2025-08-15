// Sample Cypher Queries for Writing Knowledge Graph

// 1. Create sample data
CREATE (alice:Character {name: "Alice", age: 25, role: "protagonist"})
CREATE (bob:Character {name: "Bob", age: 30, role: "antagonist"})
CREATE (cafe:Location {name: "Corner Cafe", type: "building"})
CREATE (scene1:Scene {title: "The Meeting", summary: "Alice and Bob meet for the first time"})
CREATE (story1:Story {title: "My First Story", genre: "drama", status: "draft"})

// Create relationships
CREATE (alice)-[:APPEARS_IN]->(scene1)
CREATE (bob)-[:APPEARS_IN]->(scene1)
CREATE (scene1)-[:TAKES_PLACE_IN]->(cafe)
CREATE (scene1)-[:PART_OF]->(story1)
CREATE (alice)-[:KNOWS]->(bob)

// 2. Find all characters in a story
MATCH (c:Character)-[:APPEARS_IN]->(s:Scene)-[:PART_OF]->(story:Story {title: "My First Story"})
RETURN DISTINCT c.name

// 3. Find all scenes where two characters interact
MATCH (c1:Character {name: "Alice"})-[:APPEARS_IN]->(scene:Scene)<-[:APPEARS_IN]-(c2:Character {name: "Bob"})
RETURN scene.title, scene.summary

// 4. Find all locations in a story
MATCH (loc:Location)<-[:TAKES_PLACE_IN]-(scene:Scene)-[:PART_OF]->(story:Story {title: "My First Story"})
RETURN DISTINCT loc.name, loc.type

// 5. Character relationship network
MATCH (c1:Character)-[r:KNOWS|RELATED_TO]-(c2:Character)
RETURN c1.name, type(r), c2.name

// 6. Scene sequence in a story
MATCH (s:Scene)-[:PART_OF]->(story:Story {title: "My First Story"})
OPTIONAL MATCH (s)-[:FOLLOWS]->(next:Scene)
RETURN s.title, next.title
ORDER BY s.title

// 7. Find orphaned characters (not in any scene)
MATCH (c:Character)
WHERE NOT (c)-[:APPEARS_IN]->(:Scene)
RETURN c.name

// 8. Complex query: Find characters connected through locations
MATCH (c1:Character)-[:APPEARS_IN]->(scene1:Scene)-[:TAKES_PLACE_IN]->(loc:Location)
<-[:TAKES_PLACE_IN]-(scene2:Scene)<-[:APPEARS_IN]-(c2:Character)
WHERE c1 <> c2
RETURN c1.name, loc.name, c2.name

// 9. Theme analysis
MATCH (story:Story)-[:EXPLORES]->(theme:Theme)<-[:EMBODIES]-(character:Character)
RETURN story.title, theme.name, collect(character.name) as characters_embodying_theme