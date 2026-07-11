snake_body = [(5, 5), (4, 5), (3, 5)]
direction = (1, 0)
score = 0
head = snake_body [0]
new_head = (head [0] + direction [0], head [1] + direction [1])
snake_body. insert (0, new_head)
snake_body. pop ()
if (new_head [0] < 0 or new_head [0] >= 20 or new_head [1] < 0 or new_head [1] >= 20):
    game_over = True
if (new_head in snake_body [1:]):
    game_over = True
head = snake_body [0]
new_head = (head [0] + direction [0], head [1] + direction [1])
snake_body. insert (0, new_head)
snake_body. pop ()
if (new_head [0] < 0 or new_head [0] >= 20 or new_head [1] < 0 or new_head [1] >= 20):
    game_over = True
if (new_head in snake_body [1:]):
    game_over = True
head = snake_body [0]
new_head = (head [0] + direction [0], head [1] + direction [1])
snake_body. insert (0, new_head)
snake_body. pop ()
if (new_head [0] < 0 or new_head [0] >= 20 or new_head [1] < 0 or new_head [1] >= 20):
    game_over = True
if (new_head in snake_body [1:]):
    game_over = True