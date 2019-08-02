import bottle
import os
import logging
from app.move import Move

logger = logging.getLogger(__name__)


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#00FF00',
        'taunt': 'Booya!',
        'head_url': head_url,
        'name': 'Pythonic Snake'
    }


@bottle.post('/move')
def move():
    data = bottle.request.json

    food_move = find_food(data)
    print('food_move={}'.format(food_move.direction))

    avoid_moves = avoid_snakes(data)
    print('avoid_snake_moves={}'.format(moves_to_string(avoid_moves)))

    avoid_moves = avoid_board(data, avoid_moves)
    print('avoid_board_moves={}'.format(moves_to_string(avoid_moves)))

    moves = []
    taunt = ''
    for avoid_move in avoid_moves:
        if avoid_move.direction == food_move.direction:
            moves.append(avoid_move)
            taunt = 'food move: '

    if len(moves) == 0 and len(avoid_moves) > 0:
        moves.append(avoid_moves[0])
        taunt = 'default avoid: '

    taunt += moves_to_string(moves)
    taunt += ' of {}'.format(moves_to_string(avoid_moves))

    if len(moves) == 0:
        moves.append(Move('left'))
        taunt = 'default: '

    return {
        'move': moves[0].direction,
        'taunt': taunt
    }


def get_snake(game_state, id):
    for snake in game_state['snakes']:
        if snake['id'] == id:
            return snake


def find_food(game_state):
    my_snake = get_snake(game_state, game_state['you'])

    # print('my_snake={}'.format(my_snake))

    head = my_snake['coords'][0]
    move = None
    if game_state['food'][0][0] < head[0]:
        move = Move('left')

    if game_state['food'][0][0] > head[0]:
        move = Move('right')

    if game_state['food'][0][1] < head[1]:
        move = Move('up')

    if game_state['food'][0][1] > head[1]:
        move = Move('down')

    return move


def avoid_snakes(game_state):
    my_snake = get_snake(game_state, game_state['you'])
    other_snakes = game_state['snakes']

    moves = get_possible_moves_list(my_snake)

    for snake in other_snakes:
        moves = avoid_snake(game_state['you'], len(my_snake['coords']), snake, moves)

    return moves


def avoid_snake(my_id, my_length, snake, moves):
    if snake['id'] != my_id:
        moves = avoid_snake_move(my_length, snake, moves)

    for part in snake['coords']:
        for move in moves:
            if is_same_square(Move(None, part), move):
                moves.remove(move)

        for move in moves:
            for x in range(1, 3, -1):
                if move.direction == 'left':
                    if is_same_square(Move(None, [move.coords[0] - x, move.coords[0]]), Move(None, part)):
                        moves.remove(move)
                        moves.append(move)

                if move.direction == 'right':
                    if is_same_square(Move(None, [move.coords[0] + x, move.coords[0]]), Move(None, part)):
                        moves.remove(move)
                        moves.append(move)

                if move.direction == 'up':
                    if is_same_square(Move(None, [move.coords[0], move.coords[0] + x]), Move(None, part)):
                        moves.remove(move)
                        moves.append(move)

                if move.direction == 'down':
                    if is_same_square(Move(None, [move.coords[0], move.coords[0] - x]), Move(None, part)):
                        moves.remove(move)
                        moves.append(move)

    return moves


def avoid_snake_move(my_length, snake, moves):
    other_len = len(snake['coords'])

    if other_len >= my_length:
        other_moves = get_possible_moves_list(snake)
        print('other_moves={}'.format(moves_to_string(other_moves)))
        for my_move in moves:
            for other_move in other_moves:
                if is_same_square(other_move, my_move):
                    moves.remove(my_move)

    return moves


def avoid_board(game_state, moves):
    max_right = game_state['width']
    max_down = game_state['height']

    for move in moves:
        if move.coords[0] < 0 or move.coords[0] >= max_right:
            moves.remove(move)

        if move.coords[1] < 0 or move.coords[1] >= max_down:
            moves.remove(move)

    return moves


def get_possible_moves_list(snake):
    moves = []

    head = Move(None, snake['coords'][0])
    neck = Move(None, snake['coords'][1])

    left_move = Move('left', [head.coords[0] - 1, head.coords[1]])
    if not is_same_square(neck, left_move):
        moves.append(left_move)

    right_move = Move('right', [head.coords[0] + 1, head.coords[1]])
    if not is_same_square(neck, right_move):
        moves.append(right_move)

    up_move = Move('up', [head.coords[0], head.coords[1] - 1])
    if not is_same_square(neck, up_move):
        moves.append(up_move)

    down_move = Move('down', [head.coords[0], head.coords[1] + 1])
    if not is_same_square(neck, down_move):
        moves.append(down_move)

    return moves


def is_same_square(one, two):
    if one.coords[0] == two.coords[0] and one.coords[1] == two.coords[1]:
        return True
    else:
        return False


# def lookahead_ranking(my_head, snake, moves):
#     ranked_moves = []
#     for move in moves:
#         if move.direction == 'left':
#             for x in range(2, 5):
#                 if is_same_square(Move(None, [my_head[0] - x, my_head[1]]),



def moves_to_string(moves):
    return ','.join([x.direction for x in moves])


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
