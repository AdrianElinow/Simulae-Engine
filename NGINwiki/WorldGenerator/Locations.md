
While the [[World Generator]] may generate many [[Locations]] that comprise a certain 'world', a single 'location' may initially include a 'population' of [[SimulaeNode/Simulae Actor]](s)

A 'location' is an abstract type of [[SimulaeNode]] organized as discrete 'places' organized in a network of other [[Locations]] connected as an adjacency-matrix by linking pairs as 'adjacent' [[Relations]]

```mermaid
mindmap
World Root
	loc1["Location 1"]
		loc3["Location 3"]
		...
	loc2["Location 2"]
		loc4["Location 4"]
		loc5["Location 5"]
		...
	loc6["Location 6"]
		loc7["Location 7"]
		...
	...
```

In the future, for a more realistic world-model, discrete '[[Locations]]' may instead be used as spacial 'zones' in a continuous 3-dimensional space instead of the entire make-up of the world itself.

