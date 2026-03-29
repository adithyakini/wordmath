import streamlit as st
import random
import string

st.set_page_config(page_title="Exorcist WOW", layout="centered")

GRID_SIZE = 10
WORDS = ["APPLE", "TRAIN", "WATER", "LIGHT", "PLANT"]

RIDDLES = {
    "APPLE": "Fruit 🍎",
    "TRAIN": "Runs on tracks 🚆",
    "WATER": "You drink it 💧",
    "LIGHT": "Opposite of dark 💡",
    "PLANT": "Grows in soil 🌱"
}

# -----------------------
# SAFE SESSION INIT
# -----------------------
defaults = {
    "grid": None,
    "path": None,
    "step": 0,
    "word_index": 0,
    "current_input": "",
    "lives": 3,
    "awaiting": False,
    "q": None,
    "a": None,
    "letters": [],
    "message": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------
# BUILD GAME
# -----------------------
def build_game():
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    path = []
    for r in range(GRID_SIZE):
        if r % 2 == 0:
            for c in range(GRID_SIZE):
                path.append((r, c))
        else:
            for c in reversed(range(GRID_SIZE)):
                path.append((r, c))

    idx = 0
    for word in WORDS:
        for ch in word:
            r, c = path[idx]
            grid[r][c] = ch
            idx += 1

    return grid, path

if st.session_state.grid is None:
    grid, path = build_game()
    st.session_state.grid = grid
    st.session_state.path = path

# -----------------------
# MATH
# -----------------------
def gen_q():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", str(a + b)

# -----------------------
# LETTER LOGIC
# -----------------------
def prepare_letters():
    target = WORDS[st.session_state.word_index]
    letters = list(target)
    random.shuffle(letters)
    st.session_state.letters = letters

def click_letter(letter):
    st.session_state.current_input += letter

def undo_letter():
    st.session_state.current_input = st.session_state.current_input[:-1]

def clear_input():
    st.session_state.current_input = ""

def shuffle_letters():
    random.shuffle(st.session_state.letters)

def submit_word():
    target = WORDS[st.session_state.word_index]

    if st.session_state.current_input == target:
        for _ in target:
            st.session_state.step += 1

        st.session_state.message = "✅ Correct!"
        st.session_state.awaiting = True
        st.session_state.current_input = ""
    else:
        st.session_state.message = "❌ Wrong word"
        st.session_state.current_input = ""

# prepare letters if empty
if not st.session_state.letters and st.session_state.word_index < len(WORDS):
    prepare_letters()

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist WOW (Polished)")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    st.success("👻 Exorcism Complete!")
    st.balloons()
    st.stop()

target = WORDS[st.session_state.word_index]

st.info(RIDDLES[target])
st.caption(f"Word: {st.session_state.current_input}")
st.caption(f"Lives: {st.session_state.lives}")

if st.session_state.message:
    st.write(st.session_state.message)

# -----------------------
# LETTER UI
# -----------------------
st.markdown("### 🔤 Choose Letters")

cols = st.columns(len(st.session_state.letters))
for i, l in enumerate(st.session_state.letters):
    if cols[i].button(l, key=f"letter-{i}"):
        click_letter(l)
        st.rerun()

# controls
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("Submit"):
        submit_word()
        st.rerun()
with c2:
    if st.button("Undo"):
        undo_letter()
        st.rerun()
with c3:
    if st.button("Clear"):
        clear_input()
        st.rerun()
with c4:
    if st.button("Shuffle"):
        shuffle_letters()
        st.rerun()

# -----------------------
# GRID (PROGRESS VISUAL)
# -----------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):
        pos = (i, j)

        if pos in st.session_state.path[:st.session_state.step]:
            label = f"🟨 {st.session_state.grid[i][j]}"
        elif pos == st.session_state.path[st.session_state.step]:
            label = "🧙"
        elif pos == st.session_state.path[-1]:
            label = "👻"
        else:
            label = "⬛"

        cols[j].button(label, key=f"grid-{i}-{j}", disabled=True)

# -----------------------
# DOOR SYSTEM
# -----------------------
if st.session_state.awaiting:
    st.markdown("## 🚪 Door Challenge")

    if st.session_state.q is None:
        q, a = gen_q()
        st.session_state.q = q
        st.session_state.a = a

    st.write(st.session_state.q)
    ans = st.text_input("Answer")

    if st.button("Submit Answer"):
        if ans.strip() == st.session_state.a:
            st.success("Door Opened! 🚪")
            st.session_state.word_index += 1
            st.session_state.letters = []
        else:
            st.error("Wrong! Lost a life ❌")
            st.session_state.lives -= 1

        st.session_state.awaiting = False
        st.session_state.q = None
        st.rerun()
