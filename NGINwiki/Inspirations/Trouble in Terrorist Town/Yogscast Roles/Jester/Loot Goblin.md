[[Loot Goblin]] is a Yogscast-used role in [[Trouble in Terrorist Town]].

- Team Classification: [[Yogscast Jester Roles|Jester]]
- Category Source: Yogscast TTT role taxonomy
- Vault Category: [[Yogscast Jester Roles|Jester]]

## Role Function
Fast, evasive jester role that drops loot on death and may win by surviving to round end.



## Simulae Ability ([[Abilities]])

```json
Ability = {
  "id": "ability.loot_goblin",
  "name": "Loot Goblin Ability",
  "requirements": [
    "Actor currently has the 'Loot Goblin' role",
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
          "Subtype": "Loot Goblin"
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
          "role": "Loot Goblin",
          "ability_function": "Fast, evasive jester role that drops loot on death and may win by surviving to round end.",
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

- Goal State: Satisfy Loot Goblin's personal jester-style victory trigger before standard team wins resolve.
- Action Sequence: Use the role ability to create the board-state and social-state required by that goal.
- Task Actions: Trigger role-ability [[Simulae Event]] outputs that advance this role's victory progress while blocking opposing victory paths.
- Completion Signal: Emit/observe terminal [[Simulae Event]] evidence that confirms the goal state is achieved.

## Related Pages
- [[Trouble in Terrorist Town]]
- [[Trouble in Terrorist Town Roles]]
- [[Yogscast Roles]]
