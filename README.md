# PythonStrategyRPG
It is a simple strategy turn based game
* use AStar algorithm to walk
* support melee and remote creature
* use json file to store level data (e.g. position of creatures, map info)

# Requirement
* Python 3.7
* Python-Pygame 1.9

# How To Start Game
$ python main.py

# How to Play
* use mouse to select the active creature to walk or attack 

# Demo
![rpg1](https://raw.githubusercontent.com/marblexu/PythonStrategyRPG/master/demo/rpg1.png)
![rpg2](https://raw.githubusercontent.com/marblexu/PythonStrategyRPG/master/demo/rpg2.png)

# Working in Progress

[x] Path finding and attack finding. @Oct.8
[x] Simple UI and control loop Demo. @Oct.9
[x] Add attack and counter attack computation. @Oct.10 
[x] HP display in text @Oct.10
[x] Unit die and pop out of list @Oct.10
[x] Enemy unit inpassable @Oct.10
[x] Cancel selection. @Oct.10
[x] CounterAttack criterion @Oct.10
[x] Start More Unit Numerical design @Oct.10
[x] Wrap up the Game loop with a class! @Oct.10
[x] Recursive Successor function call. @Oct.10
[x] Implement Baseline random legal action policy, trajectory sampling. @Oct.10
[x] DFS List all strategy in one Turn(not good) @Oct.11
[x] Deep copy for game state method.  @Oct.10
[x] Primitive Reward or Evaluation Function for State x Action pair. @Oct.11
[x] New Baseline, Greedy policy (in the space of Select+Move+Attack Maximize single step reward) @Oct.11
[x] Video Playback, or playing action sequence on the screen passively. @Oct.11
[x] Recursive or MiniMax Quality definition! Threat Elimination Strategy @Oct.12
[x] Add unit, StoneMan, StormSummoner @Oct.12
[x] Debug Cannot stay in same location problem @Oct.12
[x] Ability and Buff design, StormSummoner. IMplement AOE attack! @Oct.12
[x] Speed up by disable legality check! or decrease the move range computation.  @Oct.12
[x] Updata GUI loop to support Action selection @Oct.12
[x] New GUI display for AOE ability!  @Oct.12
[x] Debug the AOE attack random die. @Oct.13
[x] Scalable Approximate Threat Elimination Algor @Oct.13
[ ] Search Tree recursion 2-3 levels
[ ] Ability and Buff design, Heal
[ ] Economy and Unit purchase design. 
[ ] Efficiency increase in search by improving the deep clone.
[ ] Prune Search tree, making it less expansion! Discard useless moves soon. 
[ ] Search Tree proposal
[ ] Ability and Buff design, Summon?