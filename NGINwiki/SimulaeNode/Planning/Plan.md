A [[Simulae]] Plan is a sequence of simple [[Step]]s which can be performed programatically in pursuance of a end-goal state. 
These plans can be imagined as processes in a computer's operating system, which can be prioritized, scheduled, and can trigger other plans to be evaluated.

## Primitive Plans

Primitive plans are typically the extent of most NPCs AI in video games. These typically involve chains of basic [[Step]]s.

Think of an NPC going about a daily schedule:
1. Wake up
2. Go get a piece of food for breakfast
3. Go to their place of occupation
	1. Perform some basic animations
4. Go to a place of relaxation
5. Return home
6. Sleep
- Action/Reaction to occasional spontaneous events
	- Greeting a nearby NPC with a short scripted exchange.
	- Being interrupted by a player or hostile NPCs

## Social Plans

Social plans are more dynamic socialization plans in furtherance of an individual's goals, typically as part of a larger more general personal plan.

### Relationship Plans

An actor [[SimulaeNode]] will have tasks and plans to support their social relationships

Types of relationship plots
- Familial
	- Ancestors
	- Siblings
	- Descendants
- Romantic
- Neutral
	- Stranger
	- Acquaintance 
	- Friend
	- Neighbor
	- Heard-of
- Positive
	- Friend
	- Companion
	- Ally
	- Asymetric
		- Admirer
		- Follower & Leader
		- Fan & Idol
- Romantic
	- By Stage
		- Interested
		- Flirting
		- Dating
		- Romantic
		- Amorous
		- Lover (Boyfriend / Girlfriend)
		- Engaged
		- Married
		- Divorced
		- Ex-Lover
- Occupational
	- Co-worker / Peer
	- Supervisor 
	- Subordinate
	- Competitor
- Negative
	- Rival
	- Enemy
	- Nemesis
	- Betrayer
- Systemic
	- Police
	- Lawmaker
	- Leader

These generalized plans will have custom balancing and tweaking in order to get them dialed in to feel realistic.

### Occupational Plans

An Actor [[SimulaeNode]] may have an 'occupation' (hobbies count as occupations where relevant, just at different priorities)

These occupations typically require the performance of tasks to maintain. 

## Strategic Plans

Strategic plans are high-level plans.

# Plan Evaluation

An actor needs to generate and evaluate plans and their validity.

The evaluation should include:
- An overall score
- 'Fitness' - how applicable this plan is to solve the problem
- Violations - Anticipated negative effects incurred by this plan
- Incentives - Anticipated positive effects incurred by this plan
- Pressures - Anticipated other effects incurred by this plan


