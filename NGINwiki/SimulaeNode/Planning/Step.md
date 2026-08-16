
A step is an individual component of an [[SimulaeNode/Simulae Actor]]'s [[Plan]]

Types of Steps
- Linear
- Conditional
	- Branches off to other steps based on [[Simulae Condition]]s allowing for branching planning, backup plans, etc
- Promise
	- Steps that represent an un-planned step, serving as a promise or todo note that the step will be planned at some point, including under certain [[Simulae Condition]]. 
	- This serves as both an optimization measure as well as a representation of the real concept of re-evaluating one's plans on the fly or putting of planning until later.

### Step Statuses

Statuses:
- Promised
- Planned
- In Progress
- Completed
- Failed
- Aborted
- ...

Structure 

```json
Step: {
	type: "Linear | Conditional | Promise",
	plan: ...,
	parent: ...,
	status: ...,
	trigger_events: [ // [[Simulae Event]]s triggered when evaluating the step
		...
	],
	conditions: [ // [[Condition]]s required to evaluate the step
		...
	],
	children: [ // Steps that are triggered after the evaluation of the step
		...
	]
}
```
