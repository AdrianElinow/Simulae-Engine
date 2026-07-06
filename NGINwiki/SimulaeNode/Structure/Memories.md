An entity's 'Memories' structure is a auditable-collection of the events experienced by the entity and the information and emotional-impact associated to the event from the entity's perspective. 

For the most part this system applies primarily to sentient entities such as individual persons or groups such as factions which can be simplified to have a 'collective' memory.

The [[Simulae Event]]s they accumulate as experiences can also be sub-classed as [[Social Event]]s by engaging in the realm of the [[Socialization]] system

> Ex: Memory structure:
```json
Memory = {
	'POI': {...},
	'FAC': {...},
	'LOC': {...},
	'OBJ': {...},
	
}
```
## Experiences 

An entity acquires experiences either by directly witnessing an [[Simulae Event]] occur or by having its details relayed to them piece by piece.

The witnessing [[SimulaeNode/Simulae Actor]] gets some of the information from this [[Simulae Effect]] and is committed to their short-term memory, and if significant enough, can also be committed directly to long-term memory.


The memory system allows NPCs to:
- Retain information about their own experiences (autobiographical memory)
- Remember specific interactions and encounters (episodic memory)
- Maintain factual knowledge about the world (semantic memory)
- Track relationships and emotional responses (relationship memory)
- Recall skills and procedures (procedural memory)
- Maintain secrets and hidden knowledge (secret memory)
- Form beliefs and opinions from accumulated experience (narrative memory)

## Memory Types
- Autobiographical
- Episodic
- Semantic
- Episodic-Relationship
- Secret
- Procedural
- Emotional-Associative
- Narrative-Belief
### Individual Memory Structure

```json
{
	"type": ...,
	"known_by": [node_id, ...],
	"subject": [node_id, ...],
	"object": [node_id, ...],
	"facts": [...],
	"source": [...],
	...
}
```

| Property                 | Datatype                                                     | Description                                                                                                                                          |
| ------------------------ | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Type                     | String                                                       | Type of memory                                                                                                                                       |
| `known_by`               | list of [[SimulaeNode]] IDs                                  | Other [[SimulaeNode]] that the NPC is aware of who also knows the same information.                                                                  |
| `subject`                | list of [[SimulaeNode]] IDs                                  |                                                                                                                                                      |
| `object`                 | list of [[SimulaeNode]] IDs                                  |                                                                                                                                                      |
| `fact`                   | list of [[Fact]]s                                            |                                                                                                                                                      |
| `source`                 | list of information sources                                  | Either `node_id`s for [[SimulaeNode/Simulae Actor]]s who have provided the information or `experienced` to indicate that the information is first-hand observed. |
| `timestamp`              | canonical timestamp when this memory was first instantiated. |                                                                                                                                                      |
| `last_updated_timestamp` | canonical timestamp when this memory was last updated.       |                                                                                                                                                      |
|                          |                                                              |                                                                                                                                                      |
|                          |                                                              |                                                                                                                                                      |
## Memory Dynamics

### Reinforcement
Memories become stronger with reinforcement:
- Each recall increases `reinforcement_count`
- High reinforcement makes memories easier to access
- Frequently used memories have higher `recall_ease`

### Forgetting
Memories fade with time and lack of reinforcement:
- Old encounters may shift from vivid to hazy
- Details become fragmentary without reinforcement
- Eventually may be lost entirely

### Reconsolidation
When a memory is recalled, it can be updated:
- New information can be integrated
- Interpretations can change based on new context
- Emotional weight can shift with player actions

### Conflict Resolution
When new memories contradict old ones:
- NPC must reconcile the contradiction
- May result in belief revision
- Trust adjustments for relationships

## Implementation Notes

### Query Patterns
Memory should support these types of queries:
- "What do I know about [person]?"
- "Have I met this person before?"
- "What happened the last time I was in [location]?"
- "What do I believe about [topic]?"
- "What's my relationship with [faction]?"

### AI Integration
For AI-driven NPCs, memory should:
- Inform decision-making (what does the NPC know about options?)
- Generate dialogue (reference shared history)
- Determine initial reactions (affinity/trust scores)
- Create behavioral consistency (personality + memory = predictable patterns)

### Player Integration
For game systems, memory should:
- Track player interactions for consistency
- Allow NPCs to reference prior player actions
- Enable reputation mechanics (what does this NPC know about the player?)
- Support quest hooks (what does this NPC need or know about quests?)

## Memory Limits

### Storage Capacity
NPCs may have memory limits:
- Most recent memories are vivid
- Very old memories become hazy
- Storage capacity increases with Intelligence/Wisdom
- Emotional significance prevents deletion

### Recall Speed
Memory retrieval takes time:
- Automatic recall: immediate (reinforced memories)
- Easy recall: quick (well-indexed, frequently used)
- Difficult recall: requires thinking/conversation (old, poorly indexed)
- Suppressed recall: blocked by trauma or intentional suppression

## Future Development

The memory system could extend to:
- **Spatial memory**: Mental maps of locations
- **Temporal memory**: Understanding of sequences and causality
- **Counterfactual memory**: What-if scenarios and predicted outcomes
- **Collective memory**: Shared knowledge with other NPCs
- **False memories**: Deliberately implanted or naturally occurring false recollections
- **Memory dreams**: Consolidation of memories during rest
