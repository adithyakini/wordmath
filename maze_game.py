import streamlit as st
import random
import string
import time
from openai import OpenAI

client = OpenAI()

GRID_SIZE = 10

# ------------------------
# AI WORDS (5 CONNECTED)
# ------------------------
def get_words(level):
    prompt = f"""
    Generate 5 common English words that can connect sequentially.
    Difficulty: {level}

    Rules:
    - easy: 3-5 letters
    - medium: 4-6 letters
    - hard: 5-8 letters
    - words should be simple and common

    Return comma-separated.
    """

    try:
        res = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )
        words = res.choices[0].message.content.upper().split(",")
        return [w.strip() for w in words][:5]
    except:
        return ["CAT","DOG","SUN","MOON","STAR"]

# ------------------------
# GRID WITH PATH
# ------------------------
def generate_grid(words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    x, y = 0, 0

    directions = [(0,1),(1,0),(0,1),(1,0),(0,1)]  # zig-zag

    for word, (dx,dy) in zip(words, directions):
        for ch in word:
            grid[x][y] = ch
            path.append((x,y))
            x += dx
            y += dy

    return grid, path

# ------------------------
# INIT
# ------------------------
level = st.selectbox("Difficulty", ["easy","medium","hard"])

if "init" not in st.session_state or st.session_state.get("level") != level:

    words = get_words(level)
    grid, path = generate_grid(words)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.words = words
    st.session_state.level = level

    st.session_state.player_index = 0
    st.session_state.start_time = time.time()
    st.session_state.finished = False

    if "leaderboard" not in st.session_state:
        st.session_state.leaderboard = []

    st.session_state.init = True

# ------------------------
# TIMER
# ------------------------
elapsed = int(time.time() - st.session_state.start_time)
st.write(f"⏱️ Time: {elapsed}s")

# ------------------------
# GAME STATE
# ------------------------
grid = st.session_state.grid
path = st.session_state.path
words = st.session_state.words
player_i = st.session_state.player_index

st.title("🧙 Word Path Maze")

st.write(f"Words to find: {' → '.join(words)}")

# ------------------------
# GRID UI
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):

        label = grid[i][j]

        if player_i < len(path) and (i,j) == path[player_i]:
            label = "🧙"
        elif (i,j) in path[:player_i]:
            label = "🟦"
        
        if cols[j].button(label, key=f"{i}-{j}"):

            if st.session_state.finished:
                continue

            # correct next step
            if player_i < len(path) and (i,j) == path[player_i]:
                st.session_state.player_index += 1

                # mysterious sound trigger
                st.audio("https://www.soundjay.com/button/beep-07.wav")

                st.rerun()

            else:
                st.warning("❌ Wrong path")

# ------------------------
# WIN
# ------------------------
if st.session_state.player_index >= len(path) and not st.session_state.finished:

    total_time = int(time.time() - st.session_state.start_time)

    st.success(f"🎉 Completed in {total_time}s")

    st.session_state.leaderboard.append(total_time)
    st.session_state.finished = True

# ------------------------
# LEADERBOARD
# ------------------------
st.subheader("🏆 Leaderboard")

scores = sorted(st.session_state.leaderboard)

for i, s in enumerate(scores[:5]):
    st.write(f"{i+1}. {s}s")

# ------------------------
# RESET
# ------------------------
if st.button("🔄 New Game"):
    st.session_state.clear()
    st.rerun()
