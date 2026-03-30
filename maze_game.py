import streamlit as st
import random
import string
import time
from openai import OpenAI
import json
import os
import base64

# ------------------------
# IMAGE
# ------------------------
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

chucky_base64 = get_base64_image("chucky.png")

# ------------------------
# LEADERBOARD
# ------------------------
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
# SOUND
# ------------------------
def play_sound(url):
    st.markdown(f"""
    <audio autoplay>
    <source src="{url}" type="audio/mpeg">
    </audio>
    """, unsafe_allow_html=True)

THUNDER = "https://www.soundjay.com/nature/thunder-1.mp3"
WRONG = "https://www.soundjay.com/button/beep-10.wav"
HEARTBEAT = "https://www.soundjay.com/human/heartbeat-01a.mp3"

# occasional thunder
if random.random() < 0.05:
    play_sound(THUNDER)

# ------------------------
# STYLE
# ------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #0b0f1a, #111827);
    color: #e5e7eb;
}
button[kind="secondary"] {
    background-color: #1f2937 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------
# CONFIG
# ------------------------
GRID_SIZE = 10
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
level = st.selectbox("Difficulty", ["easy","medium","hard"])
with st.sidebar:
    st.title("🧠 How to Play")

    st.markdown("""
    **🧙 Objective**
    - Enter through the gate 🚪
    - Follow the hidden word path
    - Reach the ghost 👻 and perform the exorcism

    **🎯 Movement**
    - Move one tile at a time
    - Only one correct path exists
    - Build words as you move

    **🧩 Words**
    - Current word reveals gradually
    - Future words show hints (first & last letter)
    - Completing a word unlocks the next

    **❤️ Lives**
    - You have 3 lives
    - Wrong tile = lose 1 life

    **🏁 Goal**
    - Reach the exit gate 👻🚪
    - Faster time = better leaderboard rank
    """)

# ------------------------
# WORDS
# ------------------------
def get_words(level):
    rule = "exactly 3 letters" if level=="easy" else "4 to 5 letters" if level=="medium" else "6+ letters"
    theme = random.choice(["nature","space","food","fantasy"])

    prompt = f"""
    Generate words:
    - {rule}
    - theme: {theme}
    - avoid CAT DOG SUN
    - return comma-separated
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}]
    )

    return [w.strip().upper() for w in res.choices[0].message.content.split(",")]

def generate_full_path():
    path, visited = [], set()
    x,y = 0,0
    path.append((x,y)); visited.add((x,y))

    while y < GRID_SIZE-1:
        moves = [(1,0),(-1,0),(0,1)]
        random.shuffle(moves)

        for dx,dy in moves:
            nx,ny = x+dx,y+dy
            if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE and (nx,ny) not in visited:
                x,y = nx,ny
                path.append((x,y)); visited.add((x,y))
                break
        else:
            y+=1
            path.append((x,y)); visited.add((x,y))

    return path

def generate_words_for_path(length, level):
    words=[]
    while sum(len(w) for w in words) < length:
        words += get_words(level)
    return words

def embed_words(path, words):
    grid=[[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    i=0
    for w in words:
        for ch in w:
            if i>=len(path): return grid
            x,y = path[i]
            grid[x][y]=ch
            i+=1
    return grid

# ------------------------
# INIT
# ------------------------
if "init" not in st.session_state or st.session_state.get("level")!=level:

    path = generate_full_path()
    words = generate_words_for_path(len(path), level)
    grid = embed_words(path, words)

    st.session_state.update({
    "grid": grid,
    "path": path,
    "words": words,
    "entry": path[0],
    "exit": path[-1],

    # ✅ CRITICAL RESET
    "index": -1,
    "lives": 3,
    "wrong_tiles": set(),

    "start_time": time.time(),
    "finished": False,

    "current_word_index": 0,
    "letters_progress": 0,
    "completed_words": set(),

    "show_intro": True,
    "intro_played": False,

    "level": level
})

# leaderboard
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = load_leaderboard()

# ------------------------
# CINEMATIC CHUCKY INTRO (NON-BLOCKING FIX)
# ------------------------
# ------------------------
# CHUCKY INTRO (NO RERUN / NO STOP)
# ------------------------
if st.session_state.get("show_intro", False):

    exit_row = st.session_state.exit[0]
    x_percent = 85
    y_percent = 10 + (exit_row / GRID_SIZE) * 70

    # play thunder once
    if "intro_played" not in st.session_state:
        play_sound(THUNDER)
        st.session_state.intro_played = True

    st.markdown(f"""
    <style>

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
    }}

    @keyframes cinematicMove {{
        0% {{ transform: translate(-50%, -50%) scale(0.2); opacity:0; }}
        10% {{ transform: translate(-50%, -50%) scale(2.5); opacity:1; }}
        40% {{ transform: translate(-50%, -50%) scale(1.2); }}
        75% {{ transform: translate({x_percent}vw, {y_percent}vh) scale(0.4); }}
        100% {{ transform: translate({x_percent}vw, {y_percent}vh) scale(0.05); opacity:0; }}
    }}

    </style>

    <div class="chucky-container">
        <img src="data:image/png;base64,{chucky_base64}">
    </div>
    """, unsafe_allow_html=True)

    # ✅ disable intro AFTER first render
    st.session_state.show_intro = False

# ------------------------
# UI
# ------------------------
st.title("🧙 Om Bhool Bhulaiya Swaahaa")
elapsed=int(time.time()-st.session_state.start_time)
st.write(f"⏱ {elapsed}s ❤️ {st.session_state.lives}")

# words display
display=[]
for i,w in enumerate(st.session_state.words):
    if i in st.session_state.completed_words:
        display.append(w)
    elif i==st.session_state.current_word_index:
        reveal = "".join([c+" " if j<st.session_state.letters_progress else "_ " for j,c in enumerate(w)])
        display.append("👉 "+reveal.strip())
    else:
        hint=" ".join([c if j in (0,len(w)-1) else "_" for j,c in enumerate(w)])
        display.append(hint)

st.write(" → ".join(display))

# ------------------------
# GRID
# ------------------------
grid,path,idx = st.session_state.grid, st.session_state.path, st.session_state.index

for i in range(GRID_SIZE):
    cols=st.columns(GRID_SIZE+2)
    for j in range(GRID_SIZE+2):

        if j==0:
            cols[j].button("🚪🧙" if i==st.session_state.entry[0] and idx==-1 else "", key=f"{i}-e")
            continue

        if j==GRID_SIZE+1:
            cols[j].button("👻🚪" if i==st.session_state.exit[0] else "", key=f"{i}-x")
            continue

        x,y=i,j-1
        base=grid[x][y]

        # wizard
        if idx>=0 and (x,y)==path[idx]:

            # show final letter if word completes
            total=0
            label="🧙"
            for w in st.session_state.words:
                total+=len(w)
                if idx==total-1:
                    label=f"🧙{base}"
                    break

        elif idx > 0 and (x,y) in path[:idx]:
            label = f"🟩{base}"
        elif (x,y) in st.session_state.wrong_tiles:
            label=f"🟥{base}"
        else:
            label=base

        if cols[j].button(label, key=f"{x}-{y}"):

            if idx==-1 and (x,y)==st.session_state.entry:
                st.session_state.index=0
                st.rerun()

            elif idx>=0 and (x,y)==path[idx+1]:

                st.session_state.index+=1
                st.session_state.letters_progress+=1

                w = st.session_state.words[st.session_state.current_word_index]

                if st.session_state.letters_progress>=len(w):
                    st.session_state.completed_words.add(st.session_state.current_word_index)
                    st.session_state.current_word_index+=1
                    st.session_state.letters_progress=0

                st.rerun()

            else:
                st.session_state.lives-=1
                play_sound(WRONG)
                st.session_state.wrong_tiles.add((x,y))

# ------------------------
# LEADERBOARD
# ------------------------
st.subheader("🏆 Leaderboard")
for i,e in enumerate(st.session_state.leaderboard):
    st.write(f"{i+1}. {e['name']} - {e['time']}s")

# ------------------------
# RESET
# ------------------------
if st.button("🔄 New Game"):

    leaderboard = st.session_state.leaderboard

    # ✅ FULL RESET (except leaderboard)
    st.session_state.clear()

    st.session_state.leaderboard = leaderboard

    st.rerun()
