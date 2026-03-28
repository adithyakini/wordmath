import streamlit as st
from openai import OpenAI
import random
import string
import json

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Exorcist Maze NF", layout="centered")
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
    height: 65px;
    font-size: 18px;
    border-radius: 12px;
    transition: 0.2s;
}
div.stButton > button:hover {
    transform: scale(1.08);
    background-color: #333 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# SOUND
# -----------------------
def play(sound):
    sounds = {
        "move": "https://www.soundjay.com/buttons/sounds/button-09.mp3",
        "correct": "https://www.soundjay.com/buttons/sounds/button-3.mp3",
        "wrong": "https://www.soundjay.com/buttons/sounds/button-10.mp3",
        "ghost": "https://www.soundjay.com/human/sounds/scream-01.mp3",
        "win": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3"
    }
    st.markdown(f"<audio autoplay><source src='{sounds[sound]}'></audio>", unsafe_allow_html=True)

# -----------------------
# MAZE
# -----------------------
def build_grid():
    return [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def embed_words(grid):
    path = [(0,0)]
    r,c = 0,0

    for _ in range(40):
        dr,dc = random.choice([(0,1),(1,0),(0,-1),(-1,0)])
        nr,nc = r+dr,c+dc
        if 0<=nr<GRID_SIZE and 0<=nc<GRID_SIZE:
            r,c = nr,nc
            if (r,c) not in path:
                path.append((r,c))

    idx = 0
    for w in WORDS:
        for ch in w:
            if idx < len(path):
                pr,pc = path[idx]
                grid[pr][pc] = ch
                idx += 1

    return grid

# -----------------------
# INIT
# -----------------------
def init():
    if "grid" not in st.session_state:
        st.session_state.grid = embed_words(build_grid())

    defaults = {
        "player": (0,0),
        "ghost": (GRID_SIZE-1, GRID_SIZE-1),
        "path": [(0,0)],
        "word": "",
        "index": 0,
        "awaiting": False,
        "q": None,
        "a": None,
        "lives": 3,
        "combo": 0
    }

    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -----------------------
# HELPERS
# -----------------------
def next_letter():
    target = WORDS[st.session_state.index]
    return target[len(st.session_state.word)] if len(st.session_state.word) < len(target) else None

def move_ghost():
    gr,gc = st.session_state.ghost
    pr,pc = st.session_state.player

    moves = []
    for dr,dc in [(0,1),(1,0),(0,-1),(-1,0)]:
        r,c = gr+dr,gc+dc
        if 0<=r<GRID_SIZE and 0<=c<GRID_SIZE:
            d = abs(r-pr)+abs(c-pc)
            moves.append(((r,c), d))

    moves.sort(key=lambda x: x[1])
    st.session_state.ghost = moves[0][0] if random.random()<0.7 else random.choice(moves)[0]

def reset():
    st.session_state.word = ""
    st.session_state.path = [(0,0)]
    st.session_state.player = (0,0)
    st.session_state.combo = 0

# -----------------------
# AI QUESTION
# -----------------------
def gen_q():
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":"Easy math JSON {question,answer}"}],
            response_format={"type":"json_object"}
        )
        d = json.loads(r.choices[0].message.content)
        return d["question"], str(d["answer"])
    except:
        return "2+2?", "4"

# -----------------------
# MOVE (CORE FIX)
# -----------------------
def handle_move(pos):
    pr, pc = st.session_state.player
    r, c = pos

    if abs(pr-r)+abs(pc-c) != 1:
        return

    play("move")

    st.session_state.player = pos
    st.session_state.path.append(pos)

    letter = st.session_state.grid[r][c]
    target = WORDS[st.session_state.index]
    current = st.session_state.word
    expected = next_letter()

    # ✅ correct
    if letter == expected:
        st.session_state.word += letter
        st.session_state.combo += 1

        if st.session_state.word == target:
            play("correct")
            st.session_state.awaiting = True
            st.balloons()

    # ❌ wrong
    else:
        play("wrong")
        st.warning(f"Expected '{expected}', got '{letter}'")
        st.session_state.lives -= 1
        reset()

    # ghost always moves
    move_ghost()

    # collision
    if st.session_state.player == st.session_state.ghost:
        play("ghost")
        st.error("👻 CAUGHT!")
        st.session_state.lives -= 1
        reset()

    st.rerun()

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist Maze — No Frustration")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.index >= len(WORDS):
    play("win")
    st.success("👻 Exorcism Complete!")
    st.stop()

target = WORDS[st.session_state.index]

st.info(WORD_RIDDLES[target])
st.caption(f"Word: {st.session_state.word}")
st.caption(f"Next: {next_letter()}")
st.caption(f"🔥 Combo: {st.session_state.combo}")

# ghost warning
dist = abs(st.session_state.player[0]-st.session_state.ghost[0]) + abs(st.session_state.player[1]-st.session_state.ghost[1])
if dist <= 2:
    st.error("👻 VERY CLOSE!")
elif dist <= 4:
    st.warning("👻 Nearby...")

# -----------------------
# FOG
# -----------------------
def visible(r,c):
    pr,pc = st.session_state.player
    return abs(pr-r)+abs(pc-c) <= 2

# -----------------------
# DRAW
# -----------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):
        pos = (i,j)
        letter = st.session_state.grid[i][j]

        if not visible(i,j):
            cols[j].markdown("⬛")
            continue

        if pos == st.session_state.player:
            label = "🧙"
        elif pos == st.session_state.ghost:
            label = "👻"
        elif letter == next_letter():
            label = f"✨ {letter}"
        elif pos in st.session_state.path:
            label = f"🟨 {letter}"
        else:
            label = letter

        if cols[j].button(label, key=f"{i}-{j}", use_container_width=True):
            handle_move(pos)

# -----------------------
# CONTROLS
# -----------------------
c1,c2 = st.columns(2)

with c1:
    if st.button("↩️ Undo"):
        if len(st.session_state.path) > 1:
            st.session_state.path.pop()
            st.session_state.word = st.session_state.word[:-1]
            st.session_state.player = st.session_state.path[-1]
            st.rerun()

with c2:
    if st.button("🧹 Reset"):
        reset()
        st.rerun()

# -----------------------
# QUESTION GATE
# -----------------------
if st.session_state.awaiting:
    st.subheader("🚪 Solve to Continue")

    if st.session_state.q is None:
        q,a = gen_q()
        st.session_state.q = q
        st.session_state.a = a

    st.write(st.session_state.q)
    ans = st.text_input("Answer")

    if st.button("Submit"):
        if ans.strip() == st.session_state.a.strip():
            play("correct")
            st.session_state.index += 1
            st.session_state.word = ""
            st.session_state.awaiting = False
            st.session_state.q = None
            st.rerun()
        else:
            play("wrong")
            st.session_state.lives -= 1
            st.session_state.q = None
