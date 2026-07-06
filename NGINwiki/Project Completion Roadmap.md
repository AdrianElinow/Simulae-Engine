# Project Completion Roadmap

- [ ] Core Data Model: make nodes, relations, checks, references, abilities, and memory durable and queryable.
  - [ ] Relation search and filtering: support criteria-based lookup by IDs, names, references, checks, abilities, and relation data.
  - [ ] Save/load round-tripping: preserve a full world state across serialization without losing relations or memory.
  - [ ] Stable identity and cloning: keep copied nodes and reloaded worlds deterministic so identity does not drift.
  - [ ] Data-driven scale rules: move hard-coded policy and personality disposition logic into config where possible.

- [ ] Planning and Action Resolution: turn goals into executable behavior instead of leaving them as partial scaffolding.
  - [ ] GOAP task breakdown: decompose goals into step-by-step plans with valid fallback branches.
  - [ ] Need-driven prioritization: feed hunger, thirst, exhaustion, sickness, loneliness, and threat into one decision loop.
  - [ ] Action outcome handling: complete movement, acquisition, use, interaction, and environmental response results.
  - [ ] World-state propagation: apply action results back into the simulation so choices change the world.

- [ ] Socialization and Memory: let encounters create structured memories that affect later behavior.
  - [ ] Social event schema: finish `NGIN_Socialization` so prompts, appraisals, and responses are fully represented.
  - [ ] Memory event pipeline: convert social encounters into structured `MemoryEvent` records instead of ad hoc payloads.
  - [ ] Appraisal scoring: evaluate polarity, salience, threat, credibility, authority, and intent consistently.
  - [ ] Response ranking: make personality, policy, context, and conversation history influence the chosen response.
  - [ ] Claim and relationship updates: extract claims from events and update social relationships over time.

- [ ] World Simulation: make the campaign world act like a living system instead of a static map.
  - [ ] World generation: complete location, faction, and population generation so campaigns start in a coherent state.
  - [ ] Long-term consequences: carry world-state changes forward instead of limiting them to one scene.
  - [ ] Mission and contract resolution: let objectives resolve into campaign-level outcomes and side effects.
  - [ ] Dynamic event handling: expand pressure, scarcity, conflict, and escalation events so the world reacts.

- [ ] Gamemode Framework: keep the project content-first so new modes can be added without rewriting the engine.
  - [ ] Shared gamemode contract: define the minimum data and hooks every mode needs for roles, factions, and systems.
  - [ ] Wiki-first mode authoring: keep mode content in the wiki with light code glue instead of bespoke engine branches.
  - [ ] Mode-specific behavior hooks: support dedicated logic for social deduction, immersive sims, heists, survival, and investigation.
  - [ ] Content pack registration: make new mode packs plug in cleanly, including packs like Aneurism IV and Hitman: World of Assassination.
  - [ ] Mode regression coverage: keep each supported gamemode paired with tests that mirror the wiki contract.

- [ ] API, Client, and Persistence: make the simulation inspectable, restartable, and useful outside the terminal.
  - [ ] Import and export flows: save and restore world state, actors, and campaign progress cleanly.
  - [ ] Inspection endpoints: expose world, actor, plan, and memory state through the API for debugging and tooling.
  - [ ] Client state views: surface enough simulation detail in the client to make play and debugging practical.
  - [ ] Save versioning: add compatibility markers so older saves do not break immediately after schema changes.

- [ ] Testing and Verification: keep the engine honest as the missing systems come online.
  - [ ] Core model tests: cover node behavior, serialization, relations, and scale calculations.
  - [ ] Planning tests: verify the planning loop produces executable plans and valid fallbacks.
  - [ ] Socialization tests: cover appraisal, response selection, memory creation, and relationship drift.
  - [ ] World generation tests: validate location graphs, factions, populations, and generation invariants.
  - [ ] Gamemode tests: keep role inventories and interaction behavior in sync with each mode's wiki pages.
  - [ ] Wiki contract tests: confirm that documentation still matches the code paths it describes.

- [ ] Documentation and Content: keep the wiki as a real build guide instead of a loose note dump.
  - [ ] Wiki structure: organize pages by engine system, world system, and gamemode so the hierarchy stays navigable.
  - [ ] Page templates: add reusable templates for roles, factions, systems, and gamemodes.
  - [ ] Cross-links: keep the main entry pages linked to `[[Simulae]]`, `[[SimulaeNode]]`, `[[World Generator]]`, `[[Gamemodes]]`, and `[[Game Engine Integrations]]`.
  - [ ] Implementation notes: record design decisions as they settle so future changes do not have to rediscover them.
  - [ ] Mode documentation: document each supported gamemode with its own mechanics, cast, and system expectations.
  - [ ] Immersive sim reference library: add benchmark pages for the games that define the target design space.
    - [ ] Deus Ex: support hub missions, augmentations, hacking, dialogue choices, and multiple solutions to one objective.
      - [ ] Branching hub questing: let players pick up optional objectives and resolve them in different orders.
      - [ ] Augmentation builds: let characters unlock traversal, combat, and social access through build choices.
      - [ ] Hacking and access control: let terminals, keypads, and security systems be bypassed through skill or tools.
    - [ ] Dishonored: support supernatural traversal, chaos-driven consequences, and lethal versus nonlethal routes.
      - [ ] Power combinations: let movement, control, and combat powers chain together into emergent solutions.
      - [ ] Chaos tracking: let violence and bodies alter mission difficulty, dialogue, and endings.
      - [ ] Mission-contained sandboxes: let each level stay discrete while still reacting to prior choices.
    - [ ] Prey (2017): support continuous station exploration, scavenging, and alien-powered improvisation.
      - [ ] Interconnected spaces: let the player backtrack through a world that changes as skills unlock.
      - [ ] Environmental traversal: let tools like climbable foam, vents, and shortcuts create new routes.
      - [ ] Crafting and recycling: let loot be converted into resources instead of being only vendor trash.
    - [ ] System Shock 2: support audio-log storytelling, class-based starts, hacking, psionics, and survival pressure.
      - [ ] Environmental exposition: let logs and world artifacts carry story without forcing constant dialogue scenes.
      - [ ] Build identity: let starting role and skill investment matter throughout the run.
      - [ ] Resource strain: let ammo, healing, inventory, and station systems create sustained tension.
    - [ ] Weird West: support chapter-based campaigns, carry-over state, and faction response.
      - [ ] Multi-protagonist structure: let one character's chapter reshape the world for the next.
      - [ ] Persistent actions: let deaths, fires, loot, and faction conflicts remain true after the fact.
      - [ ] Reactive frontier simulation: let the world respond physically and socially to violence.
    - [ ] Shadows of Doubt: support procedural cities, routine-driven citizens, and evidence-based investigation.
      - [ ] Procedural population: let cities, citizens, and cases be generated with stable identities and routines.
      - [ ] Deduction tools: let players collect, connect, and test evidence instead of following a fixed script.
      - [ ] Wrong-answer fallout: let false accusations and missed clues have real campaign consequences.

- [ ] Release Readiness: finish the project only when the full loop works end-to-end.
  - [ ] End-to-end world run: generate, simulate, save, load, and resume a world without manual repair.
  - [ ] Cross-session continuity: keep actor memory, plans, and relationships intact across reloads.
  - [ ] No placeholder stubs: remove early returns and TODO-only code paths from the shipped surface.
  - [ ] Wiki-code parity: ensure the wiki, tests, and runtime behavior all describe the same system.
