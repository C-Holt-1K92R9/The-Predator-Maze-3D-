from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
from collections import deque

WINDOW_WIDTH = 1500
WINDOW_HEIGHT = 800
maze_walls_colors = []
MAZE_ROWS = 6
MAZE_COLS = 6
CELL_SIZE = 50
WALL_HEIGHT = 50
MAZE_OFFSET_X = -(MAZE_COLS * CELL_SIZE) / 2
MAZE_OFFSET_Z = -(MAZE_ROWS * CELL_SIZE) / 2
take_a_peak = False

camera_pos = (0, 500, 500)
camera_up = (0, 1, 0)
camera_target = (0, 0, 0)
fovY = 90

player_pos = [0, 0, 0]
player_angle = 0
player_height = 15
PLAYER_RADIUS = 20
player_speed = 5
player_coins = 0
player_bullets = 20
player_size = 0.1
enemy_kill = 0

GAME_STATE = "TOP_DOWN"
game_over_timer = 0
TOP_DOWN_VIEW_TIME = 10000
start_time = 0

maze = []
path_to_end = []

enemies = []
ENEMY_COUNT = 6
ENEMY_RADIUS = 10
ENEMY_SPEED = 0.25

coins = []
COIN_COUNT = 30

bullets = []
BULLET_SPEED = 5
BULLET_RADIUS = 2

gun_rotation_y = 0

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def generate_maze(rows, cols):
    global maze, path_to_end, maze_walls_colors
    maze = [[1 for _ in range(cols * 2 + 1)] for _ in range(rows * 2 + 1)]
    preset_colors = [
        (0.9, 0.2, 0.2),
        (0.2, 0.9, 0.2),
        (0.2, 0.2, 0.9),
        (0.4, 0.1, 0.1),
        (0.1, 0.3, 0.1),
        (0.1, 0.1, 0.3)
    ]
    maze_walls_colors = [[random.choice(preset_colors) for _ in range(cols * 2 + 1)] for _ in range(rows * 2 + 1)]
    stack = []
    start_cell = (random.randint(0, rows - 1), random.randint(0, cols - 1))
    stack.append(start_cell)
    visited = set([start_cell])
    while stack:
        current_row, current_col = stack[-1]
        maze[current_row * 2 + 1][current_col * 2 + 1] = 0
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = current_row + dr, current_col + dc
            if 0 <= new_row < rows and 0 <= new_col < cols and (new_row, new_col) not in visited:
                neighbors.append((new_row, new_col, dr, dc))
        if neighbors:
            next_cell_row, next_cell_col, dr, dc = random.choice(neighbors)
            maze[current_row * 2 + 1 + dr][current_col * 2 + 1 + dc] = 0
            visited.add((next_cell_row, next_cell_col))
            stack.append((next_cell_row, next_cell_col))
        else:
            stack.pop()
    start_r, start_c = random.randint(0, rows - 1), random.randint(0, cols - 1)
    end_r, end_c = random.randint(0, rows - 1), random.randint(0, cols - 1)
    maze[start_r * 2 + 1][start_c * 2 + 1] = 2
    maze[end_r * 2 + 1][end_c * 2 + 1] = 3
    path_to_end = find_path(maze, (start_r * 2 + 1, start_c * 2 + 1), (end_r * 2 + 1, end_c * 2 + 1))
    return maze, (start_r, start_c), (end_r, end_c)

def find_path(grid, start, end):
    queue = [[start]]
    visited = set([start])
    while queue:
        path = queue.pop(0)
        (r, c) = path[-1]
        if (r, c) == end:
            return path
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != 1 and (nr, nc) not in visited:
                new_path = list(path)
                new_path.append((nr, nc))
                queue.append(new_path)
                visited.add((nr, nc))
    return None

