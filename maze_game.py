import streamlit as st
import random
import string

GRID_SIZE = 8

# ------------------------
# WORD POOL
# ------------------------
WORDS = ["CAT", "DOG", "SUN", "MOON", "STAR", "FIRE", "WIND", "TREE", "ROCK"]

# ------------------------
# UTILS
# ------------------------
def get_neighbors(x, y):
    moves = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return [(i,j) for i,j in moves if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE]

# ------------------------
# MAZE GENERATOR (DFS)
# ------------------------
def generate_maze():
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    start = (0, 0)
    visited = set()
    path = []

    def dfs(x, y):
        visited.add((x,y))
        path.append((x,y))

        if len(path) > GRID_SIZE * 2:
            return True

        neighbors = get_neighbors(x,y)
        random.shuffle(neighbors)

        for nx, ny in neighbors:
            if (nx,ny) not in visited:
                if dfs(nx, ny):
                    return True

        path.pop()
        return False

    dfs(0,0)

    # embed words along path
    word_path = []
    i = 0
    for word in WORDS[:5]:
        for char in word:
            if i < len(path):
                x,y = path[i]
                grid[x][y] = char
                word_path.append((x,y))
                i += 1

    goal = word_path[-1]

    return grid, word_path, goal

# ------------------------
# VALID MOVES (SMART)
# ------------------------
def get_valid_moves(player, path):
    neighbors = get_neighbors(*player)
    return [n for n in neighbors if n in path]

# ------------------------
# GHOST AI
# ------------------------
def move_ghost(ghost, player):
    gx, gy = ghost
    px, py = player

    if abs(px - gx) > abs(py - gy):
        gx += 1 if px > gx else -1 if px < gx else 0
    else:
        gy += 1 if py > gy else -1 if py < gy else 0

    return (gx, gy)

# ------------------------
# INIT
# ------------------------
if "grid" not in st.session_state:
    grid, path, goal = generate_maze()
    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.goal = goal
    st.session_state.player = (0,0)
    st.session_state.ghost = goal
    st.session_state.game_over = False

grid = st.session_state.grid
player = st.session_state.player
ghost = st.session_state.ghost
goal = st.session_state.goal

st.title("🧙 Smart Word Maze")

valid_moves = get_valid_moves(player, st.session_state.path)

# ------------------------
# GRID RENDER
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):

        label = grid[i][j]

        if (i,j) == player:
            label = "🧙"
        elif (i,j) == ghost:
            label = "👻"
        elif (i,j) in valid_moves:
            label = f"🟩{grid[i][j]}"

        if cols[j].button(label, key=f"{i}-{j}"):

            if st.session_state.game_over:
                continue

            if (i,j) in valid_moves:
                st.session_state.player = (i,j)

                # move ghost AFTER player
                st.session_state.ghost = move_ghost(st.session_state.ghost, st.session_state.player)

            else:
                st.warning("❌ Invalid move")

# ------------------------
# GAME STATES
# ------------------------
if st.session_state.player == goal:
    st.success("🎉 You reached the ghost!")

if st.session_state.player == st.session_state.ghost:
    st.error("💀 Ghost caught you!")
    st.session_state.game_over = True

# ------------------------
# RESET
# ------------------------
if st.button("🔄 Restart"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
