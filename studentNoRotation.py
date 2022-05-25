import asyncio
import getpass
import json
import os

import websockets
from shape import *


async def agent_loop(server_address="localhost:8022", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                bestPos = -10
                shift = -10
                best_5 = solve(state['piece'],state['game'])
                if best_5!=None:
                    bestPos = bestPosition(best_5)
                    shift = compareX(bestPos,state['piece'])
                    if bestPosition!=-10 and shift!=-10:
                        if shift < 0:
                            for i in range(-shift):
                                await websocket.send(
                                    json.dumps({"cmd": "key", "key": "a"})
                                )
                                state = json.loads(
                                    await websocket.recv()
                                )
                            await websocket.send(
                                json.dumps({"cmd": "key", "key": "s"})
                            )
                        elif shift == 0:
                            await websocket.send(
                                    json.dumps({"cmd": "key", "key": "s"})
                                )
                        else:
                            for i in range(shift):
                                await websocket.send(
                                    json.dumps({"cmd": "key", "key": "d"})
                                )
                                state = json.loads(
                                    await websocket.recv()
                                )
                            await websocket.send(
                                json.dumps({"cmd": "key", "key": "s"})
                            )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

def gridCreater(game):
    grid = []
    for i in range(30):
        grid.append([])
    for m in range(30):
        for n in range(8):
            grid[m].append(0)
    for position in game:
        grid[position[1]][position[0]-1] = 1
    return grid

def identifyPiece(piece):
    try:
        x = piece[0][0]
        y = piece[0][1]
    except:
        return None
    if (piece==[[x,y],[x,y+1],[x+1,y+1],[x+1,y+2]]):
        currentPiece = SHAPES[0] #S
    elif (piece==[[x,y],[x-1,y+1],[x,y+1],[x-1,y+2]]):
        currentPiece = SHAPES[1] #Z
    elif (piece==[[x,y],[x+1,y],[x+2,y],[x+3,y]]):
        currentPiece = SHAPES[2] #I
    elif (piece==[[x,y],[x+1,y],[x,y+1],[x+1,y+1]]):
        currentPiece = SHAPES[3] #O
    elif (piece==[[x,y],[x+1,y],[x,y+1],[x,y+2]]):
        currentPiece = SHAPES[4] #J
    elif (piece==[[x,y],[x,y+1],[x+1,y+1],[x,y+2]]):
        currentPiece = SHAPES[5] #T
    elif (piece==[[x,y],[x,y+1],[x,y+2],[x+1,y+2]]):
        currentPiece = SHAPES[6] #L
    else:
        currentPiece=None
    return currentPiece

def pos(game,piece):
    grid = [[1,30],[2,30],[3,30],[4,30],[5,30],[6,30],[7,30],[8,30]]
    for y in range(30):
        new_piece = [[x,y+1] for [x,y] in piece]
        if (any(fragment in new_piece for fragment in game)) or (any(fragment in new_piece for fragment in grid)):
            return game+piece
        else:
            piece = new_piece

def heuristics(virtualgame):
    score = 0
    a = -0.510066
    b = 0.760666
    c = -0.35663
    d = -0.184483
    aggregate = aggregateHeight(virtualgame)
    lines = completeLines(virtualgame)
    numberHoles = countHoles(virtualgame)
    bumpiness = getBumpiness(virtualgame)
    score = a * aggregate + b * lines + c * numberHoles + d * bumpiness
    return score

def aggregateHeight(virtualgame):
    aggregate = 0
    for i in range(1,9,1):
        min_Y = 30
        for coordinates in virtualgame:
            if (coordinates[0] == i) and (coordinates[1] < min_Y):
                min_Y = coordinates[1]
        aggregate += 30-min_Y
    return aggregate

def completeLines(virtualgame):
    lines = 0
    for i in range(1,30,1):
        somaColunas = 0
        for coordinates in virtualgame:
            if (coordinates[1] == i):
                somaColunas += 1
        if somaColunas==8:
            lines += 1
    return lines

def countHoles(virtualgame):
    numberHoles = 0
    dic = {}
    virtualgameSorted = sorted(virtualgame,key=lambda x:(x[0],x[1]))
    for coordinates in virtualgameSorted:
        if coordinates[0] not in dic.keys():
            dic[coordinates[0]] = coordinates[1]
        else:
            if dic.get(coordinates[0])!=coordinates[1]-1:
                numberHoles += 1
            dic[coordinates[0]] = coordinates[1]
    for key in dic.keys():
        numberHoles += (29 - dic.get(key))
    return numberHoles

def getBumpiness(virtualgame):
    bumpiness = 0
    for i in range(1,8,1):
        min_Y_c1 = 30
        min_Y_c2 = 30
        for coordinates in virtualgame:
            if (coordinates[0] == i) and (coordinates[1] < min_Y_c1):
                min_Y_c1 = coordinates[1]
            if (coordinates[0] == i+1) and (coordinates[1] < min_Y_c2):
                min_Y_c2 = coordinates[1]
        bumpiness += abs(min_Y_c1 - min_Y_c2)
    return bumpiness

def solve(piece,game):
    currentPiece = identifyPiece(piece)
    if currentPiece!=None:
        piece = []
        scores = []
        positionsScores = []
        best_5 = []
        min_X = 9
        max_X = -1
        for (x,y) in currentPiece.positions:
            piece.append([x,y])
            if x<min_X:
                min_X = x
            if x>max_X:
                max_X = x
    
        left = -(min_X-1)
        right = (8-max_X)

        count = 0
        while left <= right:
            count+=1
            print(f"count --- {count}")
            position = [[x+left,y] for [x,y] in piece]
            virtualgame = pos(game,position)
            if virtualgame!=None:
                score = heuristics(virtualgame)
                best_position={'x':count,'rotate':0}
                scores.append(score)
                positionsScores.append(position)
                best_5.append((score,best_position))
            left+=1
        print(f"SCORES --> {scores}")
        print(f"BEST5 --> {best_5}")

        # posicao = abs(left - x) + 1
        return best_5

def bestPosition(best_5):
    bestScore = -1000000
    bestPosition = -3
    for tup in best_5:
        if (tup[0] > bestScore):
            bestScore = tup[0]
            bestPosition = tup[1].get('x')
    return bestPosition

def compareX(bestPosition,piece):
    shift = 0
    min_X = 8
    for coordinates in piece:
        if coordinates[0]<min_X:
            min_X = coordinates[0]
    shift = bestPosition - min_X
    return shift
        

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8022")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))