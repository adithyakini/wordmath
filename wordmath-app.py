import streamlit as st
import json
from openai import OpenAI
import base64

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Fun Math Game", page_icon="🎮")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------- SESSION STATE ----------------
def init_state():
    defaults = {
        "level": 1,
        "score": 0,
        "question": None,
        "stage": "math",  # math → word → done
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------- SOUND ----------------
def play_sound(file):
    try:
        with open(file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """, unsafe_allow_html=True)
    except:
        pass  # don't crash if file missing

# ---------------- AI QUESTION ----------------
@st.cache_data(ttl=300)
def generate_question(level):
    prompt = f"""
    Create a FUN math + word puzzle for Grade {level}.

    Return JSON:
    {{
        "math_question": "...",
        "math_answer": number,
        "word_puzzle": "_ A _",
        "word_answer": "...",
        "hint": "..."
    }}
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return json.loads(res.choices[0].message.content)

# ---------------- LOAD QUESTION ----------------
def load_question():
    st.session_state.question = generate_question(st.session_state.level)
    st.session_state.stage = "math"

if st.session_state.question is None:
    load_question()

q = st.session_state.question

# ---------------- UI ----------------
st.title("🎮 Silly Math Adventure")
st.write(f"⭐ Level: {st.session_state.level} | Score: {st.session_state.score}")

# ---------------- STAGE: MATH ----------------
if st.session_state.stage == "math":
    st.subheader("🧮 Solve this:")
    st.write(q["math_question"])

    answer = st.number_input("Your Answer", key="math_input")

    if st.button("Submit Math"):
        if answer == q["math_answer"]:
            st.success("🎉 Correct!")
            play_sound("correct.mp3")
            st.session_state.score += 10
            st.session_state.stage = "word"
            st.rerun()
        else:
            st.error("💥 Wrong!")
            st.warning(q["hint"])
            play_sound("wrong.mp3")

# ---------------- STAGE: WORD ----------------
elif st.session_state.stage == "word":
    st.subheader("🔤 Word Puzzle")
    st.write(q["word_puzzle"])

    guess = st.text_input("Your Guess", key="word_input")

    if st.button("Submit Word"):
        if guess.lower() == q["word_answer"].lower():
            st.success("🤣 Genius!")
            play_sound("win.mp3")
            st.session_state.level += 1
            st.session_state.stage = "done"
            st.rerun()
        else:
            st.error("😜 Try again!")
            play_sound("wrong.mp3")

# ---------------- STAGE: DONE ----------------
elif st.session_state.stage == "done":
    st.success("🎯 Ready for next challenge?")

    if st.button("Next Question"):
        load_question()
        st.rerun()
