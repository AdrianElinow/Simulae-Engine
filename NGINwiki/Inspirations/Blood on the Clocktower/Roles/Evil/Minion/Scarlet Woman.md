[[Scarlet Woman]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Minion Roles]]
- Script: [[Trouble Brewing]]
- Role Type: Minion

## Ability Summary
If there are enough players alive and the Demon dies, you become the Demon.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.scarlet_woman",
  "name": "Scarlet Woman Ability",
  "requirements": [
    "Actor currently has the 'Scarlet Woman' role",
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
          "Subtype": "Scarlet Woman"
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
          "role": "Scarlet Woman",
          "ability_function": "If there are enough players alive and the Demon dies, you become the Demon.",
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
- [[Trouble Brewing]]
