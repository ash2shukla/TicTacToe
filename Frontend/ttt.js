$(document).ready(function() {
    var sock_server = "ws://localhost:8000";
    $("#refresh").hide();
    var xo = undefined;

    // local grid
    var grid = [undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined];
    var connection = new WebSocket(sock_server);
    
    // virtually handling the "so called critical section of TTT board"
    var sema = undefined;

    // svgs for X and O
    // SVG animations are disabled in windows on battery saver mode so X might not render properly at battery saver
    var x = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130.2 130.2"><line class="path line" fill="none" stroke="#D06079" stroke-width="6" stroke-linecap="round" stroke-miterlimit="10" x1="34.4" y1="37.9" x2="95.8" y2="92.3"/><line class="path line" fill="none" stroke="#D06079" stroke-width="6" stroke-linecap="round" stroke-miterlimit="10" x1="95.8" y1="38" x2="34.4" y2="92.2"/></svg>'
    var o = '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 130.2 130.2"><circle class="path circle" fill="none" stroke="#73AF55" stroke-width="6" stroke-miterlimit="10" cx="65.1" cy="65.1" r="62.1"/></svg>'

    // is game over
    var finished = false;
    connection.onopen = function() {
        // connection.send('Ping ping');
    };
    
    connection.onerror = function(error) {
        console.log('Websocket error' + error)
    };

    connection.onmessage = function (e) {
        var parsed_message = JSON.parse(e.data);
        if (parsed_message.event == 'game_state') {
            if (parsed_message.state == 'waiting') {
                $("#state").text("Waiting for other player to join");
            } else if (parsed_message.state == 'start') {
                $("#state").text("Player joined starting game");
            }
        } else if (parsed_message.event == 'toss') {
            $("#state").text("You are "+ parsed_message.xo.toUpperCase());
            xo = parsed_message.xo;
            // let the user move only if he is X
            sema = xo == 'x';
            console.log('toss done ' + parsed_message.xo);
        } else if (parsed_message.event == 'opponent_move') {
            // after opponent move let the user move set grid as per opponent's move
            sema = true;
            grid[Number(parsed_message.move_coord)] = xo == 'x'?'o':'x';

            // insert x or o svg as per opponent move
            $('#'+parsed_message.move_coord).append(xo == 'x'? o: x);
        } else if (parsed_message.event == 'won') {
            $("#state").text('Congratulations you won.');
            sema = false;
            finished = true;
            $("#refresh").show();

        } else if (parsed_message.event == 'lost') {
            $("#state").text("Poor lad better luck next time. You lost.")
            sema = false;
            finished = true;
            $("#refresh").show();
        } else if (parsed_message.event == "opponent_disconnected") {
            // if opponent disconnected then finish game dont let the user make changes and show restart game button
            sema = false;
            finished = true;
            $("#state").text("Opponent has disconnected");
            $("#refresh").show();
        }
        console.log('Server: ' + e.data);
    }

    connection.onclose = function(arg) {
        console.log('Closed')
    }

    function send_move(event) {
        if (!sema && !finished) {
            alert("Not your move");
            // raise a message "not your move"
        }
        if (finished) {
            alert("Refresh page to restart game.")
        }
        if (grid[Number(event.data.move_index)] == undefined && sema && !finished) {
            sema = false;
            grid[Number(event.data.move_index)] = xo;
            // insert x or o svg
            $("#" + event.data.move_index).append(xo == 'x'? x: o);
            connection.send( JSON.stringify({"event": "move" , "move_coord": event.data.move_index}) );
        }
        console.log(grid);
    }

    $("#1").click({move_index: '1'}, send_move);
    $("#2").click({move_index: '2'}, send_move);
    $("#3").click({move_index: '3'}, send_move);
    $("#4").click({move_index: '4'}, send_move);
    $("#5").click({move_index: '5'}, send_move);
    $("#6").click({move_index: '6'}, send_move);
    $("#7").click({move_index: '7'}, send_move);
    $("#8").click({move_index: '8'}, send_move);
    $("#9").click({move_index: '9'}, send_move);

});