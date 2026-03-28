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
# STYLE
# -----------------------
st.markdown("""
<style>
div.stButton > button {
    height: 70px;
    font-size: 20px;
    border-radius: 10px;
    transition: all 0.2s ease;
}
div.stButton > button:hover {
    transform: scale(1.1);
    background-color: #444 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# SOUND
# -----------------------
def play_sound(sound):
    sounds = {
        "move": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "correct": "https://www.soundjay.com/buttons/sounds/button-3.mp3",
        "wrong": "https://www.soundjay.com/buttons/sounds/button-10.mp3",
        "ghost": "https://www.soundjay.com/human/sounds/scream-01.mp3",
        "win": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3"
    }

    st.markdown(f"""
        <audio autoplay>
        <source src="{sounds[sound]}" type="audio/mp3">
        </audio>
    """, unsafe_allow_html=True)

# -----------------------
# BUILD MAZE
# -----------------------
def build_game():
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = [(0, 0)]
    r, c = 0, 0

    # random branching path
    for _ in range(40):
        dr, dc = random.choice([(0,1),(1,0),(0,-1),(-1,0)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            r, c = nr, nc
            if (r, c) not in path:
                path.append((r, c))

    # embed words
    idx = 0
    for w in WORDS:
        for ch in w:
            if idx < len(path):
                pr, pc = path[idx]
                grid[pr][pc] = ch
                idx += 1

    st.session_state.grid = grid

# -----------------------
# INIT
# -----------------------
def init():
    if "grid" not in st.session_state:
        build_game()

    defaults = {
        "player": (0, 0),
        "ghost": (GRID_SIZE-1, GRID_SIZE-1),
        "path_taken": [(0, 0)],
        "current_word": "",
        "word_index": 0,
        "awaiting": False,
        "question": None,
        "answer": None,
        "lives": 3
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -----------------------
# AI SAFE
# -----------------------
def generate_question():
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Simple math question JSON {question, answer}"}],
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return data.get("question", "2+2?"), str(data.get("answer", "4"))
    except:
        return "2+2?", "4"

# -----------------------
# WORD HELPERS
# -----------------------
def get_next_letter():
    target = WORDS[st.session_state.word_index]
    current = st.session_state.current_word
    if len(current) < len(target):
        return target[len(current)]
    return None

def get_valid_moves():
    pr, pc = st.session_state.player
    next_letter = get_next_letter()
    valid = []

    for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
        r, c = pr+dr, pc+dc
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            if st.session_state.grid[r][c] == next_letter:
                valid.append((r, c))
    return valid

# -----------------------
# GHOST AI
# -----------------------
def move_ghost():
    gr, gc = st.session_state.ghost
    pr, pc = st.session_state.player

    best = (gr, gc)
    dist = abs(gr-pr) + abs(gc-pc)

    for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
        r, c = gr+dr, gc+dc
        if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
            d = abs(r-pr) + abs(c-pc)
            if d < dist:
                dist = d
                best = (r, c)

    st.session_state.ghost = best

# -----------------------
# DRAW
# -----------------------
def draw():
    valid_moves = get_valid_moves()

    for i in range(GRID_SIZE):
        cols = st.columns(GRID_SIZE)
        for j in range(GRID_SIZE):
            pos = (i, j)
            player = st.session_state.player
            ghost = st.session_state.ghost
            letter = st.session_state.grid[i][j]

            if pos == player:
                label = "🧙"
            elif pos == ghost:
                label = "👻"
            elif pos in valid_moves:
                label = f"✨ {letter}"
            elif pos in st.session_state.path_taken:
                label = f"🟨 {letter}"
            else:
                label = letter

            if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
                move(pos)

# -----------------------
# MOVE
# -----------------------
def move(pos):
    pr, pc = st.session_state.player
    r, c = pos

    if abs(pr-r)+abs(pc-c) != 1:
        return

    if pos in st.session_state.path_taken:
        return

    play_sound("move")
    st.session_state.player = pos
    st.session_state.path_taken.append(pos)
    st.session_state.current_word += st.session_state.grid[r][c]

    check_word()

    move_ghost()

    if st.session_state.player == st.session_state.ghost:
        play_sound("ghost")
        st.error("👻 Caught!")
        st.session_state.lives -= 1
        reset_word()

    st.rerun()

# -----------------------
# WORD CHECK
# -----------------------
def check_word():
    current = st.session_state.current_word
    target = WORDS[st.session_state.word_index]

    if current == target:
        play_sound("correct")
        st.balloons()
        st.session_state.awaiting = True

    elif not target.startswith(current):
        play_sound("wrong")
        st.session_state.lives -= 1
        reset_word()

# -----------------------
# RESET / UNDO
# -----------------------
def reset_word():
    st.session_state.current_word = ""
    st.session_state.path_taken = [st.session_state.path_taken[0]]
    st.session_state.player = st.session_state.path_taken[0]

def undo():
    if len(st.session_state.path_taken) > 1:
        st.session_state.path_taken.pop()
        st.session_state.current_word = st.session_state.current_word[:-1]
        st.session_state.player = st.session_state.path_taken[-1]

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Maze")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    play_sound("win")
    st.success("👻 Exorcism Complete!")
    st.stop()

target = WORDS[st.session_state.word_index]

st.markdown("## 🧩 Riddle")
st.info(WORD_RIDDLES[target])
st.caption(f"Progress: {st.session_state.current_word}")
st.caption(f"Next letter: {get_next_letter()}")

draw()

# CONTROLS
c1, c2 = st.columns(2)
with c1:
    if st.button("↩️ Undo"):
        undo()
        st.rerun()
with c2:
    if st.button("🧹 Reset"):
        reset_word()
        st.rerun()

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
            play_sound("correct")
            st.session_state.word_index += 1
            st.session_state.current_word = ""
            st.session_state.awaiting = False
            st.session_state.question = None
            st.rerun()
        else:
            play_sound("wrong")
            st.session_state.lives -= 1
