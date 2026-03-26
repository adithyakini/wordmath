import streamlit as st
import json, re, random, base64
from openai import OpenAI

# ---------------- CONFIG ----------------
st.set_page_config(page_title="💨 Fartman Math Riddle", page_icon="💨")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------- STATE ----------------
def init():
    defaults = {
        "level": 1,
        "score": 0,
        "streak": 0,
        "lives": 3,
        "stage": "math",
        "question": None,
        "math_input": 0,
        "word_input": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ---------------- SOUND ----------------
def sound(file):
    try:
        with open(file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """, unsafe_allow_html=True)
    except:
        pass

# ---------------- FARTMAN VISUAL ----------------
def fartman(lives):
    img_map = {
        3: "assets/fartman_happy.png",
        2: "assets/fartman_ok.png",
        1: "assets/fartman_worried.png",
        0: "assets/fartman_dead.png"
    }
    st.image(img_map[lives], width=220)

# ---------------- FUN TEXT ----------------
def funny_correct():
    msgs = [
        "💨 BOOM! Brain fart worked!",
        "🔥 You’re on FIREman!",
        "🎯 Too easy for you!",
        "🤣 Fartman is proud!"
    ]
    return random.choice(msgs)

def funny_wrong():
    msgs = [
        "💀 Oops… that stinks!",
        "😬 That was a weak fart...",
        "🤢 Try again human!",
        "💨 Misfire!"
    ]
    return random.choice(msgs)

# ---------------- AI ----------------
@st.cache_data(ttl=300)
def gen_q(level):
    prompt = f"""
    Generate a FUN Grade {level} math + riddle.

    Return ONLY JSON:
    {{
        "math_question": "...",
        "math_answer": number,
        "riddle": "...",
        "word_answer": "...",
        "hint": "..."
    }}
    """

    try:
        res = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        raw = re.sub(r"```.*?```", "", res.choices[0].message.content.strip(), flags=re.S)
        data = json.loads(raw)

        data["math_answer"] = int(data["math_answer"])
        data["word_answer"] = data["word_answer"].strip().upper()

        return data
    except:
        return {
            "math_question": "What is 6 + 2?",
            "math_answer": 8,
            "riddle": "I bark and guard your house. What am I?",
            "word_answer": "DOG",
            "hint": "A loyal animal"
        }

# ---------------- LOAD ----------------
def new_q():
    st.session_state.question = gen_q(st.session_state.level + random.random())
    st.session_state.stage = "math"
    st.session_state.lives = 3
    st.session_state.math_input = 0
    st.session_state.word_input = ""

if st.session_state.question is None:
    new_q()

q = st.session_state.question

# ---------------- HEADER ----------------
st.title("💨 Fartman Math Riddle Madness")

col1, col2 = st.columns(2)
col1.metric("⭐ Level", st.session_state.level)
col2.metric("🔥 Streak", st.session_state.streak)

st.progress(min(st.session_state.streak / 5, 1.0))

fartman(st.session_state.lives)

# ---------------- MATH ----------------
if st.session_state.stage == "math":
    st.subheader("🧮 Solve or Fartman suffers!")

    st.write(q["math_question"])
    ans = st.number_input("Answer", key="math_input")

    if st.button("💥 Submit Math"):
        if int(ans) == q["math_answer"]:
            st.success(funny_correct())
            sound("correct.mp3")

            st.session_state.score += 10
            st.session_state.streak += 1
            st.session_state.stage = "word"
            st.rerun()
        else:
            st.error(funny_wrong())
            sound("wrong.mp3")

            st.session_state.streak = 0
            st.warning(q["hint"])

# ---------------- RIDDLE ----------------
elif st.session_state.stage == "word":
    st.subheader("🧩 Solve the Riddle or Fartman Dies!")

    st.write(q["riddle"])

    guess = st.text_input("Your Guess", key="word_input")

    if st.button("💨 Submit Guess"):
        if guess.strip().upper() == q["word_answer"]:
            st.success("🎉 YOU SAVED FARTMAN!")
            sound("win.mp3")
            st.balloons()

            st.session_state.level += 1
            st.session_state.stage = "done"
            st.rerun()

        else:
            st.session_state.lives -= 1
            sound("wrong.mp3")
            st.session_state.streak = 0

            if st.session_state.lives > 0:
                st.error(f"{funny_wrong()} | Lives left: {st.session_state.lives}")
                st.warning(q["hint"])
                st.rerun()
            else:
                st.error("💀 FARTMAN HAS FALLEN!")
                st.write(f"Answer: **{q['word_answer']}**")
                st.session_state.stage = "done"
                st.rerun()

# ---------------- DONE ----------------
elif st.session_state.stage == "done":
    st.success("🎯 Another mission?")

    if st.button("🚀 Next Level"):
        new_q()
        st.rerun()
