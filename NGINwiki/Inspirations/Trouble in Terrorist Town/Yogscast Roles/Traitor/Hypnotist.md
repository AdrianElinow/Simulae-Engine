[[Hypnotist]] is a Yogscast-used role in [[Trouble in Terrorist Town]].

- Team Classification: [[Yogscast Traitor Roles|Traitor]]
- Category Source: Yogscast TTT role taxonomy
- Vault Category: [[Yogscast Traitor Roles|Traitor]]

## Role Function
Traitor support that revives dead players as traitor-aligned allies.



## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.hypnotist",
  "name": "Hypnotist Ability",
  "requirements": [
    "Actor currently has the 'Hypnotist' role",
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
          "Subtype": "Hypnotist"
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
          "role": "Hypnotist",
          "ability_function": "Traitor support that revives dead players as traitor-aligned allies.",
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

## Related Pages
- [[Trouble in Terrorist Town]]
- [[Trouble in Terrorist Town Roles]]
- [[Yogscast Roles]]
