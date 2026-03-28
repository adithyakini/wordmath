import streamlit as st
from openai import OpenAI
import json
import random
import string

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Exorcist Maze", layout="centered")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

GRID_SIZE = 7

WORDS = ["APPLE", "TRAIN", "WATER"]

WORD_RIDDLES = {
    "APPLE": "Fruit that keeps the doctor away 🍎",
    "TRAIN": "Runs on tracks 🚆",
    "WATER": "You drink it 💧"
}

# -----------------------
# BUILD GAME
# -----------------------
def build_game():
    grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    r, c = 0, 0
    path.append((r, c))

    for _ in range(1, GRID_SIZE * GRID_SIZE):
        if c < GRID_SIZE - 1:
            c += 1
        else:
            r += 1
            c = 0
        if r < GRID_SIZE:
            path.append((r, c))

    full_letters = []
    for w in WORDS:
        full_letters += list(w)

    for (r, c), letter in zip(path, full_letters):
        grid[r][c] = letter

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == "":
                grid[i][j] = random.choice(string.ascii_uppercase)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.full_letters = full_letters

# -----------------------
# INIT
# -----------------------
def init():
    if "grid" not in st.session_state:
        build_game()

    if "player_idx" not in st.session_state:
        st.session_state.player_idx = 0

    if "current_word_progress" not in st.session_state:
        # ✅ FIX: include first letter automatically
        first_letter = st.session_state.grid[0][0]
        st.session_state.current_word_progress = first_letter

    if "word_index" not in st.session_state:
        st.session_state.word_index = 0

    if "awaiting" not in st.session_state:
        st.session_state.awaiting = False

    if "question" not in st.session_state:
        st.session_state.question = None

    if "answer" not in st.session_state:
        st.session_state.answer = None

    if "lives" not in st.session_state:
        st.session_state.lives = 3

init()

# -----------------------
# AI
# -----------------------
def generate_question():
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "Generate simple math question + answer JSON"
        }],
        response_format={"type": "json_object"}
    )

    data = json.loads(res.choices[0].message.content)
    return data["question"], str(data["answer"])

# -----------------------
# DRAW
# -----------------------
def draw():
    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)

        for j in range(GRID_SIZE):
            pos = (i, j)
            player_pos = st.session_state.path[st.session_state.player_idx]

            if pos == player_pos:
                label = "🧙"
            elif pos == st.session_state.path[-1]:
                label = "👻"
            else:
                label = st.session_state.grid[i][j]

            if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
                handle_click(pos)

# -----------------------
# MOVE
# -----------------------
def handle_click(pos):
    idx = st.session_state.player_idx

    if idx + 1 >= len(st.session_state.path):
        return

    next_pos = st.session_state.path[idx + 1]

    if pos != next_pos:
        st.warning("❌ Wrong path!")
        return

    letter = st.session_state.grid[pos[0]][pos[1]]

    st.session_state.current_word_progress += letter
    st.session_state.player_idx += 1

    current_word = WORDS[st.session_state.word_index]

    if st.session_state.current_word_progress == current_word:
        st.success(f"🎉 Word completed: {current_word}")
        st.session_state.awaiting = True

    st.rerun()

# -----------------------
# RETRACE FUNCTIONS
# -----------------------
def undo_move():
    if st.session_state.player_idx > 0:
        st.session_state.player_idx -= 1
        st.session_state.current_word_progress = st.session_state.current_word_progress[:-1]
        st.rerun()

def reset_word():
    # reset to start of current word
    word_start_idx = sum(len(w) for w in WORDS[:st.session_state.word_index])

    st.session_state.player_idx = word_start_idx
    st.session_state.current_word_progress = ""
    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Word Maze")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    st.success("👻 Exorcism Complete! You Win!")
    st.stop()

current_word = WORDS[st.session_state.word_index]

st.markdown("## 🧩 Riddle")
st.info(WORD_RIDDLES[current_word])

st.caption(f"Progress: {st.session_state.current_word_progress}")

draw()

# -----------------------
# CONTROLS
# -----------------------
st.markdown("### 🎮 Controls")
c1, c2 = st.columns(2)

with c1:
    if st.button("↩️ Undo"):
        undo_move()

with c2:
    if st.button("🧹 Reset Word"):
        reset_word()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting:
    st.markdown("## 🚪 Solve to Proceed")

    if st.session_state.question is None:
        q, a = generate_question()
        st.session_state.question = q
        st.session_state.answer = a

    st.write(st.session_state.question)
    ans = st.text_input("Answer")

    if st.button("Submit"):
        if ans.strip() == st.session_state.answer.strip():
            st.success("🚪 Door opened!")

            st.session_state.current_word_progress = ""
            st.session_state.word_index += 1
            st.session_state.awaiting = False
            st.session_state.question = None

            st.rerun()
        else:
            st.error("❌ Wrong answer!")
            st.session_state.lives -= 1
