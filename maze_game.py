import streamlit as st
import random
import string
import time
from openai import OpenAI
import random
import json
import os

LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f)
        
# ------------------------
# SOUND FUNCTION
# ------------------------
def play_sound(url):
    st.markdown(f"""
        <audio autoplay>
        <source src="{url}" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)
    
THUNDER = "https://www.soundjay.com/nature/thunder-1.mp3"
WRONG = "https://www.soundjay.com/button/beep-10.wav"
WIN = "https://www.soundjay.com/misc/small-bell-ring-01a.mp3"
HEARTBEAT = "https://www.soundjay.com/human/heartbeat-01a.mp3"

if random.random() < 0.05:  # 5% chance each rerun
    play_sound(THUNDER)
    
st.markdown("""
<style>

/* DARK BACKGROUND */
.stApp {
    background: linear-gradient(180deg, #0b0f1a, #111827);
    color: #e5e7eb;
}

/* TILE BUTTONS */
button[kind="secondary"] {
    background-color: #1f2937 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
    border: 1px solid #374151 !important;
}

/* HOVER EFFECT */
button:hover {
    border: 1px solid #22c55e !important;
}

/* TITLE GLOW */
h1 {
    text-shadow: 0 0 10px #60a5fa, 0 0 20px #60a5fa;
}

</style>

<div class="lightning"></div>
""", unsafe_allow_html=True)

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
def generate_full_path():
    path = []
    visited = set()

    x, y = 0, 0
    path.append((x,y))
    visited.add((x,y))

    # force path to reach right edge
    while y < GRID_SIZE - 1:

        moves = [(1,0),(-1,0),(0,1)]
        random.shuffle(moves)

        moved = False

        for dx, dy in moves:
            nx, ny = x+dx, y+dy

            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx,ny) not in visited:
                x, y = nx, ny
                path.append((x,y))
                visited.add((x,y))
                moved = True
                break

        if not moved:
            y += 1
            path.append((x,y))
            visited.add((x,y))

    return path

def generate_words_for_path(path_length, level):

    words = []

    while sum(len(w) for w in words) < path_length:

        new_words = get_words(level)

        for w in new_words:
            words.append(w)

            if sum(len(w) for w in words) >= path_length:
                break

    return words
    
def embed_words_in_grid(path, words):
    grid = [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    i = 0
    for word in words:
        for ch in word:
            if i >= len(path):
                return grid
            x, y = path[i]
            grid[x][y] = ch
            i += 1

    return grid
    # ------------------------
    # EMBED WORDS INTO PATH
    # ------------------------
    i = 0
    for word in words:
        for ch in word:
            if i < len(path):
                px, py = path[i]
                grid[px][py] = ch
                i += 1

    return grid, path

# ------------------------
# INIT
# ------------------------
if "init" not in st.session_state or st.session_state.get("level") != level:

    path = generate_full_path()

    words = generate_words_for_path(len(path), level)

    grid = embed_words_in_grid(path, words)

    st.session_state.grid = grid
    st.session_state.path = path
    st.session_state.words = words
    st.session_state.level = level
    st.session_state.entry = path[0]
    st.session_state.exit = path[-1]
    st.session_state.index = -1
    st.session_state.lives = 3
    st.session_state.wrong_tiles = set()
    st.session_state.start_time = time.time()
    st.session_state.finished = False
    st.session_state.current_word_index = 0
    st.session_state.letters_progress = 0
    st.session_state.init = True
    
    st.session_state.current_word_index = 0
    st.session_state.letters_progress = 0

    st.session_state.play_wrong = False
    st.session_state.play_win = False
    st.session_state.play_heartbeat = False                

# leaderboard init
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = load_leaderboard()

# ------------------------
# TIMER (FIXED)
# ------------------------
if st.session_state.finished:
    elapsed = st.session_state.get("final_time", 0)
else:
    elapsed = int(time.time() - st.session_state.start_time)

# ------------------------
# UI
# ------------------------

with st.sidebar:
    st.title("🧠 How to Play")

    st.markdown("""
    **🧙 Objective**
    - Enter through the gate
    - Follow the hidden word path
    - Reach the ghost 👻 and perform the exorcism

    **🎯 Rules**
    - Move step-by-step along the correct path
    - Each step builds a word
    - Complete words to progress

    **❤️ Lives**
    - You have 3 lives
    - Wrong tile = lose 1 life

    **🧩 Words**
    - Words are revealed gradually
    - Complete current word to unlock next

    **🏁 Goal**
    - Reach the exit gate
    - Perform the exorcism faster for leaderboard!
    """)
    
st.title("🧙 Om Bhool Bhulaiya Swaahaa")

st.write(f"⏱️ Time: {elapsed}s | ❤️ Lives: {st.session_state.lives}")
current_idx = min(st.session_state.current_word_index, len(st.session_state.words) - 1)
words = st.session_state.words

current_idx = st.session_state.current_word_index
letters_done = st.session_state.letters_progress
words = st.session_state.words

display = []

for i, w in enumerate(words):

    # COMPLETED words
    if i < current_idx:
        display.append(w)

    # CURRENT word (partial reveal)
    elif i == current_idx:

        revealed = ""
        for j, ch in enumerate(w):
            if j < letters_done:
                revealed += ch + " "
            else:
                revealed += "_ "

        display.append(f"👉 {revealed.strip()}")

    # FUTURE words
    else:
        display.append("???")

st.write("Words:", " → ".join(display))

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
                    st.session_state.letters_progress += 1
                    if st.session_state.current_word_index < len(st.session_state.words):
                        current_word = st.session_state.words[st.session_state.current_word_index]
                    else:
                        current_word = ""
                    if (st.session_state.current_word_index < len(st.session_state.words)
                        and st.session_state.letters_progress >= len(current_word)):
                            st.session_state.current_word_index += 1
                            st.session_state.letters_progress = 0
                    st.rerun()
                else:
                    st.session_state.lives -= 1
                    play_sound(WRONG)
                    if st.session_state.lives == 1:
                        play_sound(HEARTBEAT)
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

    st.session_state.final_time = final_time
    st.session_state.finished = True

    leaderboard = st.session_state.leaderboard

    # check if qualifies for top 5
    qualifies = (
        len(leaderboard) < 5 or
        final_time < max(entry["time"] for entry in leaderboard)
    )

    if qualifies:
        st.session_state.new_high_score = True
    else:
        st.success(f"✨ Completed in {final_time}s!")

if st.session_state.get("new_high_score", False):

    st.success(f"🏆 New High Score! Time: {st.session_state.final_time}s")

    name = st.text_input("Enter your name:")

    if st.button("Submit Score"):

        leaderboard = st.session_state.leaderboard

        leaderboard.append({
            "name": name if name else "Anonymous",
            "time": st.session_state.final_time
        })

        # sort and keep top 5
        leaderboard = sorted(leaderboard, key=lambda x: x["time"])[:5]

        save_leaderboard(leaderboard)

        st.session_state.leaderboard = leaderboard
        st.session_state.new_high_score = False

        st.success("Score saved!")
        
# ------------------------
# LEADERBOARD
# ------------------------
st.subheader("🏆 Leaderboard")

for i, entry in enumerate(st.session_state.leaderboard):
    st.write(f"{i+1}. {entry['name']} - {entry['time']}s")

# ------------------------
# RESET
# ------------------------
if st.button("🔄 New Game"):

    leaderboard = st.session_state.leaderboard

    st.session_state.clear()

    st.session_state.leaderboard = leaderboard

    st.rerun()
