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
# BUILD SNAKE PATH GRID
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

# -----------------------
# INIT
# -----------------------
if "init" not in st.session_state:
    grid, path = build_game()

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.step = 0
    st.session_state.word_index = 0
    st.session_state.current_input = ""
    st.session_state.lives = 3
    st.session_state.awaiting = False
    st.session_state.q = None
    st.session_state.a = None
    st.session_state.init = True

# -----------------------
# MATH
# -----------------------
def gen_q():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", str(a + b)

# -----------------------
# WORD INPUT (WOW STYLE)
# -----------------------
def click_letter(letter):
    st.session_state.current_input += letter

def submit_word():
    target = WORDS[st.session_state.word_index]

    if st.session_state.current_input == target:
        # reveal path automatically
        for _ in target:
            st.session_state.step += 1

        st.session_state.awaiting = True
        st.session_state.current_input = ""
    else:
        st.warning("Wrong word! Try again")
        st.session_state.current_input = ""

# -----------------------
# UI
# -----------------------
st.title("🧙 Exorcist WOW Mode")

if st.session_state.lives <= 0:
    st.error("💀 Game Over")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
    st.stop()

if st.session_state.word_index >= len(WORDS):
    st.success("👻 You reached the ghost! Exorcism complete!")
    st.stop()

target = WORDS[st.session_state.word_index]

st.info(RIDDLES[target])
st.caption(f"Your word: {st.session_state.current_input}")
st.caption(f"Lives: {st.session_state.lives}")

# -----------------------
# LETTER BANK (WOW STYLE)
# -----------------------
letters = list(target)
random.shuffle(letters)

cols = st.columns(len(letters))
for i, l in enumerate(letters):
    if cols[i].button(l):
        click_letter(l)
        st.rerun()

# controls
c1, c2 = st.columns(2)
with c1:
    if st.button("Submit"):
        submit_word()
        st.rerun()

with c2:
    if st.button("Clear"):
        st.session_state.current_input = ""
        st.rerun()

# -----------------------
# DRAW GRID (AUTO REVEAL)
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

        cols[j].button(label, key=f"{i}-{j}", disabled=True)

# -----------------------
# DOOR SYSTEM
# -----------------------
if st.session_state.awaiting:
    st.subheader("🚪 Solve to Continue")

    if st.session_state.q is None:
        q, a = gen_q()
        st.session_state.q = q
        st.session_state.a = a

    st.write(st.session_state.q)
    ans = st.text_input("Answer")

    if st.button("Submit Answer"):
        if ans.strip() == st.session_state.a:
            st.success("Door opened! ✅")
            st.session_state.word_index += 1
        else:
            st.error("Wrong! Lost a life ❌")
            st.session_state.lives -= 1

        st.session_state.awaiting = False
        st.session_state.q = None
        st.rerun()
