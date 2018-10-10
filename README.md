# TicTacToe
A simplistic multiplayer Tic Tac Toe using python for backend and jquery for frontend.

The fiddle also supports multiple concurrent games.
It uses WebSocket Protocol for Client Server interaction.

## How to run?
dependency - Python3.6+
SimpleWebSocketServer (install by - pip install git+https://github.com/dpallot/simple-websocket-server.git)

1. cd Frontend run> python -m http.server 8080 (Change the IP in ttt.js <sock_server> as per the network)
2. cd Backend run> python socket_server.py <- ws runs on 8000

Open in browser - HOST_IP:8080

## Other Notes-
1. o and x is chosen randomly by server
2. x gets to play the first move
3. on opponent drop game ends
