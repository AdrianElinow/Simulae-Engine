[[Minstrel]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Townsfolk]]
- Script: [[Bad Moon Rising]]
- Role Type: Townsfolk

## Ability Summary
When a Minion dies by execution, most players become drunk until dusk the next day.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.minstrel",
  "name": "Minstrel Ability",
  "requirements": [
    "Actor currently has the 'Minstrel' role",
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
          "Subtype": "Minstrel"
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
          "role": "Minstrel",
          "ability_function": "When a Minion dies by execution, most players become drunk until dusk the next day.",
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
- [[Townsfolk]]
- [[Bad Moon Rising]]
