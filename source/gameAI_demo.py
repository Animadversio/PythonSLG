# Exitflag = False
# automove = True
# SingleUnitTurn = False # Each player is allowed to move only one unit in a turn. If false then can move all
# while not Exitflag:
#     if playerAI[game.curPlayer] == "human":
#         game.GUI_loop(oneturn=True)
#     else:
#         policystr, policyFun, params = playerAI[game.curPlayer]
#         Moveflag = automove # if True then without key tab, it's keeping moving.
#         for event in pg.event.get():
#             if event.type == pg.QUIT:
#                 Exitflag = True
#             if event.type == pg.KEYDOWN:
#                 if event.key == pg.K_TAB:
#                     Moveflag = True
#         if Moveflag:
#             game.drawBackground()
#             game.drawBuildingList()
#             game.drawUnitList()
#             pg.display.update()
#             if SingleUnitTurn: game.endTurn() # Each side move one unit each turn!
#             best_seq, best_state, best_rew = policyFun(game, **params)
#             _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True,)
#             game.drawBackground()
#             game.drawBuildingList()
#             game.drawUnitList()
#             pg.display.update()
#     enemyPos, enemyUnit = game.getAllEnemyUnit()
#     if len(enemyUnit) == 0:
#         print("Player %d Win the game!"%game.curPlayer)
#         Exitflag=True
#
# #%%
# G.GUI_loop()






#% Demo Random Game play
# gamestr = GameStateCtrl()
# actseq = []
# # game.GUI_loop()
# #%%
# game = gamestr
# for i in range(250):
#     moves, nextUIstate = game.getPossibleMoves()
#     move = choice(moves)
#     game.action_execute(*move, clone=False) # game =
#     actseq.append(move)
# print([unit.pos for unit in game.unitList])
# print([unit.player for unit in game.unitList])
# #%%
# game.GUI_loop()

# Demo Greedy Agents
# game = GameStateCtrl()
# game.endTurn()
# for i in range(20):
#     best_seq, best_state, best_rew = greedyPolicy(game)
#     _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
# game.GUI_loop()
# #%% This demonstrates Two Greedy agents playing with each other.
# game = GameStateCtrl()
# game.endTurn()
#
# # This is the basic loop for playing an action sequence step by step
# Exitflag = False
# while not Exitflag:
#     for event in pg.event.get():
#         if event.type == pg.QUIT:
#             Exitflag = True
#         if event.type == pg.KEYDOWN:
#             if event.key == pg.K_TAB:
#                 best_seq, best_state, best_rew = greedyPolicy(game)
#                 _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
#     game.drawBackground()
#     game.drawUnitList()
#     pg.display.update()
# #%%
# # Strategic Value
# game = GameStateCtrl()
# game.endTurn()
# best_seq, best_state, best_rew = greedyPolicy(game)
# _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
# best_seq, best_state, best_rew = greedyPolicy(game)
# _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
#%%

#%% DFS search engine
"""Obsolete"""
# def DFS, even a single round has > 3287649 possible action sequences as defined here.
# game = GameStateCtrl()
# game.endTurn()
# T0 = time()
# movseq_col = Stack()
# movseq_col.push(([], 0, game))
# whole_movseqs = PriorityQueue() # [] #
# while not movseq_col.isEmpty():
#     actseq, cumrew, curGame = movseq_col.pop()
#     moves, nextUIstate = curGame.getPossibleMoves()
#     # if len(movseq_col.list) > 500 or len(whole_movseqs) > 100:
#     #     break
#     #     print("%d traj found"%len(whole_movseqs))
#     for move in moves: #
#         next_actseq = copy(actseq)
#         next_actseq.append(move)
#         nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True)
#         nextcumrew = cumrew + nextrewards[curGame.curPlayer-1]
#         if move[0] is "attack" or move[0] is "stand":
#             # whole_movseqs.append((next_actseq, nextGame, nextcumrew))
#             # print("%d traj found" % len(whole_movseqs))
#             whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew)
#             print("%d traj found" % len(whole_movseqs.heap))
#             continue
#         # move = choice(moves)
#         movseq_col.push((next_actseq, nextcumrew, nextGame))
# print("%.2f sec" % (time() - T0)) # selecting and moving one of the units has 192 different move seqs. Finished in .25sec
# print([unit.pos for unit in game.unitList])
# print([unit.player for unit in game.unitList])
#%%
# getSuccessor
# stepState = SELECT_UNIT
#
# if stepState is SELECT_UNIT:
#     selectable_pos, selectable_unit = getSelectableUnit(unitList, curPlayer)  # Possible moves
#     # Actuate Select
#     if len(selectable_pos) is 0:
#         nextState = END_TURN
#         curPlayer = next(playerIter)
#
# stepState = SELECT_MOVTARGET
# obst_pos = getObstacleInRange(curUnit, None, unitList)
# movRange = getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
# # Actuate Move
#
# stepState = SELECT_ATTTARGET
# attRange = getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
# targetPos, targetUnits = getTargetInRange(curUnit, attRange, unitList)