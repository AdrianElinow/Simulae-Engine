[[Vortox]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Demon]]
- Script: [[Sects and Violets]]
- Role Type: Demon

## Ability Summary
Each night, choose a player to die; Townsfolk information is false and good must execute daily.

## Simulae Abilities ([[Abilities]])

- At Night, choose a player to die (kill)
- Passively, invert all information
- Passively, win if no one is executed during the day

```json
Ability = {
  "id": "ability.vortox",
  "name": "Vortox Ability",
  "requirements": [
    "Actor currently has the 'Vortox' role",
    "Actor is in an eligible state to resolve role effects",
    "Round/gamemode timing allows this role to activate"
  ],
  "activation": "Action | Reaction | Passive (role-dependent)",
  "effects": [
    {
      "conditions": [
        "Check the role's timing window (day/night/on-death/on-vote/etc.)",
        "Check target validity, resource limits, and use-count constraints",
        "Check role-specific trigger state before resolving outcome"
      ],
      "event": {
        "Meta": {
          "namespace": "Gamemodes/Social Deduction",
          "version": "1.0"
        },
        "Event": {
          "Class": "Social | Physical | System",
          "Type": "RoleAbility",
          "Subtype": "Vortox"
        },
        "Timestamps": {
          "start_timestamp": "<resolution start>",
          "end_timestamp": "<resolution end>"
        },
        "SimulaeNodes": {
          "Location": "<role context location>",
          "Sources": ["<actor>"],
          "Targets": ["<selected target(s) or affected nodes>"],
          "Observers": ["<based on visibility/privacy rules>"]
        },
        "Payload": {
          "role": "Vortox",
          "ability_function": "Each night, choose a player to die; Townsfolk information is false and good must execute daily.",
          "outcome": "<resolved effect data>"
        },
        "Causality": {
          "cause_event_ids": ["<prior related event ids>"]
        }
      }
    }
  ]
}
```

This ability specification follows [[Abilities]] and emits [[Simulae Event]] structures when its effect conditions are satisfied.

## Task ([[Task]])

- Goal State: Maintain daily executions while surviving long enough for Evil to win under persistent false-information pressure.
- Action Sequence: Use the role ability to create the board-state and social-state required by that goal.
- Task Actions: Trigger role-ability [[Simulae Event]] outputs that advance this role's victory progress while blocking opposing victory paths.
- Completion Signal: Emit/observe terminal [[Simulae Event]] evidence that confirms the goal state is achieved.

## Linked Roles
- [[Blood on the Clocktower Role]]
- [[Demon]]
- [[Sects and Violets]]