def init_game():
    global player_pos, player_angle, player_coins, player_bullets, enemies, coins, bullets, GAME_STATE, start_time, maze, TOP_DOWN_VIEW_TIME, COIN_COUNT, enemy_kill
    maze, start_cell, end_cell = generate_maze(MAZE_ROWS, MAZE_COLS)
    player_pos[0] = MAZE_OFFSET_X + start_cell[1] * CELL_SIZE * 2 + CELL_SIZE
    player_pos[1] = player_height
    player_pos[2] = MAZE_OFFSET_Z + start_cell[0] * CELL_SIZE * 2 + CELL_SIZE
    player_angle = 0
    player_coins = 0
    player_bullets = 20
    TOP_DOWN_VIEW_TIME = 10000
    COIN_COUNT = 30
    enemy_kill = 0
    enemies = []
    coins = []
    bullets = []
    all_cells = [(r, c) for r in range(MAZE_ROWS) for c in range(MAZE_COLS)]
    random.shuffle(all_cells)
    for i in range(ENEMY_COUNT):
        r, c = all_cells.pop()
        enemies.append({
            "pos": [
                MAZE_OFFSET_X + c * CELL_SIZE * 2 + CELL_SIZE,
                player_height,
                MAZE_OFFSET_Z + r * CELL_SIZE * 2 + CELL_SIZE
            ],
            "alive": True
        })
    for i in range(COIN_COUNT):
        r, c = all_cells.pop()
        coins.append({
            "pos": [
                MAZE_OFFSET_X + c * CELL_SIZE * 2 + CELL_SIZE,
                10,
                MAZE_OFFSET_Z + r * CELL_SIZE * 2 + CELL_SIZE
            ],
            "collected": False
        })
    GAME_STATE = "TOP_DOWN"
    start_time = glutGet(GLUT_ELAPSED_TIME)

def draw_maze():
    glPushMatrix()
    glTranslatef(MAZE_OFFSET_X, 0, MAZE_OFFSET_Z)
    global maze
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(MAZE_COLS * 2 * CELL_SIZE, 0, 0)
    glVertex3f(MAZE_COLS * 2 * CELL_SIZE, 0, MAZE_ROWS * 2 * CELL_SIZE)
    glVertex3f(0, 0, MAZE_ROWS * 2 * CELL_SIZE)
    glEnd()
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if maze[r][c] == 1:
                glColor3f(*maze_walls_colors[r][c])
                glPushMatrix()
                x_pos = c * CELL_SIZE
                z_pos = r * CELL_SIZE
                glTranslatef(x_pos, WALL_HEIGHT / 2, z_pos)
                glutSolidCube(CELL_SIZE)
                glColor3f(0, 0, 0)
                glLineWidth(2)
                half = CELL_SIZE / 2
                glBegin(GL_LINES)
                glVertex3f(-half, -half, -half); glVertex3f(half, -half, -half)
                glVertex3f(half, -half, -half); glVertex3f(half, -half, half)
                glVertex3f(half, -half, half); glVertex3f(-half, -half, half)
                glVertex3f(-half, -half, half); glVertex3f(-half, -half, -half)
                glVertex3f(-half, half, -half); glVertex3f(half, half, -half)
                glVertex3f(half, half, -half); glVertex3f(half, half, half)
                glVertex3f(half, half, half); glVertex3f(-half, half, half)
                glVertex3f(-half, half, half); glVertex3f(-half, half, -half)
                glVertex3f(-half, -half, -half); glVertex3f(-half, half, -half)
                glVertex3f(half, -half, -half); glVertex3f(half, half, -half)
                glVertex3f(half, -half, half); glVertex3f(half, half, half)
                glVertex3f(-half, -half, half); glVertex3f(-half, half, half)
                glVertex3f(-half, half, -half); glVertex3f(half, half, half)
                glVertex3f(half, half, -half); glVertex3f(-half, half, half)
                glVertex3f(-half, -half, -half); glVertex3f(half, half, -half)
                glVertex3f(half, -half, -half); glVertex3f(-half, half, -half)
                glVertex3f(-half, -half, half); glVertex3f(half, half, half)
                glVertex3f(half, -half, half); glVertex3f(-half, half, half)
                glVertex3f(-half, -half, -half); glVertex3f(-half, half, half)
                glVertex3f(-half, half, -half); glVertex3f(-half, -half, half)
                glVertex3f(half, -half, -half); glVertex3f(half, half, half)
                glVertex3f(half, half, -half); glVertex3f(half, -half, half)
                glEnd()
                glPopMatrix()
            elif maze[r][c] == 2:
                glColor3f(0.0, 0.0, 0.0)
                glPushMatrix()
                x_pos = c * CELL_SIZE
                z_pos = r * CELL_SIZE
                glTranslatef(x_pos, 1, z_pos)
                glScalef(CELL_SIZE, 2, CELL_SIZE)
                glutSolidCube(1)
                glPopMatrix()
            elif maze[r][c] == 3:
                glColor3f(1, 1, 1)
                glPushMatrix()
                x_pos = c * CELL_SIZE
                z_pos = r * CELL_SIZE
                glTranslatef(x_pos, 1, z_pos)
                glScalef(CELL_SIZE, 2, CELL_SIZE)
                glutSolidCube(1)
                glPopMatrix()
    glPopMatrix()

