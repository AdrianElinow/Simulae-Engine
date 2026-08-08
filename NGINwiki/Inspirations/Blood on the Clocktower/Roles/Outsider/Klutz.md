[[Klutz]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Outsider Roles]]
- Script: [[Sects and Violets]]
- Role Type: Outsider

## Ability Summary
When you die, choose a player publicly; if they are evil, your team loses.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.klutz",
  "name": "Klutz Ability",
  "requirements": [
    "Actor currently has the 'Klutz' role",
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
          "Subtype": "Klutz"
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
          "role": "Klutz",
          "ability_function": "When you die, choose a player publicly; if they are evil, your team loses.",
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

- Goal State: If killed, make a public final choice that avoids immediate Good-team loss while still preserving a Good path to victory.
- Action Sequence: Use the role ability to create the board-state and social-state required by that goal.
- Task Actions: Trigger role-ability [[Simulae Event]] outputs that advance this role's victory progress while blocking opposing victory paths.
- Completion Signal: Emit/observe terminal [[Simulae Event]] evidence that confirms the goal state is achieved.

## Linked Roles
- [[Blood on the Clocktower Role]]
- [[Outsider Roles]]
- [[Sects and Violets]]
