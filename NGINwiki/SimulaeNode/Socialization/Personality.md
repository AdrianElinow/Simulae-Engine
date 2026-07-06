The Personality [[Scales]] are a series of axes that attempt to approximate the many aspects of a human psyche in a data structure through which can be calculated appropriate reactions, responses, and priorities of a given [[SimulaeNode/Simulae Actor]]'s interactions in the [[Socialization]]

## Scales

| Personality Factor | Low Extreme   |             |               | Neutral / Average |               |                  | High Extreme      |
| ------------------ | ------------- | ----------- | ------------- | ----------------- | ------------- | ---------------- | ----------------- |
| Agreeableness      | Hostile       | Unfriendly  | Aloof         | Neutral           | Friendly      | Agreeable        | Compassionate     |
| Extroversion       | Reclusive     | Withdrawn   | Quiet         | Neutral           | Sociable      | Gregarious       | Attention-seeking |
| Contientiousness   | Negligent     | Careless    | Irresponsible | Neutral           | Reliable      | Conscientious    | Perfectionist     |
| Neuroticism        | Cold          | Stable      | Calm          | Neutral           | Sensitive     | Anxious          | Fragile           |
| Openness           | Closed-Minded | Traditional | Conventional  | Inquisitive       | Investigative | Obsessive        |                   |
| Loyalty            | Rebellious    | Subversive  | Independent   | Indifferent       | Conformist    | Loyal            | Zealous           |
| Ambition           | Selfless      | Apathetic   | Unmotivated   | Steady            | Ambitious     | Selfish          | Messianic         |
| Empathy            | Sadistic      | Callous     | Apathetic     | Neutral           | Sympathetic   | Idealistic       | Virtuous          |
| Conscience         | Immoral       | Amoral      | Rational      | Pragmatic         | Ethical       | Idealistic       | Virtuous          |
| Trust              | Paranoid      | Distrustful | Skeptical     | Neutral           | Unsuspicious  | Trusting         | Gullible          |
| Humor              | Humorless     | Dry         | Reserved      | Neutral           | Witty         | Joker            | Clownish          |
| Attachment         | Avoidant      | Detached    | Reserved      | Neutral           | Affectionate  | Anxious          | Obsessive         |
| Cognitive-Style    | Concrete      | Practical   | Analytic      | Balanced          | Abstract      | Systems-Oriented | Visionary         |




## Diagram

![[personality-scales-diagram.png]]
```mermaid

radar-beta
	title Political Scales
	
	axis loy["Loyalty"]
	axis amb["Ambition"]
	axis emp["Empathy"]
	axis emo["Emotionality"]
	axis risk["Risk"]
	axis mor["Conscience"]
	axis cons["Conscientiousness"]
	axis cur["Curiosity"]
	axis trust["Trust"]
	axis res["Resilience"]
	axis asrt["Assertiveness"]
	axis confl["Conflict-Style"]
	axis humor["Humor"]
	axis adapt["Adaptability"]
	axis atch["Attachment"]
	axis cog["Cognitive-Style"]
	axis coop["Cooperativeness"]
	axis soc["Social-Energy"]
	  
	curve NPC{1,2,3,4,5,6,7,1,2,3,4,5,6,7,1,2,3,4}
	graticule polygon
	max 7
	min 0
```
