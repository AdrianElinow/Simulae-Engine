A task is an individual unit of a [[Plan]] or a standalone action to be performed by a [[Simulae Actor]]

A task has a few important components:
- A goal state to be achieved
- An action (or sequence of actions) that must be performed to achieve the goal-state

```json
Task = {
	"id": "...",
	"type": "command|quest|contract|objective",
	"parent": "...",
	"issuance": (Event),
	"status": "..."
	"success_conditions": [...],
	"fail_conditions": [...],
	"success_outcomes": [...],
	"fail_outcomes": [...],
	"side_effects": {...},
	"deadline": (Timestamp),
}
```



## Primitives

Primitive tasks are the basic actions an NPC will employ during the course of their plan execution

These primitives relate to other [[SimulaeNode]] entities 
- Change location (movement)
- 


LOC
- change location 
- change ownership
OBJ
- change ownership
- change relation
	- acquire (becomes relation of another item)
	- modify (components)
	- deconstruct (components)
		- at workstation or ability
	- adorn (accessories)
		- 
	- construct (craft -> becomes other item component)
		- at workstation or ability
	- 
POI
PTY
FAC



| Action   | Description                                                                                       |
| -------- | ------------------------------------------------------------------------------------------------- |
| Goto     | Travel/Navigate to a target (either explicit or vague)                                            |
| Acquire  | Construct a sub-plan that ends with the target entity in the possession or ownership of the actor |
| Search   | The actor performs necessary actions in order to learn the location of a target                   |
| Take     | The actor adds the item to their [[Relations]]                                                    |
| Use      | The actor consumes the target                                                                     |
| Make     | The actor fabricates the target                                                                   |
| Interact | The actor triggers a target to perform an action                                                  |
