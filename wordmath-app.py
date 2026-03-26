import streamlit as st
import random
import json
from openai import OpenAI
import base64

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Fun Math Word Game", page_icon="🎮")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ------------------ SESSION STATE ------------------
if "level" not in st.session_state:
    st.session_state.level = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "question" not in st.session_state:
    st.session_state.question = None

# ------------------ SOUND UTILS ------------------
def play_sound(file):
    with open(file, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

# ------------------ ANIMATIONS ------------------
def show_balloons():
    st.balloons()

# ------------------ CHATGPT QUESTION ------------------
@st.cache_data(ttl=300)
def generate_question(level):
    prompt = f"""
    Create a FUN math + word puzzle for a Grade {level} kid.

    Keep it short, playful, and silly.

    Return JSON:
    {{
        "math_question": "...",
        "math_answer": number,
        "word_puzzle": "word with missing letters like _ A _",
        "word_answer": "...",
        "hint": "..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-5.3",
        messages=[{"role": "system", "content": "You are a funny game master for kids"},
                  {"role": "user", "content": prompt}],
        temperature=0.8
    )

    return json.loads(response.choices[0].message.content)

# ------------------ LOAD QUESTION ------------------
if st.session_state.question is None:
    st.session_state.question = generate_question(st.session_state.level)

q = st.session_state.question

# ------------------ UI ------------------
st.title("🎮 Silly Math & Word Adventure")

st.write(f"⭐ Level: {st.session_state.level} | Score: {st.session_state.score}")

st.subheader("🧮 Solve this:")
st.write(q["math_question"])

user_answer = st.number_input("Your Answer", step=1)

if st.button("Submit Answer"):
    if user_answer == q["math_answer"]:
        st.success("🎉 Correct! You unlocked the word!")

        play_sound("correct.mp3")
        show_balloons()

        st.session_state.score += 10

        st.subheader("🔤 Word Puzzle")
        st.write(q["word_puzzle"])

        word_guess = st.text_input("Guess the word")

        if st.button("Submit Word"):
            if word_guess.lower() == q["word_answer"].lower():
                st.success("🤣 You got it! Genius!")
                play_sound("win.mp3")
                st.session_state.level += 1
            else:
                st.error("😜 Oops! Try again!")
                play_sound("wrong.mp3")

    else:
        st.error("💥 Wrong! Here's a hint:")
        st.warning(q["hint"])
        play_sound("wrong.mp3")

# ------------------ NEXT QUESTION ------------------
if st.button("Next Question"):
    st.session_state.question = generate_question(st.session_state.level)
    st.rerun()
