import streamlit as st
import random
import openai

# -----------------------
# CONFIG
# -----------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

CHAPTERS = [
    "Place Value",
    "Adding in your head",
    "Exploring addition",
    "Subtracting in your head",
    "Exploring subtraction",
    "Multiplying",
    "Dividing",
    "Fractions of objects"
]

MAZE_LENGTH = 5  # rooms before boss

# -----------------------
# STATE
# -----------------------
if "chapter" not in st.session_state:
    st.session_state.chapter = None

if "step" not in st.session_state:
    st.session_state.step = 0

if "question" not in st.session_state:
    st.session_state.question = None

if "answer" not in st.session_state:
    st.session_state.answer = None

if "lives" not in st.session_state:
    st.session_state.lives = 3

if "score" not in st.session_state:
    st.session_state.score = 0


# -----------------------
# AI QUESTION GENERATOR
# -----------------------
def generate_question(chapter):
    prompt = f"""
    Generate a simple math question for a child based on this topic: {chapter}.
    Also provide the correct answer.

    Format:
    Question: ...
    Answer: ...
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content

    try:
        q = text.split("Question:")[1].split("Answer:")[0].strip()
        a = text.split("Answer:")[1].strip()
    except:
        q = "2 + 2"
        a = "4"

    return q, a


# -----------------------
# UI
# -----------------------
st.title("🧩 Math Maze: Exorcism Quest")

# -----------------------
# CHAPTER SELECT
# -----------------------
if not st.session_state.chapter:
    st.subheader("Choose your Chapter")

    chapter = st.selectbox("Select Topic", CHAPTERS)

    if st.button("Enter Maze"):
        st.session_state.chapter = chapter
        st.session_state.step = 0
        st.session_state.lives = 3
        st.session_state.score = 0

        q, a = generate_question(chapter)
        st.session_state.question = q
        st.session_state.answer = a

    st.stop()

# -----------------------
# HUD
# -----------------------
col1, col2, col3 = st.columns(3)
col1.metric("❤️ Lives", st.session_state.lives)
col2.metric("⭐ Score", st.session_state.score)
col3.metric("🧭 Room", f"{st.session_state.step}/{MAZE_LENGTH}")

st.divider()

# -----------------------
# GAME OVER
# -----------------------
if st.session_state.lives <= 0:
    st.error("💀 The spirit consumed you... Game Over!")

    if st.button("Restart"):
        st.session_state.clear()

    st.stop()

# -----------------------
# BOSS ROOM
# -----------------------
if st.session_state.step >= MAZE_LENGTH:
    st.success("🔥 You reached the center!")

    st.markdown("## 🕯️ Final Ritual Question")

    q, a = generate_question(st.session_state.chapter)

    st.write(q)
    user = st.text_input("Your Answer")

    if st.button("Perform Exorcism"):
        if user.strip() == a.strip():
            st.success("✨ EXORCISM COMPLETE! You win!")
        else:
            st.error("❌ The ritual failed... try again!")

    st.stop()

# -----------------------
# NORMAL ROOM
# -----------------------
st.markdown(f"## 🚪 Room {st.session_state.step + 1}")

st.write(st.session_state.question)

user_answer = st.text_input("Your Answer")

if st.button("Submit"):
    correct = st.session_state.answer

    if user_answer.strip() == correct.strip():
        st.success("✅ Door unlocked!")
        st.session_state.score += 10
        st.session_state.step += 1

        q, a = generate_question(st.session_state.chapter)
        st.session_state.question = q
        st.session_state.answer = a

    else:
        st.error("❌ Wrong! The spirit attacks!")
        st.session_state.lives -= 1

        # hint using AI
        hint_prompt = f"""
        Question: {st.session_state.question}
        Correct Answer: {correct}

        Give a small hint for a child.
        """

        hint = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": hint_prompt}]
        )

        st.info(hint.choices[0].message.content)
