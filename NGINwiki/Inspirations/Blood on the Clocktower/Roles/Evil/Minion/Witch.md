[[Witch]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Minion Roles]]
- Script: [[Sects and Violets]]
- Role Type: Minion

## Ability Summary
Each night, choose a player; if they nominate tomorrow, they die.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.witch",
  "name": "Witch Ability",
  "requirements": [
    "Actor currently has the 'Witch' role",
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
          "Subtype": "Witch"
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
          "role": "Witch",
          "ability_function": "Each night, choose a player; if they nominate tomorrow, they die.",
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

## Linked Roles
- [[Blood on the Clocktower Role]]
- [[Minion Roles]]
- [[Sects and Violets]]
