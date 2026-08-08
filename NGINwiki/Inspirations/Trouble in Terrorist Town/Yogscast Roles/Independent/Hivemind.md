[[Hivemind]] is a Yogscast-used role in [[Trouble in Terrorist Town]].

- Team Classification: [[Yogscast Independent Roles|Independent]]
- Category Source: Yogscast TTT role taxonomy
- Vault Category: [[Yogscast Independent Roles|Independent]]

## Role Function
Independent role with shared-state style mechanics that reward coordinated pressure across fights.



## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.hivemind",
  "name": "Hivemind Ability",
  "requirements": [
    "Actor currently has the 'Hivemind' role",
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
          "Subtype": "Hivemind"
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
          "role": "Hivemind",
          "ability_function": "Independent role with shared-state style mechanics that reward coordinated pressure across fights.",
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

- Goal State: Reach Hivemind's independent victory state (survival/elimination/conversion objective) without relying on team victory.
- Action Sequence: Use the role ability to create the board-state and social-state required by that goal.
- Task Actions: Trigger role-ability [[Simulae Event]] outputs that advance this role's victory progress while blocking opposing victory paths.
- Completion Signal: Emit/observe terminal [[Simulae Event]] evidence that confirms the goal state is achieved.

## Related Pages
- [[Trouble in Terrorist Town]]
- [[Trouble in Terrorist Town Roles]]
- [[Yogscast Roles]]
