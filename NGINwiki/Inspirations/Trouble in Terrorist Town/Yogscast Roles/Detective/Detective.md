[[Detective]] is a Yogscast-used role in [[Trouble in Terrorist Town]].

- Team Classification: [[Yogscast Detective Roles|Detective]]
- Category Source: Yogscast TTT role taxonomy
- Vault Category: [[Yogscast Detective Roles|Detective]]

## Role Function
Investigative leader role with access to detective equipment and evidence-based team guidance.

## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.detective",
  "name": "Detective Ability",
  "requirements": [
    "Actor currently has the 'Detective' role",
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
          "Subtype": "Detective"
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
          "role": "Detective",
          "ability_function": "Investigative leader role with access to detective equipment and evidence-based team guidance.",
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
