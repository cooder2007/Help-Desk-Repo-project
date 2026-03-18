import streamlit as st
from ollama import chat
st.title("Help Desk ChatBot")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Help Desk ChatBot"}]
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if prompt := st.chat_input("Type your message:"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    response = chat(model="gemma3:4b", messages=st.session_state["messages"])
    bot_reply = response.get("message", {}).get("content", "Sorry, I didn’t understand that.")
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})