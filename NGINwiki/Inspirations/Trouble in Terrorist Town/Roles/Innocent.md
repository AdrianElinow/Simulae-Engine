[[Innocent]] is a core Good-side role in [[Trouble in Terrorist Town]].

- Team: Innocent
- Goal: Eliminate all [[Traitor]] players.
- Information Access: No automatic role-reveal tools.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.innocent",
  "name": "Innocent Ability",
  "requirements": [
    "Actor currently has the 'Innocent' role",
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
          "Subtype": "Innocent"
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
          "role": "Innocent",
          "ability_function": "Eliminate all [[Traitor]] players.",
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

## Typical Social Behavior
- Build trust networks with other survivors.
- Share suspicions and defend confirmed evidence from [[Detective]] reports.

## Linked Roles
- [[Trouble in Terrorist Town Roles]]
- [[Detective]]
- [[Traitor]]
