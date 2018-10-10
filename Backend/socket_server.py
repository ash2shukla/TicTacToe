from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from json import dumps, loads
from json.decoder import JSONDecodeError
from random import choice
from string import ascii_letters


# Something better like Redis can be used instead of declaring globals like this
connected_clients = {}
player_waiting  = None
current_games = {}

class TTTSock(WebSocket):
    """
    Handles the client requests for TTT Multiplayer.

    Sent Event
        1. game_state - state: waiting, start ( if state is start it will also have 'game_id' ) 
        2. toss - xo: x or o
        3. err - message
        4. opponent_disconnected
        5. won
        6. lost
    
    Received Event
        1. move - move_coord
    """
    def check_if_won(self, current_grid):
        print(current_grid)
        # conditions in a 3x3 TTT where user may win
        conditions = [[1,2,3], [4,5,6], [7,8,9], [1,4,7], [2,5,8], [3,6,9], [1,5,9], [3,5,7]]
        x =  []
        o =  []
        for index, xo in current_grid.items():
            if xo == 'x':
                x.append(int(index))
            elif xo == 'o':
                o.append(int(index))
        if any([all([ pos in x for pos in condition]) for condition in conditions]):
            return 'x'
        elif any([all([ pos in o for pos in condition]) for condition in conditions]):
            return 'o'
        else:
            return None

    def handleConnected(self):
        """
        handles connection request of TTT client
        """
        global connected_clients
        global player_waiting
        # if we want to allow only one connection per IP then leave out the address[1]
        self.id = self.address[0] + str(self.address[1])
        connected_clients[self.id] = {'connection': self, 'opponent': None, 'ingame': False, 'game_id': None}
        if player_waiting is None:
            # if no player is waiting then connected player will wait till someone else joins
            player_waiting = self.id
            # send event game_state to wait
            self.sendMessage('{"event": "game_state", "state": "waiting"}')
        else:
            # see if a player is waiting assign it to the opponent of this player and send the waiting player start game event
            waiting_player_obj = connected_clients[player_waiting]

            # create a random game id
            game_id = ''.join([choice(ascii_letters) for i in range(10)])

            # update information of this client
            connected_clients[self.id]['opponent'] = player_waiting
            connected_clients[self.id]['ingame'] = True
            connected_clients[self.id]['game_id'] = game_id
            self.sendMessage( dumps({"event": "game_state", "state": "start", "game_id": game_id}) )

            # update information of the opponent
            waiting_player_obj['opponent'] = self.id
            waiting_player_obj['ingame'] = True
            waiting_player_obj['game_id'] = game_id
            waiting_player_obj['connection'].sendMessage(dumps({"event": "game_state", "state": "start", "game_id": game_id}))

            # make a toss
            toss = choice(['x', 'o'])
            other = 'x' if toss == 'o' else 'o'

            # Assign the xo to player_waiting and send toss event
            waiting_player_obj['connection'].xo = other
            waiting_player_obj['connection'].sendMessage(dumps({"event": "toss", "xo": other}))

            # Assign the xo to the connected player and send toss event
            self.xo = toss
            self.sendMessage(dumps({"event": "toss", "xo": toss}))

            global current_games

            # Instantiate grid for the new Game
            current_games[game_id] = {toss: self.id, other: player_waiting, 'covered_grid': {}}

            # no player is waiting now
            player_waiting = None

        print(self.address, 'connected')
    
    def handleClose(self):
        global player_waiting
        if player_waiting == self.id:
            player_waiting = None
        print(self.address, 'closed')
        if connected_clients[self.id]['ingame']:
            connected_clients[connected_clients[self.id]['opponent']]['connection'].sendMessage(dumps({"event": "opponent_disconnected"}))

        del connected_clients[self.id]

    def handleMessage(self):
        print(f'ID: {self.id} Message: {self.data}')
        try:
            # load data in json and return err if invalid JSON
            data = loads(self.data)
            if data.get('event') == 'move':
                # triggered on a move from a client
                opponent_id = connected_clients[self.id]['opponent']
                # if move coordinates are already in covered_grid corresponding to game_id then send an Invalid move
                # The case is by default handled by frontend's logic but its just a double check
                if data.get('move_coord') in current_games[connected_clients[self.id]['game_id']]['covered_grid']:
                     self.sendMessage(dumps({"event": "err", "message": "Invalid move"}))
                else:
                    # if the move is unique then insert it in covered_grid as {'move_coord': 'x' or 'o'}
                    current_games[connected_clients[self.id]['game_id']]['covered_grid'][data.get('move_coord')] = self.xo
                    # forward the move to the opponent's socket
                    connected_clients[opponent_id]['connection'].sendMessage(dumps({"event": "opponent_move", "move_coord": data.get('move_coord')}))
                    # get current_grid and check if someone has won
                    current_grid =  current_games[connected_clients[self.id]['game_id']]['covered_grid']
                    has_won = self.check_if_won(current_grid)
                    if has_won is not None:
                        if self.xo == has_won:
                            self.sendMessage(dumps({"event": "won"}))
                            connected_clients[opponent_id]['connection'].sendMessage(dumps({"event": "lost"}))
                        else:
                            self.sendMessage(dumps({"event": "lost"}))
                            connected_clients[opponent_id]['connection'].sendMessage(dumps({"event": "won"}))

        except JSONDecodeError:
            self.sendMessage(dumps({"event": "err", "message": "invalid JSON Object"}))
        except Exception as e:
            print(e)

server = SimpleWebSocketServer('', 8000, TTTSock)
server.serveforever()
