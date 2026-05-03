An appraisal is a given [[Simulae Actor]]s understanding / interpretation of a [[Social Event]]



```mermaid
sequenceDiagram
	actor Actor1
	actor Actor2
	Actor1 ->> Actor2: Prompt
	Actor2 ->> Actor2: Appraisal -> Responses -> Filtering
	
	Actor2 ->> Actor1: Response
	Actor1 ->> Actor1: Appraisal -> Responses -> Filtering
	Actor1 ->> Actor2: Response
	
	
```



```mermaid
flowchart TB
	subgraph actor1["Actor 1"]
		direction LR
		a1["Appraisal"]
		p1["Prompt"]
		rs1["Responses"]
		f1["Filtering"]
	end
	
	subgraph actor2["Actor 2"]
		direction LR
		a2["Appraisal"]
		rs2["Responses"]
		f2["Filtering"]
		p2["Prompt"]
	end
	
	p1 --> a2
	a2 --> rs2
	rs2 --> f2
	f2 --> p2
	p2 --> a1
	a1 --> rs1
	rs1 --> f1
	f1 --> p1
```








# Test Scenarios
By [[Social Event]] type

- Open
	- Nonverbal greeting (head nod)
	- Simple greeting ("hello")
	- formal greeting
- Close
	- nonverbal (head nod)
	- 
- Turn
- Topic
- Inform
- Inquire
- Stance
- Influence
- Affect
- Direct
- Negotiate
- Coordinate
- Deceive
- Summary
