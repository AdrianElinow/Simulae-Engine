The 'Relations' structure contains nested lookups forming a tree which details the physical relationship between the [[SimulaeNode]] and other [[SimulaeNode]]s with a direct physical relationship.
These relationships are detailed in this structure when they are 'inseparable' from the subject, meaning that if one were to move the subject [[SimulaeNode]], the ones detailed in these structures would also be affected by that relocation (either by accompanying it or would have their relationship's changed/removed as a result of that process)

> Example: A node representing a building is 'relocated' to another place. Here's what would happen:
> 	- It's Walls and Rooms of which it is composed are also relocated
> 	- Furniture and people inside are also relocated
> 	- The building's links/pathways leading in/out from/to the structure have their links broken as the building is no longer there.
> 	- Someone on the roof of the building, or hanging onto the side of the building may remain held to the side of the structure *or* fall off of it along it's journey or remain at the initial location
> 	- If a magic portal still exists that teleports a [[SimulaeNode]] inside of the building regardless of where it is, would *not* have it's relationship broken.

## [[Relations]] Categories

| ***Relation*** | ***Description***                                                                                                                         |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Components     | The [[SimulaeNode]]s that make-up the given 'Product' [[SimulaeNode]] (ex: the Table-legs and the Table-top which make up a Table object) |
| Contents       | The [[SimulaeNode]]s that are held within the 'Containing' [[SimulaeNode]] (ex: gold or loot in a treasure-chest)                         |
| Accessories    | The [[SimulaeNode]]s that are attached to (externally), but not apart of, the 'Accessorized' [[SimulaeNode]]                              |
| Adjacents      | The SimulaeNodes that are located 'adjacent' to the given [[SimulaeNode]].                                                                |
| Sources        | Any [[SimulaeNode]]s from which a [[Simulae Event]] was enacted/triggered                                                                 |
| Targets        | Any [[SimulaeNode]]s which were affected by the [[Simulae Event]]                                                                         |
| Observers      | Any [[SimulaeNode]]s which directly observed the [[Simulae Event]] and what information was distributed to them accordingly               |
> Note: This is not an exhaustive list of 'Relations' as this structure is designed to be extensible, allowing for other types of 'relations' between SimulaeNodes beyond what is listed.

```mermaid

flowchart TB
	subgraph sn["Subject SimulaeNode"]
		subgraph cont["Contents"]
			snContent["Content-SimulaeNode"]
		end
		component["Component SimulaeNode"]
	end
	
	accessory["Accessory SimulaeNode"]
	
	subgraph adjacent["Adjacent SimulaeNode"]
		subgraph otherContents["Other Contents"]
			otherContent["... SimulaeNode"]
		end
		otherComponents["Other Component"]
	end

	sn -- "Adjacent-to" --> adjacent
	sn -- "Accessorized-by" --> accessory

```


> ex: Relations for a [[SimulaeNode]]
```json
Relations = {
	'Components': {...},
	'Contents': {...},
	'Accessories': {...},
	'Adjacents': {...},
}
```

> ex: Relations for a [[Simulae Event]]
```json
Relations = {
	'Sources': {...},
	'Targets': {...},
	'Observers': {...},
}
```


