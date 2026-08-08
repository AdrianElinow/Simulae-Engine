[[Traitor]] is a hidden Evil-side role in [[Trouble in Terrorist Town]].

- Team: Traitor
- Goal: Eliminate all non-traitor players.
- Information Access: Knows allied traitors and uses covert tools.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.traitor",
  "name": "Traitor Ability",
  "requirements": [
    "Actor currently has the 'Traitor' role",
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
          "Subtype": "Traitor"
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
          "role": "Traitor",
          "ability_function": "Eliminate all non-traitor players.",
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
- Blend into normal [[Innocent]] discussion.
- Create misinformation and redirect suspicion.
- Remove high-value targets such as [[Detective]].

## Linked Roles
- [[Trouble in Terrorist Town Roles]]
- [[Innocent]]
- [[Detective]]
