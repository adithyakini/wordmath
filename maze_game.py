import streamlit as st
import random
import string
from openai import OpenAI

# ------------------------
# CONFIG
# ------------------------
GRID_SIZE = 6
client = OpenAI()

# ------------------------
# AI WORD GENERATION
# ------------------------
def get_ai_words(level="easy"):
    prompt = f"""
    Generate 8 English words for a word maze game.

    Rules:
    - difficulty: {level}
    - easy: 3-5 letters
    - medium: 4-6 letters
    - hard: 5-8 letters
    - words should share letters for possible overlaps
    - avoid rare or obscure words

    Return ONLY comma-separated words.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )

        words = response.choices[0].message.content.strip().upper().split(",")
        return [w.strip() for w in words if w.strip()]

    except:
        # fallback if API fails
        return ["CAT","DOG","SUN","MOON","STAR","FIRE","WIND","TREE"]

# ------------------------
# PREFIX BUILD
# ------------------------
def build_prefixes(words):
    prefixes = set()
    for w in words:
        for i in range(len(w)):
            prefixes.add(w[:i+1])
    return prefixes

# ------------------------
# GRID
# ------------------------
def generate_grid():
    return [[random.choice(string.ascii_uppercase) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def neighbors(x, y):
    moves = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return [(i,j) for i,j in moves if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE]

# ------------------------
# GHOST AI
# ------------------------
def move_ghost(ghost, player):
    gx, gy = ghost
    px, py = player

    if abs(px-gx) > abs(py-gy):
        gx += 1 if px > gx else -1 if px < gx else 0
    else:
        gy += 1 if py > gy else -1 if py < gy else 0

    return (gx, gy)

# ------------------------
# AI HINT
# ------------------------
def get_ai_hint(current_word, words):
    prompt = f"""
    Current partial word: {current_word}

    From this list:
    {words}

    Suggest ONE valid next word.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip().upper()
    except:
        return "NO HINT"

# ------------------------
# INIT GAME
# ------------------------
if "initialized" not in st.session_state:

    level = "easy"

    words = get_ai_words(level)
    prefixes = build_prefixes(words)

    st.session_state.grid = generate_grid()
    st.session_state.words = words
    st.session_state.prefixes = prefixes

    st.session_state.player = (0,0)
    st.session_state.ghost = (GRID_SIZE-1, GRID_SIZE-1)

    start_letter = st.session_state.grid[0][0]

    st.session_state.word = start_letter
    st.session_state.visited = {(0,0)}
    st.session_state.score = 0
    st.session_state.game_over = False

    st.session_state.initialized = True

# ------------------------
# UI HEADER
# ------------------------
st.title("🧙 AI Word Maze")

level = st.selectbox("Difficulty", ["easy", "medium", "hard"])

if st.button("🎮 New Game"):
    st.session_state.clear()
    st.rerun()

st.write(f"### Current Word: `{st.session_state.word}`")
st.write(f"Score: {st.session_state.score}")
st.write(f"Words: {', '.join(st.session_state.words)}")

# ------------------------
# GAME STATE
# ------------------------
grid = st.session_state.grid
player = st.session_state.player
ghost = st.session_state.ghost
word = st.session_state.word
visited = st.session_state.visited
prefixes = st.session_state.prefixes
words = st.session_state.words

# ------------------------
# VALID MOVES
# ------------------------
valid_moves = []
for nx, ny in neighbors(*player):
    if (nx, ny) not in visited:
        new_word = word + grid[nx][ny]
        if new_word in prefixes:
            valid_moves.append((nx, ny))

# ------------------------
# GRID UI
# ------------------------
for i in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for j in range(GRID_SIZE):

        label = grid[i][j]

        if (i,j) == player:
            label = "🧙"
        elif (i,j) == ghost:
            label = "👻"
        elif (i,j) in valid_moves:
            label = f"🟩{grid[i][j]}"

        if cols[j].button(label, key=f"{i}-{j}"):

            if st.session_state.game_over:
                continue

            if (i,j) in valid_moves:

                letter = grid[i][j]
                new_word = word + letter

                st.session_state.player = (i,j)
                st.session_state.word = new_word
                st.session_state.visited.add((i,j))

                # WORD COMPLETED
                if new_word in words:
                    st.success(f"✅ {new_word}")
                    st.session_state.score += len(new_word)

                    st.session_state.word = ""
                    st.session_state.visited = {st.session_state.player}

                # ghost moves
                st.session_state.ghost = move_ghost(ghost, st.session_state.player)

            else:
                st.warning("❌ Invalid move")

# ------------------------
# HINT
# ------------------------
if st.button("💡 Smart Hint"):
    hint = get_ai_hint(word, words)
    st.info(f"Try: {hint}")

# ------------------------
# GAME OVER
# ------------------------
if st.session_state.player == st.session_state.ghost:
    st.error("💀 Ghost caught you!")
    st.session_state.game_over = True

if len(valid_moves) == 0:
    st.error("🚫 No valid moves!")
    st.session_state.game_over = True
