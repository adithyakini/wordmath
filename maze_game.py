import streamlit as st
import random
import string
from openai import OpenAI

GRID_SIZE = 6
client = OpenAI()

# ------------------------
# AI WORDS
# ------------------------
def get_ai_words(level="easy"):
    prompt = f"""
    Generate 6 common English words.
    Difficulty: {level}
    Easy: 3-5 letters
    Medium: 4-6 letters
    Hard: 5-8 letters

    Words should share letters if possible.

    Return comma-separated only.
    """

    try:
        res = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )
        words = res.choices[0].message.content.upper().split(",")
        return [w.strip() for w in words if w.strip()]
    except:
        return ["CAT","DOG","SUN","MOON","STAR","FIRE"]

# ------------------------
# PREFIXES
# ------------------------
def build_prefixes(words):
    p = set()
    for w in words:
        for i in range(len(w)):
            p.add(w[:i+1])
    return p

# ------------------------
# PATH GENERATION (DFS)
# ------------------------
def generate_path():
    path = []
    visited = set()

    def dfs(x, y):
        path.append((x,y))
        visited.add((x,y))

        if len(path) >= GRID_SIZE * 2:
            return True

        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(dirs)

        for dx, dy in dirs:
            nx, ny = x+dx, y+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx,ny) not in visited:
                if dfs(nx, ny):
                    return True

        path.pop()
        return False

    dfs(0,0)
    return path

# ------------------------
# GRID WITH EMBEDDED WORDS
# ------------------------
def generate_solvable_grid(words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = generate_path()

    i = 0
    for word in words:
        for ch in word:
            if i < len(path):
                x,y = path[i]
                grid[x][y] = ch
                i += 1

    return grid

# ------------------------
# NEIGHBORS
# ------------------------
def neighbors(x,y):
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    return [(x+dx,y+dy) for dx,dy in dirs if 0 <= x+dx < GRID_SIZE and 0 <= y+dy < GRID_SIZE]

# ------------------------
# GHOST
# ------------------------
def move_ghost(g, p):
    gx, gy = g
    px, py = p

    if abs(px-gx) > abs(py-gy):
        gx += 1 if px > gx else -1 if px < gx else 0
    else:
        gy += 1 if py > gy else -1 if py < gy else 0

    return (gx, gy)

# ------------------------
# INIT
# ------------------------
level = st.selectbox("Difficulty", ["easy","medium","hard"])

if "init" not in st.session_state or st.session_state.get("level") != level:

    words = get_ai_words(level)
    prefixes = build_prefixes(words)
    grid = generate_solvable_grid(words)

    st.session_state.words = words
    st.session_state.prefixes = prefixes
    st.session_state.grid = grid
    st.session_state.level = level

    st.session_state.player = (0,0)
    st.session_state.ghost = (GRID_SIZE-1, GRID_SIZE-1)

    start_letter = grid[0][0]

    st.session_state.word = start_letter
    st.session_state.visited = {(0,0)}
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.init = True

# ------------------------
# STATE
# ------------------------
grid = st.session_state.grid
player = st.session_state.player
ghost = st.session_state.ghost
word = st.session_state.word
visited = st.session_state.visited
words = st.session_state.words
prefixes = st.session_state.prefixes

st.title("🧙 Word Maze (Solvable)")

st.write(f"Word: **{word}**")
st.write(f"Score: {st.session_state.score}")
st.write(f"Words: {', '.join(words)}")

# ------------------------
# VALID MOVES
# ------------------------
valid_moves = []
for nx, ny in neighbors(*player):
    if (nx,ny) not in visited:
        new_word = word + grid[nx][ny]
        if new_word in prefixes:
            valid_moves.append((nx,ny))

# ------------------------
# GRID UI
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
                st.stop()

            if (i,j) in valid_moves:

                new_word = word + grid[i][j]

                st.session_state.player = (i,j)
                st.session_state.word = new_word
                st.session_state.visited.add((i,j))

                if new_word in words:
                    st.success(f"✅ {new_word}")
                    st.session_state.score += len(new_word)
                    st.session_state.word = ""
                    st.session_state.visited = {st.session_state.player}

                st.session_state.ghost = move_ghost(ghost, st.session_state.player)

                st.rerun()

            else:
                st.warning("❌ Invalid move")

# ------------------------
# GAME OVER
# ------------------------
if st.session_state.player == st.session_state.ghost:
    st.error("💀 Ghost caught you")
    st.session_state.game_over = True

if len(valid_moves) == 0:
    st.error("🚫 No moves left")
    st.session_state.game_over = True

# ------------------------
# RESET
# ------------------------
if st.button("🔄 Restart"):
    st.session_state.clear()
    st.rerun()
