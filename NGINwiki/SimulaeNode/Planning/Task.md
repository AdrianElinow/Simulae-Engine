A task is an individual unit of a [[Plan]] or a standalone action to be performed by a [[SimulaeNode/Simulae Actor]]

A task has a few important components:
- A goal state to be achieved
- An action (or sequence of actions) that must be performed to achieve the goal-state

```json
Task = {
	"id": "...",
	"type": "command|quest|contract|objective",
	"parent": "...",
	"issuance": (Event),
	"status": "...",
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
- Basic Actions (Video Game controls)
	- Movement
		- Walk
		- Crouch
		- Crawl
		- Run (spring) 
		- Jump
		- Dodge? (dash)
		- Lean (left/right)
		- Vault (over, up)
		- Climb (ladder / hand-holds / rope)
	- Combat
		- shoot / reload / aim / change use-mode (alternate aim or fire mode, underbarrel, etc)
		- Swing (sword/axe/etc), block, parry, etc
		- Unarmed / Martial art
			- Strike (punch, kick, etc)
			- Grapple
			- ...
	- Use (& select) power / special ability
	- Item
		- Interact / use
		- drop
		- Equip
PTY (Group/Team command)
- Ping / Report
- Order formation
- Order mode (walk vs. run / stealth vs. weapons-free / ranged vs melee / etc)
- Issue plan (to perform task)
FAC

