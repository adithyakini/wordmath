import streamlit as st
import random
import string
import time
from openai import OpenAI

GRID_SIZE = 10
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------------------
# DIFFICULTY
# ------------------------
level = st.selectbox("Difficulty", ["easy","medium","hard"])

# ------------------------
# AI WORDS
# ------------------------
def get_words(level):

    if level == "easy":
        rule = "exactly 3 letters"
    elif level == "medium":
        rule = "4 to 5 letters"
    else:
        rule = "6 or more letters"

    prompt = f"""
    Generate 5 common English words.

    Rules:
    - Each word must be {rule}
    - Words must be simple and common
    - Return ONLY comma-separated words
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    words = [w.strip().upper() for w in res.choices[0].message.content.split(",")]
    return words

# ------------------------
# PATH GENERATION
# ------------------------
def generate_branching_path(words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    x, y = 0, 0

    for word in words:
        for ch in word:
            grid[x][y] = ch
            path.append((x,y))

            moves = [(1,0),(0,1),(-1,0),(0,-1)]
            random.shuffle(moves)

            for dx, dy in moves:
                nx, ny = x+dx, y+dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx,ny) not in path:
                    x, y = nx, ny
                    break

    return grid, path

# ------------------------
# INIT
# ------------------------
if "init" not in st.session_state or st.session_state.get("level") != level:

    words = get_words(level)
    grid, path = generate_branching_path(words)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.words = words
    st.session_state.level = level

    st.session_state.entry = path[0]
    st.session_state.exit = path[-1]

    st.session_state.index = -1  # wizard outside
    st.session_state.lives = 3
    st.session_state.wrong_tiles = set()
    st.session_state.start_time = time.time()
    st.session_state.finished = False

    st.session_state.init = True

# leaderboard init
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = []

# ------------------------
# TIMER
# ------------------------
if not st.session_state.finished:
    elapsed = int(time.time() - st.session_state.start_time)
else:
    elapsed = st.session_state.final_time

# ------------------------
# UI
# ------------------------
st.title("🧙 Word Maze Exorcism")

st.write(f"⏱️ Time: {elapsed}s | ❤️ Lives: {st.session_state.lives}")
st.write(f"Words: {' → '.join(st.session_state.words)}")

grid = st.session_state.grid
path = st.session_state.path
idx = st.session_state.index

# ------------------------
# GRID
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE + 2)

    for j in range(GRID_SIZE + 2):

        # ENTRY SIDE
        if j == 0:
            if i == st.session_state.entry[0]:
                label = "🚪🧙" if idx == -1 else "🚪"
            else:
                label = ""
            cols[j].button(label, key=f"{i}-entry")
            continue

        # EXIT SIDE
        if j == GRID_SIZE + 1:
            if i == st.session_state.exit[0]:
                label = "👻🚪"
            else:
                label = ""
            cols[j].button(label, key=f"{i}-exit")
            continue

        x, y = i, j-1
        base = grid[x][y]

        # wizard
        if idx >= 0 and idx < len(path) and (x,y) == path[idx]:
            label = "🧙"

        # correct path
        elif idx >= 0 and (x,y) in path[:idx]:
            label = f"🟩{base}"

        # wrong
        elif (x,y) in st.session_state.wrong_tiles:
            label = f"🟥{base}🔴"

        else:
            label = base

        if cols[j].button(label, key=f"{x}-{y}"):

            if st.session_state.finished:
                continue

            current_index = st.session_state.index

            # ENTER MAZE
            if current_index == -1:
                if (x,y) == st.session_state.entry:
                    st.session_state.index = 0
                    st.rerun()
                else:
                    st.session_state.lives -= 1
                    st.session_state.wrong_tiles.add((x,y))
                    st.warning("Enter through the gate!")

            # NORMAL MOVE
            else:
                next_index = current_index + 1

                if next_index < len(path) and (x,y) == path[next_index]:
                    st.session_state.index = next_index
                    st.rerun()
                else:
                    st.session_state.lives -= 1
                    st.session_state.wrong_tiles.add((x,y))
                    st.warning("Wrong path!")

            if st.session_state.lives <= 0:
                st.error("💀 Game Over")
                st.session_state.finished = True

# ------------------------
# WIN (EXORCISM)
# ------------------------
if idx == len(path) - 1 and not st.session_state.finished:

    final_time = int(time.time() - st.session_state.start_time)

    st.success(f"✨ Exorcism complete in {final_time}s!")

    st.session_state.leaderboard.append(final_time)
    st.session_state.final_time = final_time
    st.session_state.finished = True

# ------------------------
# LEADERBOARD
# ------------------------
st.subheader("🏆 Leaderboard")

for i, t in enumerate(sorted(st.session_state.leaderboard)[:5]):
    st.write(f"{i+1}. {t}s")

# ------------------------
# RESET
# ------------------------
if st.button("🔄 New Game"):
    st.session_state.clear()
    st.rerun()
