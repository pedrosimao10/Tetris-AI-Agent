import asyncio
import getpass
import json
import os

import websockets
from shape import *


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                totalScores = solve(state['piece'],state['game'])
                if totalScores!=None:
                    bestRot = bestRotation(totalScores)
                    bestPos = bestPosition(totalScores)
                    for i in range(bestRot):
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": "w"})
                        )
                        state = json.loads(
                            await websocket.recv()
                        )
                    if state['piece']!=None:
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
                                state = json.loads(
                                    await websocket.recv()
                                )
                            elif shift == 0:
                                await websocket.send(
                                        json.dumps({"cmd": "key", "key": "s"})
                                    )
                                state = json.loads(
                                    await websocket.recv()
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
                                state = json.loads(
                                    await websocket.recv()
                                )

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

def identifyPiece(piece):
    try:
        x = piece[0][0]
        y = piece[0][1]
    except:
        return None
    if (piece==[[x,y],[x,y+1],[x+1,y+1],[x+1,y+2]]) or (piece==[[x,y],[x+1,y],[x-1,y+1],[x,y+1]]):
        currentPiece = SHAPES[0] #S
    elif (piece==[[x,y],[x-1,y+1],[x,y+1],[x-1,y+2]]) or (piece==[[x,y],[x+1,y],[x+1,y+1],[x+2,y+1]]):
        currentPiece = SHAPES[1] #Z
    elif (piece==[[x,y],[x+1,y],[x+2,y],[x+3,y]]) or (piece==[[x,y],[x,y+1],[x,y+2],[x,y+3]]):
        currentPiece = SHAPES[2] #I
    elif (piece==[[x,y],[x+1,y],[x,y+1],[x+1,y+1]]):
        currentPiece = SHAPES[3] #O
    elif (piece==[[x,y],[x+1,y],[x,y+1],[x,y+2]]) or (piece==[[x,y],[x+1,y],[x+2,y],[x+2,y+1]]) or (piece==[[x,y],[x,y+1],[x-1,y+2],[x,y+2]]) or (piece==[[x,y],[x,y+1],[x+1,y+1],[x+2,y+1]]):
        currentPiece = SHAPES[4] #J
    elif (piece==[[x,y],[x,y+1],[x+1,y+1],[x,y+2]]) or (piece==[[x,y],[x+1,y],[x+2,y],[x+1,y+1]]) or (piece==[[x,y],[x-1,y+1],[x,y+1],[x,y+2]]) or (piece==[[x,y],[x-1,y+1],[x,y+1],[x+1,y+1]]):
        currentPiece = SHAPES[5] #T
    elif (piece==[[x,y],[x,y+1],[x,y+2],[x+1,y+2]]) or  (piece==[[x,y],[x+1,y],[x+2,y],[x,y+1]]) or (piece==[[x,y],[x+1,y],[x+1,y+1],[x+1,y+2]]) or (piece==[[x,y],[x-2,y+1],[x-1,y+1],[x,y+1]]):
        currentPiece = SHAPES[6] #L
    else:
        currentPiece=None
    return currentPiece

def numberRotations(currentPiece):
    rotate = 0
    if currentPiece == SHAPES[0]: #S
        rotate = 1
    elif currentPiece == SHAPES[1]: #Z
        rotate = 1
    elif currentPiece == SHAPES[2]: #I
        rotate = 1
    elif currentPiece == SHAPES[3]: #O
        rotate = 0
    elif currentPiece == SHAPES[4]: #J
        rotate = 3
    elif currentPiece == SHAPES[5]: #T
        rotate = 3
    elif currentPiece == SHAPES[6]: #L
        rotate = 3
    return rotate

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
    rotate = numberRotations(currentPiece)
    if currentPiece!=None:
        totalScores = []
        for rotation in range(0,rotate+1,1):
            piece = []
            scores = []
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
                position = [[x+left,y] for [x,y] in piece]
                virtualgame = pos(game,position)
                if virtualgame!=None:
                    score = heuristics(virtualgame)
                    best_position={'x':count,'rotate':rotation}
                    scores.append(score)
                    totalScores.append((score,best_position))
                left+=1
            currentPiece.rotate()
        return totalScores
    else:
        return None

def bestPosition(totalScores):
    bestScore = -1000000
    bestPosition = -3
    for tup in totalScores:
        if (tup[0] > bestScore):
            bestScore = tup[0]
            bestPosition = tup[1].get('x')
    return bestPosition

def bestRotation(totalScores):
    bestScore = -1000000
    bestRotation = 0
    for tup in totalScores:
        if (tup[0] > bestScore):
            bestScore = tup[0]
            bestRotation = tup[1].get('rotate')
    return bestRotation

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
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))