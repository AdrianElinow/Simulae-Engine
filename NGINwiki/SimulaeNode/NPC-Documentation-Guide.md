# NPC Documentation Guide

This guide explains how to use the [NPC-Template.md](NPC-Article-Template.md) structure for creating comprehensive NPC documents within the Simulae framework.

## Overview

The NPC template is organized into functional sections that align with the [[SimulaeNode]] and [[SimulaeNode/Simulae Actor]] frameworks:

- **Identity**: Basic information and physical appearance
- **Scales & Personality**: Personality and policy scales for behavioral consistency
- **Background**: History, motivations, and beliefs
- **Relations**: Connections to other entities
- **Abilities & Skills**: Capabilities and competencies
- **Attributes**: Core numerical characteristics
- **Socialization**: Communication and interaction patterns
- **Interactions**: History and relationship tracking

## Section Guidance

### Identity
Fill in basic biographical information and physical characteristics. This section helps NPCs be visually and conceptually distinct.

- Keep physical descriptions vivid but concise
- Use the Profession/Title to quickly convey social position
- Faction Affiliation should link to a [[Faction]] document

### Scales & Personality
These scales define behavioral tendencies and should be used for **AI generation consistency** and **roleplay decisions**.

- Position scales as a spectrum: indicate where the NPC falls rather than filling every position
- Personality scales influence how NPCs make decisions and interact
- Policy scales drive political stances and faction alignment
- Use these when generating dialogue or determining NPC reactions

### Background
Create a compelling narrative history:

- Core Beliefs & Motivations explains *why* they act as they do
- Secrets provide tension and plot hooks
- Fears reveal vulnerability and pressure points

### Relations
Use this section for the [[Relations]] component of the SimulaeNode:

- Explicitly track relationship types (family, professional, romantic, enemy)
- Include status information for dynamic tracking
- Favor/Debt status enables quest generation

### Abilities & Skills
Document what this NPC can actually do:

- Combat Rating helps determine encounter difficulty
- Special abilities are derived from their faction, background, or training
- Weaknesses create vulnerability and story opportunities

### Attributes
Use numeric or descriptive scales consistent with your system:

- Can be simplified to 3-5 core attributes
- Provides hard numbers for mechanics/encounters
- Context notes help explain why they have certain values

### Socialization
This integrates directly with the [[Socialization]] system:

- Speech patterns and mannerisms provide roleplay guidance
- Interaction patterns reference the core interaction types (INFORM, INQUIRE, INFLUENCE, etc.)
- Body language affects non-verbal "sizing up" mechanics
- Reputation affects initial encounter dispositions

### Interaction History
Tracks the evolving relationship with the player:

- Update this table as encounters occur
- Affinity and Trust levels determine future interactions
- Debt/Favor status creates hooks for quests and obligations

## Creating New NPCs

### Minimal NPC (Quick Reference)
For minor NPCs, complete at minimum:
- Identity (basics only)
- Profession/Title
- One Personality Scale (Core trait)
- Communication Style
- One or two paragraph Background

### Standard NPC (Full Documentation)
For NPCs the player will interact with multiple times:
- Complete all sections except optional subsections
- Prioritize Relations and Socialization
- Include 2-3 plot hooks

### Important NPC (Comprehensive)
For faction leaders, antagonists, or major plot characters:
- Complete all sections with detail
- Include full Background narrative
- Document all Relations thoroughly
- Include complete Interaction History table
- Add Development Notes tracking arc progression

## Integration with Other Systems

### With SimulaeNode
The template maps to SimulaeNode components:
- **References**: Identity, Background
- **Relations**: Relations section
- **Attributes**: Attributes section and scale positions
- **Checks**: Checks section
- **Abilities**: Abilities & Skills section

### With Socialization System
Use scale positions and communication patterns to:
- Determine initial NPC stance toward player
- Generate appropriate dialogue options
- React to player actions based on personality scales
- Calculate persuasion/intimidation difficulty

### With Factions
- Link NPCs to factions via Faction Affiliation
- Use Policy Scales to show faction alignment
- Track faction rank or standing
- Show intra-faction relationships via Relations

## Tips for Consistency

1. **Use the Scales Strategically**: You don't need to fill every scale, but those you do should inform behavior
2. **Keep Motivations Clear**: The clearer the "why", the easier to roleplay consistently
3. **Create Contrasts**: Mix scales to create interesting NPCs (loyal but amoral, ambitious but risk-averse)
4. **Link Relations**: NPCs should have connections to other NPCs, creating a web of relationships
5. **Update Regularly**: Mark encounter dates and update Affinity/Trust as the story progresses
6. **Use Secrets**: Hidden information creates roleplay tension and revelation opportunities

## Example: Quick NPC Walkthrough

**Tavern Barkeep** (Minimal)
- Name, Age, Appearance (1-2 lines)
- Profession: Tavern Keeper for [Faction]
- Personality: Friendly, Observant, Risk-Averse
- Communication: Casual, Warm, gossip-focused
- Background: (1 paragraph about their life)
- Plot Hook: Information broker for local factions

**Faction Captain** (Standard)
- Complete all Identity sections
- Position on relevant Personality and Policy scales
- Full Background including rise to rank
- Relations to other faction members and rivals
- Combat abilities and command skills
- Known reputation and rumors
- Current goals and conflicts

**Antagonist** (Comprehensive)
- Everything above plus:
- Detailed enemy relationships
- Complete Interaction History framework
- Development arc notes
- Multiple plot connections
- Personality contradictions that create depth

## File Naming Convention

When creating individual NPC files:
- Use format: `[LastName]-[FirstName].md` or `[Title]-[Name].md`
- Examples: `Blackthorn-Mara.md`, `Captain-Vex.md`, `The-Merchant-Krell.md`
- Organize NPC files in a `SimulaeNode/Characters/` or `NPCs/` subdirectory

## Linking to Other Documents

Use wiki-style links (double brackets) to connect:
- NPCs to Factions: `[[Faction Name]]`
- NPCs to Locations: `[[Location Name]]`
- NPCs to Events: `[[Event Name]]`
- NPCs to Quests: `[[Quest Name]]`
- NPCs to other NPCs: `[[Character Name]]`

This creates a network of interconnected documentation for easy navigation and relationship tracking.
