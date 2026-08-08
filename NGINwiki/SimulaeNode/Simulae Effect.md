Simulae Effects are the resultant actions of an update/ability which are intended to be able to encompass any and all updates to another [[SimulaeNode]]

This is intended to be the base class for how [[SimulaeNode]]s interact with one another.

Examples:
- Basic functions are all abilities:
	- 'Walking' is an ability 
		- Granted by having a locomotive component (such as legs) 
		- Actions:
			- Costs energy (calories + oxygen)
			- Updates [[Simulae Actor]]/owners location
	- 'Breathing' is an ability that is granted by having a respiratory component (such as lungs), intakes environment's atmosphere, harvests the useful material and provides useful material to the rest of the body
	- 'Eating' is an ability that is granted by having digestive system components that allow the [[Simulae Actor]] owner to consume other [[SimulaeNode]]s. 
		- 'Intake' component (Mouth) transmutes a type of simulae node (i.e. organic edible material -> 'food') to its components and/or chewed version and provides it to its 'downstream' organ (esophagus/stomach)
		- 'liquifier' component (stomach) transmutes given material to its base material components and provides it to its 'downstream' organ (intestines)
		- 'harvester/sorter' component (intestines) harvests the 'useful' (which be nutritional food and drink BUT can also include poisons and 'dangerous' material) components from the given material, provides the harvested components to the rest of the body and provides the rest of the unused material to the 'downstream' organ (rectum)
	- 'Healing' is a slow passive ability that costs energy, compositional material, and low usage (eat food and rest to heal)
	- Hands (with opposable thumbs) are incredibly versatile and provide lots of important abilities to their owners allowing them the ability to 'grip' things, and fingers with which to 'manipulate' objects, as well as the sense of 'touch' and 'temperature' (skin), 'push', and 'pull'
- 'Inanimate' objects have abilities:
	- lightswitches can be flicked on/off and update electric lights to turn on/off accordingly
	- lights, when turned on, consume electricity and provide light
	- cars are made up of many components including engines, transmissions, driveshafts, differentials, axles, wheels, suspensions
	- bandages are inanimate objects which can be used to 'stabilize' a [[Simulae Actor]]s damaged/bleeding body part which will allow the passive 'heal' ability to outpace the blood drain/damage
- Damage model:
	- Guns consume ammunition, burning the powder charge, transmuting that energy and expel the bullet at a calculated velocity
	- A bullet, that along its flight path, can puncture and deliver remaining energy to whatever it collides with. This effect can inflict organ damage, cause bleeding and/or organ failure which can impact the recipient's abilities.
		- Damaged organs indicate pain to the owner's nervous system/brain and reduce effectiveness or completely compromise functionality
		- destroyed organs cause the owner to lose access to their abilities (when someone's legs are blown off, they can no longer walk)

### Effect Conditions

An effect may have [[Condition]]s which must be satisfied in order to be performed.

> ex: in order to perform the action 'resurrect' the target's status must be 'Dead' (but must also be 'animate' such that one cannot 'resurrect' inanimate objects which are technically not alive)

### Effect Actions

Possible Effect Actions can include any number of:
- Adding/Removing/Updating a target [[SimulaeNode]]'s state:
	- [[References]] - Add/Update/Delete 
	- [[Attributes]] - Add/Update/Delete 
	- [[Relations]] - Add/Remove/Transmute/Update/Compose/Decompose [[SimulaeNode]]s
	- [[Abilities]] - Cause them to be disabled/fail/upgrade/etc
	- [[Memories]] - Causing hallucinations or erasing memories
- Triggering another [[Simulae Effect]]
- Creating a [[Simulae Event]]

...