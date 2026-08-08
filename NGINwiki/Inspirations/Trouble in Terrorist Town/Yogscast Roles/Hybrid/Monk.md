[[Monk]] is a Yogscast-used role in [[Trouble in Terrorist Town]].

- Team Classification: [[Yogscast Innocent Roles|Innocent]], [[Yogscast Traitor Roles|Traitor]]
- Category Source: Yogscast TTT role taxonomy
- Vault Category: [[Yogscast Hybrid Roles|Hybrid]]

## Role Function
Religious communication role; in Yogscast variants this label is used for both innocent and traitor-side outcomes.



## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.monk",
  "name": "Monk Ability",
  "requirements": [
    "Actor currently has the 'Monk' role",
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
          "Subtype": "Monk"
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
          "role": "Monk",
          "ability_function": "Religious communication role; in Yogscast variants this label is used for both innocent and traitor-side outcomes.",
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

- Goal State: Resolve Monk's dual-alignment objective by selecting and executing the winning side-path for the current round state.
- Action Sequence: Use the role ability to create the board-state and social-state required by that goal.
- Task Actions: Trigger role-ability [[Simulae Event]] outputs that advance this role's victory progress while blocking opposing victory paths.
- Completion Signal: Emit/observe terminal [[Simulae Event]] evidence that confirms the goal state is achieved.

## Related Pages
- [[Trouble in Terrorist Town]]
- [[Trouble in Terrorist Town Roles]]
- [[Yogscast Roles]]
