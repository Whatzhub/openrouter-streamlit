# import openai
# from openai import OpenAI
import streamlit as st
from streamlit_chat import message
import requests
import sseclient
import json
from shared import constants
from tenacity import retry, wait_exponential

st.title("💬 Streamlit GPT")

# Initilize session states
if "disabled" not in st.session_state:
    st.session_state.disabled = False

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

def toggle_submitted():
    if st.session_state.disabled == False: st.session_state.disabled = True
    else: st.session_state.disabled = False
    
@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def chat_completion(message_placeholder, full_response):
    try:
        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {constants.OPENROUTER_API_KEY}",
            "HTTP-Referer": constants.OPENROUTER_REFERRER, # Optional, for including your app on openrouter.ai rankings.
            "Accept": "text/event-stream",
        },
        data=json.dumps({
            "model": "openai/gpt-3.5-turbo-1106", # Optional
            "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            "stream": True,
        }),
        stream=True,
        timeout=6 # 6 seconds
    )
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data != '[DONE]':
                print(f"Event: {event.data}")
                print(json.loads(event.data)['choices'][0]['delta']['content'], end="", flush=True)
                full_response += (json.loads(event.data)['choices'][0]['delta']['content'] or "")
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        toggle_submitted()
        st.rerun()
        print(f"st.session_state.disabled: {st.session_state.disabled}")
        print(f"this ran!")
    except requests.exceptions.Timeout:
        print('The request timed out')
        print("Wait 2^x * 1 second between each retry starting with 4 seconds, then up to 10 seconds, then 10 seconds afterwards")
        raise Exception
    except requests.exceptions.RequestException as e:
        print('An error occurred:', e)
        print("Wait 2^x * 1 second between each retry starting with 4 seconds, then up to 10 seconds, then 10 seconds afterwards")
        raise Exception
    
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
# Accept user input
prompt = st.chat_input("What is up?", disabled=st.session_state.disabled, on_submit=toggle_submitted)
if prompt:
    # Add user message to chat history
    print(f"st.session_state.disabled: {st.session_state.disabled}")
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        chat_completion(message_placeholder, full_response)