import streamlit as st
import random
import string
import time
from openai import OpenAI
import random
import json
import os
import base64


def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

chucky_base64 = get_base64_image("chucky.png")

        
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
def play_loop_sound_base64(path):
    import base64
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <audio autoplay loop>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)


    
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
        rule = "exactly 4 letter very simple words for kids (like BOOK, TREE, BALL, FISH)"
    elif level == "medium":
        rule = "exactly 5 letter common words (like APPLE, WATER, LIGHT)"
    else:
        rule = "6 or more letter words (like SHADOW, MYSTIC, PLANET)"

    prompt = f"""
    Generate 10 English words.

    Rules:
    - {rule}
    - Words must be common and easy to recognize
    - No obscure or rare words
    - No duplicates

    Return ONLY comma-separated words.
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.8,
        messages=[{"role": "user", "content": prompt}]
    )

    return [w.strip().upper() for w in res.choices[0].message.content.split(",")]

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
    st.session_state.show_intro = True
    st.session_state.current_word_index = 0
    st.session_state.letters_progress = 0

    st.session_state.chucky_active = True
    st.session_state.chucky_sound_played = False
    st.session_state.completed_words = set()
    

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

if st.session_state.get("show_intro", False):

    exit_row = st.session_state.exit[0]

    x_percent = 85
    y_percent = 10 + (exit_row / GRID_SIZE) * 70

    st.markdown(f"""
    <style>

    @keyframes shake {{
        0% {{ transform: translate(0px, 0px); }}
        25% {{ transform: translate(5px, -5px); }}
        50% {{ transform: translate(-5px, 5px); }}
        75% {{ transform: translate(5px, 5px); }}
        100% {{ transform: translate(0px, 0px); }}
    }}

    .stApp {{
        animation: shake 0.4s;
    }}

    .chucky-container {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: cinematicMove 4s forwards;
        z-index: 9999;
        pointer-events: none;
    }}

    .chucky-container img {{
        width: 75vw;
        max-width: 900px;
        border-radius: 20px;
    }}

    @keyframes cinematicMove {{
        0% {{
            transform: translate(-50%, -50%) scale(0.2);
            opacity: 0;
        }}
        10% {{
            transform: translate(-50%, -50%) scale(2.5);
            opacity: 1;
        }}
        20% {{
            transform: translate(-50%, -50%) scale(1.8);
        }}
        40% {{
            transform: translate(-50%, -50%) scale(1.2);
        }}
        75% {{
            transform: translate({x_percent}vw, {y_percent}vh) scale(0.4);
        }}
        100% {{
            transform: translate({x_percent}vw, {y_percent}vh) scale(0.05);
            opacity: 0;
        }}
    }}

    </style>

    <div class="chucky-container">
        <img src="data:image/png;base64,{chucky_base64}">
    </div>
    """, unsafe_allow_html=True)

    # ✅ WAIT → THEN CONTINUE GAME
    time.sleep(4)

    st.session_state.show_intro = False
    st.rerun()
    
with st.sidebar:

    st.title("📖 The Story")

    st.markdown("""
    👹 **Chucky has returned…**

    Once again, Chucky is back causing chaos —  
    scaring and hurting innocent children.

    🌙 The town is in fear. No one dares to face him.

    But not all hope is lost…

    🦸‍♀️ **Avika, the Super Girl**, has stepped forward.

    She knows the only way to stop Chucky is to  
    perform a powerful **exorcism ritual**.

    ⚡ But Chucky is hiding deep inside a **mystic maze** —  
    filled with confusing letters and false paths.

    🔤 To reach him, Avika must:
    - Find the **correct path**
    - Complete **hidden words**
    - Avoid traps and dead ends

    👻 Only then can she reach the exit gate…  
    and **banish Chucky forever**.

    ---
    """)

    st.title("🧠 How to Play")

    st.markdown("""
    **🎯 Objective**
    - Enter through the gate 🚪
    - Follow the hidden path
    - Reach Chucky 👻 and perform the exorcism

    **🧩 Words**
    - Each step builds a word
    - Complete words to progress
    - Hints show 2 letters

    **❤️ Lives**
    - You have 3 lives
    - Wrong tile = lose 1 life

    **🏁 Goal**
    - Reach the exit gate
    - Finish as fast as possible for leaderboard
    """)
    
st.title("🧙 Om Bhool Bhulaiya Swaahaa")
# ------------------------
# CHUCKY NEAR EXIT (FIXED POSITION)
# ------------------------
if st.session_state.get("chucky_active", False):

    # 🔊 play sound once
    if not st.session_state.get("chucky_sound_played", False):
        play_loop_sound_base64("chucky_laugh.mp3")
        st.session_state.chucky_sound_played = True

    exit_row = st.session_state.exit[0]

    # map row → vertical position
    y_percent = 10 + (exit_row / GRID_SIZE) * 70

    st.markdown(f"""
    <style>

    .chucky-exit {{
        position: fixed;
        top: {y_percent}vh;
        left: 92vw;   /* right side near exit gate */
        transform: translate(-50%, -50%);
        z-index: 999;
        pointer-events: none;

        animation: pulseSize 2s infinite ease-in-out,
                   floatY 3s infinite ease-in-out;
    }}

    .chucky-exit img {{
        width: 100px;
    }}

    /* SMALL ↔ BIG */
    @keyframes pulseSize {{
        0% {{ transform: translate(-50%, -50%) scale(1); }}
        50% {{ transform: translate(-50%, -50%) scale(1.6); }}
        100% {{ transform: translate(-50%, -50%) scale(1); }}
    }}

    /* slight vertical float */
    @keyframes floatY {{
        0% {{ top: {y_percent}vh; }}
        50% {{ top: {y_percent + 3}vh; }}
        100% {{ top: {y_percent}vh; }}
    }}

    </style>

    <div class="chucky-exit">
        <img src="data:image/png;base64,{chucky_base64}">
    </div>
    """, unsafe_allow_html=True)
    
st.write(f"⏱️ Time: {elapsed}s | ❤️ Lives: {st.session_state.lives}")
current_idx = min(st.session_state.current_word_index, len(st.session_state.words) - 1)
words = st.session_state.words

current_idx = st.session_state.current_word_index
letters_done = st.session_state.letters_progress
words = st.session_state.words

display = []

words = st.session_state.words
current_idx = st.session_state.current_word_index
letters_done = st.session_state.letters_progress

for i, w in enumerate(words):

    # ✅ COMPLETED
    if i in st.session_state.completed_words:
        display.append(w)

    # ✅ CURRENT WORD (progressive)
    elif i == current_idx:
        revealed = ""
        for j, ch in enumerate(w):
            if j < letters_done:
                revealed += ch + " "
            else:
                revealed += "_ "
        display.append(f"👉 {revealed.strip()}")

    # ✅ FUTURE WORDS (2-letter hint system)
    else:
        hint = ["_"] * len(w)

        # always reveal first letter
        hint[0] = w[0]

        # reveal one more letter (middle or last)
        if len(w) > 2:
            reveal_index = len(w) // 2
        else:
            reveal_index = len(w) - 1

        hint[reveal_index] = w[reveal_index]

        display.append(" ".join(hint))

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
            # 🔥 show letter if this tile completes a word
            total = 0
            for w in st.session_state.words:
                total += len(w)
                if idx == total - 1:
                    label = f"🧙{base}"
                    break

        # correct path
        elif idx > 0 and (x,y) in path[:idx]:
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
                    # 🔥 FIX: detect completion using PATH INDEX (not letters_progress)
                    total = 0

                    for i, w in enumerate(st.session_state.words):
                        total += len(w)

                        if st.session_state.index == total - 1:
                            st.session_state.completed_words.add(i)
                            st.session_state.current_word_index = i + 1
                            st.session_state.letters_progress = 0
                            break
                
                    st.rerun()
                else:
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
