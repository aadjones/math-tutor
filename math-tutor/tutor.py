import openai
import streamlit as st
import os

# Set up a slider for controlling the model temperature
temperature = st.slider("Set GPT model temperature (0 is more logical; 1 is more creative):", min_value=0.0, max_value=1.0, value=0.7, step=0.05)

# Set up some input files for loading the system context
def load_context(file_path):
    if file_path:
        with open(file_path, 'r') as f:
            return f.read()
    return None

txt_files = [f for f in os.listdir('./modes') if f.endswith('.txt')]

if not txt_files:
    st.warning("No .txt files found in the 'modes' directory.")
else:
    selected_file = st.selectbox("Choose a lesson:", txt_files)
    CONTEXT = load_context(f'./modes/{selected_file}')

# Set up the session states 
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = temperature
    else:
        st.session_state["temperature"] = temperature

    if "messages" not in st.session_state or "system" not in [m['role'] for m in st.session_state.messages]:
        st.session_state.messages = [
            {"role": "system", "content": CONTEXT},
            {"role": "assistant", "content": "Welcome to your math tutoring session! Would you like to hear your first problem?"}
        ]
    else:
        for message in st.session_state.messages:
            if message["role"] == "system":
                message["content"] = CONTEXT

def main():
    # New: Dropdown for selecting GPT model inside main
    model_options = ["GPT-3.5", "GPT-4"]
    selected_model = st.selectbox("Choose a GPT model:", model_options)
    model_mapping = {
        "GPT-3.5": "gpt-3.5-turbo",
        "GPT-4": "gpt-4"
    }
    st.session_state["openai_model"] = model_mapping[selected_model]
    for message in st.session_state.messages:
        if message["role"] != "system": # don't display the system messages; those are pre-instructions
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Send a message"):
        # Debug: Display the model being used right before making the API call
        # st.write(f"Debug: Making API call using {st.session_state['openai_model']}")
        # st.write(f"Debug: Using temperature {st.session_state['temperature']}")

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
                temperature=st.session_state["temperature"],
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response}) # update the session state messages to allow for continuity in the conversation

if __name__ == "__main__":
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    if txt_files:  # Only run main() if there are text files to choose from
        main()