def draw_player():
    global player_size
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(90, 0, 1, 0)
    glRotatef(-player_angle, 0, 1, 0)
    glScalef(player_size, player_size, player_size)
    glColor3f(1, 0, 0)
    glTranslatef(-18, 54, 0)
    glutSolidCube(36)
    glTranslatef(0, 36, 0)
    glutSolidCube(36)
    glColor3f(0, 1, 0)
    glTranslatef(36, -36, 0)
    glutSolidCube(36)
    glTranslatef(-36, 0, 0)
    glTranslatef(36, 36, 0)
    glutSolidCube(36)
    glTranslatef(-18, 36, 0)
    glColor3f(0, 0, 0)
    gluSphere(gluNewQuadric(), 18, 100, 10)
    glColor3f(0.5, 0.5, 0.5)
    glTranslatef(0, -36, 18)
    gluCylinder(gluNewQuadric(), 24, 3, 90, 10, 10)
    glTranslatef(-36, 0, 0)
    glColor3f(1.0, 0.85, 0.7)
    gluCylinder(gluNewQuadric(), 12, 6, 48, 10, 10)
    glTranslatef(72, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 48, 10, 10)
    glTranslatef(-48, -54, -18)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 48, 10, 10)
    glTranslatef(48, 0, 0)
    gluCylinder(gluNewQuadric(), 12, 6, 48, 10, 10)
    glPopMatrix()

def draw_enemies():
    for enemy in enemies:
        if enemy["alive"]:
            glPushMatrix()
            glTranslatef(enemy["pos"][0], enemy["pos"][1], enemy["pos"][2])
            glColor3f(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
            glutSolidCube(ENEMY_RADIUS * 2)
            glPopMatrix()

def draw_coins():
    for coin in coins:
        if not coin["collected"]:
            glPushMatrix()
            glTranslatef(coin["pos"][0], coin["pos"][1], coin["pos"][2])
            glColor3f(1.0, 1.0, 0.0)
            glutSolidSphere(5, 10, 10)
            glPopMatrix()

def draw_bullets():
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet["pos"][0], bullet["pos"][1], bullet["pos"][2])
        glColor3f(1.0, 1.0, 1.0)
        glutSolidSphere(BULLET_RADIUS, 5, 5)
        glPopMatrix()

def setupCamera():
    global camera_pos, camera_up, camera_target, enemy_kill
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if GAME_STATE == "TOP_DOWN":
        camera_pos = (200, 700, 250)
        camera_target = (200, 0, 250)
        camera_up = (0, 0, -1)
    else:
        dx = math.sin(math.radians(player_angle))
        dz = -math.cos(math.radians(player_angle))
        camera_pos = (player_pos[0], player_pos[1] + player_height, player_pos[2])
        camera_target = (player_pos[0] + dx, player_pos[1] + player_height, player_pos[2] + dz)
        camera_up = (0, 1, 0)
    gluLookAt(
        camera_pos[0], camera_pos[1], camera_pos[2],
        camera_target[0], camera_target[1], camera_target[2],
        camera_up[0], camera_up[1], camera_up[2]
    )

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()
    if GAME_STATE == "PLAYING" or GAME_STATE == "TOP_DOWN":
        draw_maze()
        draw_enemies()
        draw_coins()
        draw_bullets()
        draw_player()
        if GAME_STATE == "PLAYING":
            draw_text(10, WINDOW_HEIGHT - 30, f"Coins: {player_coins}")
            draw_text(10, WINDOW_HEIGHT - 50, f"Bullets: {player_bullets}")
            draw_text(10, WINDOW_HEIGHT - 70, f"Enemy Kills: {enemy_kill}")
    if GAME_STATE == "TOP_DOWN":
        time_left = max(0, TOP_DOWN_VIEW_TIME - (glutGet(GLUT_ELAPSED_TIME) - start_time))
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2, f"Time left: {time_left // 1000}s")
        draw_text(WINDOW_WIDTH/2 - 150, WINDOW_HEIGHT/2 - 30, "Memorize the path! Game starts soon...")
    elif GAME_STATE == "GAME_OVER":
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2, "GAME OVER!")
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 30, f"You collected {player_coins} coins.\nKill Count: {enemy_kill} Press R to restart.")
    elif GAME_STATE == "GAME_WON":
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2, "YOU WON!")
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 30, f"You collected {player_coins} coins.Kill Count: {enemy_kill}")
        draw_text(WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 60, "Press R to restart.")
    glutSwapBuffers()

