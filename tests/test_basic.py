def test_game_init():
    from pac.game import Game
    g = Game()
    assert g.width > 0
    assert g.height > 0


def test_eat_pellet():
    from pac.game import Game, Vec
    g = Game()
    # place pellet at pac location
    g.map[g.pac.y][g.pac.x] = '.'
    before = g.score
    g.update()
    assert g.score > before
