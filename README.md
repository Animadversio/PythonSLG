# Python SLG
It is a strategy turn based game, inspired by code in PythonStrategyRPG, game mechanism is inspired by Ancient Empire II
* use AStar algorithm to walk
* support melee and remote creature
* use json file to store level data (e.g. position of creatures, map info)

# Requirement
* Python 3.7
* Python-Pygame 1.9

# How To Start Game
$ python main.py

# How to Play
* Use mouse or 4 direction arrows to move cursor, double click space or enter to select the active units, then to move, attack or use magic
* DClick the HQ to purchase units. 
* Press Tab to end turn.
* Press 1,2 to select action.  

# Features
## Game System
* Unit with AOE magic. Remote and melee unit. Far reaching siege unit. 
* Purchasing unit from HeadQuarter or Castle. 

 
## Policy
Advanced policy for planning multiple unit action coordination is a crucial part of this project. The following policies have been implemented. 

* Greedy one step reward maximization policy. 
* Greedy one step reward maximization, with heuristics
    * position maximize threat posing on others
    * Position minimize danger posed by opponent units.
    * Attack unit that eliminate the most threat posed by it. 

`![rpg1](https://raw.githubusercontent.com/marblexu/PythonStrategyRPG/master/demo/rpg1.png)`
`![rpg2](https://raw.githubusercontent.com/marblexu/PythonStrategyRPG/master/demo/rpg2.png)`


# Working in Progress

- [x] Path finding and attack finding. @Oct.8
- [x] Simple UI and control loop Demo. @Oct.9
- [x] Add attack and counter attack computation. @Oct.10 
- [x] HP display in text @Oct.10
- [x] Unit die and pop out of list @Oct.10
- [x] Enemy unit inpassable @Oct.10
- [x] Cancel selection. @Oct.10
- [x] CounterAttack criterion @Oct.10
- [x] Start More Unit Numerical design @Oct.10
- [x] Wrap up the Game loop with a class! @Oct.10
- [x] Recursive Successor function call. @Oct.10
- [x] Implement Baseline random legal action policy, trajectory sampling. @Oct.10
- [x] DFS List all strategy in one Turn(not good) @Oct.11
- [x] Deep copy for game state method.  @Oct.10
- [x] Primitive Reward or Evaluation Function for State x Action pair. @Oct.11
- [x] New Baseline, Greedy policy (in the space of Select+Move+Attack Maximize single step reward) @Oct.11
- [x] Video Playback, or playing action sequence on the screen passively. @Oct.11
- [x] Recursive or MiniMax Quality definition! Threat Elimination Strategy @Oct.12
- [x] Add unit, StoneMan, StormSummoner @Oct.12
- [x] Debug Cannot stay in same location problem @Oct.12
- [x] Ability and Buff design, StormSummoner. IMplement AOE attack! @Oct.12
- [x] Speed up by disable legality check! or decrease the move range computation.  @Oct.12
- [x] Updata GUI loop to support Action selection @Oct.12
- [x] New GUI display for AOE ability!  @Oct.12
- [x] Debug the AOE attack random die. @Oct.13
- [x] Scalable Approximate Threat Elimination Algor @Oct.13
- [x] Search Tree recursion 2-3 levels for Threat Elimination algorithm @Oct.13
- [x] debug negative harm affect positively @Oct.13
- [x] Utility function, computing combat info, computing attack coverage, and Mov Attack pair... @Oct.14
- [x] Danger of tile calculation add this to heuristic. @Oct.14
- [x] Risk aversion greedy policy, alpha to trade off risk and reward.  @Oct.14
    * Many interesting behavior emerged from this change! Very well done. 
    * Still, it doesn't estimate the potential benefit (2nd order gain) of that position... 
    * This is a first order estimate of next enemy turn lost, but no 2nd order estimate of gain in the next turn..
- [x] Simple estimation of threat posing on others, and Maximize threat on others, minimize threat posed on me. @Oct.15
- [x] Efficiency increase by improving the deep clone unit and game state, improve attack range computation by not saving the set. @Oct.15
- [x] Debug the negative threat elimin value problem @Oct.15
- [x] Debug the negative risk problem @Oct.15 
- [x] Debug the reward calculation negative problem.... @Oct.15
- [x] Debug the overkill over reward problem @Oct.15
- [x] Add more printing interface @oCT.15
- [x] Increase efficiency by approximating greedy policy and merging movement and attack planning! @Oct.17-18
    * This change is SO EFFECTIVE that planning time is lower than .5 sec for each side now! 
    * Implement approximate fast search for AOE as well! 
- [x] Economy and Unit purchase design. 
    - [x] Add building castle system. 
    - [x] Add income and funding
    - [x] Add buying action
- [x] Make it compatible with previous policies, test the game with unit purchasing with the search based AIs. @Dec.3 @Nov.28
- [ ] Let AI and human play together or AI with different parameters play and compete. 
- [ ] Add the Monte Carlo Tree Search to the game
- [ ] Learning based Value or Q evaluation, by self play and offline learning. 
- [ ] Occupy and Factory and barrack. 
- [ ] Prune Search tree, making it less expansion! Discard useless moves soon. 
- [ ] Optimize efficiency of the copy of unit
- [ ] Pre compute a match table to save computation.  
- [ ] Ability and Buff design, Heal
- [ ] Ability and Buff design, Summon?
- [ ] Ability and Buff design, Attack Aura, Defence Aura?
- [ ] Ability and Buff design, Berserker, Attack + Def + as HP - ?