def update_game_logic():
    global GAME_STATE, game_over_timer, player_bullets, player_coins, maze, TOP_DOWN_VIEW_TIME, start_time, player_size, enemy_kill
    if GAME_STATE == "TOP_DOWN":
        player_size = 0.5
        if glutGet(GLUT_ELAPSED_TIME) - start_time > TOP_DOWN_VIEW_TIME:
            GAME_STATE = "PLAYING"
    elif GAME_STATE == "PLAYING":
        player_size = 0.1
        for enemy in enemies:
            if enemy["alive"]:
                enemy_x = enemy["pos"][0] - MAZE_OFFSET_X
                enemy_z = enemy["pos"][2] - MAZE_OFFSET_Z
                cell_c = int(enemy_x // CELL_SIZE)
                cell_r = int(enemy_z // CELL_SIZE)
                player_x = player_pos[0] - MAZE_OFFSET_X
                player_z = player_pos[2] - MAZE_OFFSET_Z
                player_c = int(player_x // CELL_SIZE)
                player_r = int(player_z // CELL_SIZE)
                queue = deque()
                queue.append([(cell_r, cell_c)])
                visited = set([(cell_r, cell_c)])
                found_path = None
                while queue:
                    path = queue.popleft()
                    r, c = path[-1]
                    if (r, c) == (player_r, player_c):
                        found_path = path
                        break
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < len(maze) and 0 <= nc < len(maze[0]) and maze[nr][nc] != 1 and (nr, nc) not in visited:
                            queue.append(path + [(nr, nc)])
                            visited.add((nr, nc))
                if found_path and len(found_path) > 1:
                    next_r, next_c = found_path[1]
                    target_x = MAZE_OFFSET_X + next_c * CELL_SIZE + CELL_SIZE / 2
                    target_z = MAZE_OFFSET_Z + next_r * CELL_SIZE + CELL_SIZE / 2
                    dx = target_x - enemy["pos"][0]
                    dz = target_z - enemy["pos"][2]
                    dist = math.sqrt(dx**2 + dz**2)
                    if dist > 0:
                        move_dist = min(ENEMY_SPEED, dist)
                        enemy["pos"][0] += (dx / dist) * move_dist
                        enemy["pos"][2] += (dz / dist) * move_dist
                dx = player_pos[0] - enemy["pos"][0]
                dz = player_pos[2] - enemy["pos"][2]
                dist = math.sqrt(dx**2 + dz**2)
                if dist < PLAYER_RADIUS + ENEMY_RADIUS:
                    GAME_STATE = "GAME_OVER"
                    game_over_timer = glutGet(GLUT_ELAPSED_TIME)
        for bullet in bullets[:]:
            bullet["pos"][0] += bullet["dir"][0] * BULLET_SPEED
            bullet["pos"][2] += bullet["dir"][2] * BULLET_SPEED
            for enemy in enemies[:]:
                if enemy["alive"]:
                    dx = bullet["pos"][0] - enemy["pos"][0]
                    dz = bullet["pos"][2] - enemy["pos"][2]
                    dist = math.sqrt(dx**2 + dz**2)
                    if dist < BULLET_RADIUS + ENEMY_RADIUS:
                        corners = [
                            (MAZE_OFFSET_X + CELL_SIZE, player_height, MAZE_OFFSET_Z + CELL_SIZE),
                            (MAZE_OFFSET_X + (MAZE_COLS * 2 - 1) * CELL_SIZE, player_height, MAZE_OFFSET_Z + CELL_SIZE),
                            (MAZE_OFFSET_X + CELL_SIZE, player_height, MAZE_OFFSET_Z + (MAZE_ROWS * 2 - 1) * CELL_SIZE),
                            (MAZE_OFFSET_X + (MAZE_COLS * 2 - 1) * CELL_SIZE, player_height, MAZE_OFFSET_Z + (MAZE_ROWS * 2 - 1) * CELL_SIZE)
                        ]
                        corner = random.choice(corners)
                        enemy["pos"][0], enemy["pos"][1], enemy["pos"][2] = corner
                        bullets.remove(bullet)
                        enemy_kill += 1
                        if enemy_kill % 6 == 0 and enemy_kill > 0:
                            for coin in coins:
                                coin["collected"] = False
                            GAME_STATE = "TOP_DOWN"
                            TOP_DOWN_VIEW_TIME = 5000
                            start_time = glutGet(GLUT_ELAPSED_TIME)
                        break
            if abs(bullet["pos"][0]) > 1000 or abs(bullet["pos"][2]) > 1000:
                if bullet in bullets:
                    bullets.remove(bullet)
        for coin in coins:
            if not coin["collected"]:
                dx = player_pos[0] - coin["pos"][0]
                dz = player_pos[2] - coin["pos"][2]
                dist = math.sqrt(dx**2 + dz**2)
                if dist < PLAYER_RADIUS + 5:
                    coin["collected"] = True
                    player_coins += 1
        end_cell_x = 0
        end_cell_z = 0
        for r in range(len(maze)):
            for c in range(len(maze[0])):
                if maze[r][c] == 3:
                    end_cell_x = MAZE_OFFSET_X + c * CELL_SIZE
                    end_cell_z = MAZE_OFFSET_Z + r * CELL_SIZE
        dx = player_pos[0] - end_cell_x
        dz = player_pos[2] - end_cell_z
        dist = math.sqrt(dx**2 + dz**2)
        if dist < CELL_SIZE:
            GAME_STATE = "GAME_WON"

def keyboardListener(key, x, y):
    global player_pos, player_angle, GAME_STATE, gun_rotation_y, player_bullets, player_coins
    if GAME_STATE == "PLAYING":
        if key == b'w':
            dx = math.sin(math.radians(player_angle)) * player_speed
            dz = -math.cos(math.radians(player_angle)) * player_speed
            new_x = player_pos[0] + dx
            new_z = player_pos[2] + dz
            wall_collided = False
            for r in range(len(maze)):
                for c in range(len(maze[0])):
                    if maze[r][c] == 1:
                        wall_x_min = MAZE_OFFSET_X + c * CELL_SIZE - CELL_SIZE/2
                        wall_x_max = MAZE_OFFSET_X + c * CELL_SIZE + CELL_SIZE/2
                        wall_z_min = MAZE_OFFSET_Z + r * CELL_SIZE - CELL_SIZE/2
                        wall_z_max = MAZE_OFFSET_Z + r * CELL_SIZE + CELL_SIZE/2
                        if (wall_x_min < new_x < wall_x_max) and (wall_z_min < new_z < wall_z_max):
                            wall_collided = True
                            break
                if wall_collided:
                    break
            if not wall_collided:
                player_pos[0] = new_x
                player_pos[2] = new_z
        if key == b's':
            dx = math.sin(math.radians(player_angle)) * player_speed
            dz = -math.cos(math.radians(player_angle)) * player_speed
            new_x = player_pos[0] - dx
            new_z = player_pos[2] - dz
            wall_collided = False
            for r in range(len(maze)):
                for c in range(len(maze[0])):
                    if maze[r][c] == 1:
                        wall_x_min = MAZE_OFFSET_X + c * CELL_SIZE - CELL_SIZE/2
                        wall_x_max = MAZE_OFFSET_X + c * CELL_SIZE + CELL_SIZE/2
                        wall_z_min = MAZE_OFFSET_Z + r * CELL_SIZE - CELL_SIZE/2
                        wall_z_max = MAZE_OFFSET_Z + r * CELL_SIZE + CELL_SIZE/2
                        if (wall_x_min < new_x < wall_x_max) and (wall_z_min < new_z < wall_z_max):
                            wall_collided = True
                            break
                if wall_collided:
                    break
            if not wall_collided:
                player_pos[0] = new_x
                player_pos[2] = new_z
        if key == b'd':
            player_angle += 5
        if key == b'a':
            player_angle -= 5
        if key == b'q':
            if player_coins > 4:
                player_bullets += 1
                player_coins -= 5
    if key == b'r' and (GAME_STATE == "GAME_OVER" or GAME_STATE == "GAME_WON"):
        init_game()

def mouseListener(button, state, x, y):
    global player_bullets, bullets
    if GAME_STATE == "PLAYING":
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and player_bullets > 0:
            dx = math.sin(math.radians(player_angle))
            dz = -math.cos(math.radians(player_angle))
            bullets.append({
                "pos": [player_pos[0], player_pos[1], player_pos[2]],
                "dir": [dx, 0, dz]
            })
            player_bullets -= 1

def idle():
    update_game_logic()
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(10, 0)
    glutCreateWindow(b"The Predator Maze (3D)")
    init_game()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
