[[Goon]] is a [[Blood on the Clocktower Role]] in [[Blood on the Clocktower]].

- Team: [[Outsider Roles]]
- Script: [[Bad Moon Rising]]
- Role Type: Outsider

## Ability Summary
Each night, the first player to choose you with an ability is drunk until dusk, and you become their alignment.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.goon",
  "name": "Goon Ability",
  "requirements": [
    "Actor currently has the 'Goon' role",
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
          "Subtype": "Goon"
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
          "role": "Goon",
          "ability_function": "Each night, the first player to choose you with an ability is drunk until dusk, and you become their alignment.",
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
- [[Outsider Roles]]
- [[Bad Moon Rising]]
