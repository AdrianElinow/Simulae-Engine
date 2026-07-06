
The [[Simulae]] system is intended as a meta-framework for representing and simulating actors in a game-engine agnostic manner, such that it could be integrated into any game engine with varying levels of effort. 

# Simulae Node Integration


# Simulae Actor Integration

[[SimulaeNode/Simulae Actor]]s are intended to represent Actors (NPCs, Players, entities that make choices and perform actions).

As most actors in game engines typically play out actions in-game by the use of scripts, it is relevant to map these scripts to the [[SimulaeNode/Simulae Actor]]s [[Abilities]] and add a compatibility layer in order to trigger these scripts when the actor intends to perform the corresponding [[Abilities]].