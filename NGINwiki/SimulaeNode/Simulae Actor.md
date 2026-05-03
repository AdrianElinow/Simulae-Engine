Simulae Actor's are Sentient [[SimulaeNode]] entities that have agency over themselves, surroundings, and other sentient entities. 

They can interact with other sentient entities via the [[Socialization]] system, and can perform complex tasks based on their breakdown of these tasks into sequences of simpler subtasks via the [[Plan]] system


# Abilities

## Primitive Abilities

These 'primitive' [[Abilities]] are the basic abilities shared by all [[SimulaeNode/Simulae Actor]] nodes. 

The primitive abilities include the few explicitly implemented 'ability' scripts required to make the [[Step]]s actionable and executable in a [[Simulae]] engine.

| Action   | Description                                                                                       |
| -------- | ------------------------------------------------------------------------------------------------- |
| Goto     | Travel/Navigate to a target (either explicit or vague)                                            |
| Acquire  | Construct a sub-plan that ends with the target entity in the possession or ownership of the actor |
| Search   | The actor performs necessary actions in order to learn the location of a target                   |
| Take     | The actor adds the item to their [[Relations]]                                                    |
| Use      | The actor consumes the target                                                                     |
| Make     | The actor fabricates the target                                                                   |
| Interact | The actor triggers a target to perform an action                                                  |

# Structure

```json
"90f61883-0b73-11f1-8a69-8c1d96bb63bc": {
	"ID": "90f61883-0b73-11f1-8a69-8c1d96bb63bc",
	"References": {
		"Name": "Example NPC",
		"Gender": "Male",
		"LOC": "90f5a239-0b73-11f1-b996-8c1d96bb63bc"
	},
	"Nodetype": "POI",
	"Scales": {
		"Policy": {
			"Economy": [5,4],
			"Liberty": [3,0],
			"Class": [4,4],
			"Culture": [4,3],
			"Diplomacy": [3,8],
			"Militancy": [4,4],
			"Diversity": [3,2],
			"Secularity": [2,3],
			"Technology": [2,4],
			"Legality": [5,4],
			"Justice": [2,9],
			"Natural-Balance": [3,3],
			"Government": [3,2]
		},
		"Personality": {
			"Loyalty": [4,0],
			"Ambition": [1,2],
			"Empathy": [5,7],
			"Emotionality": [4,1],
			"Risk": [2,3],
			"Conscience": [3,4],
			"Conscientiousness": [2,8],
			"Curiosity": [4,0],
			"Trust": [3,3],
			"Resilience": [3,3],
			"Assertiveness": [3,5],
			"Conflict-Style": [3,1],
			"Humor": [3,6],
			"Adaptability": [4,9],
			"Attachment": [4,3],
			"Cognitive-Style": [3,0],
			"Cooperativeness": [4,1],
			"Social-Energy": [3,3]
		}
	},
	"Attributes": {
	"Age": 35,
		"Height": 1.8,
		"Weight": 69.19
	},
	"Relations": {
		"Contents": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"Components": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {...}
		},
		"Attachments": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"Adjacent": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"POI": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"PTY": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"LOC": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		},
		"OBJ": {
			"POI": {},
			"PTY": {},
			"LOC": {},
			"OBJ": {}
		}
	},
	"Checks": {...},
	"Abilities": {...},
	"Memory": {...}
},
```