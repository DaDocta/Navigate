from openai import OpenAI

def init_openai_client(api_key):
    return OpenAI(api_key=api_key)

def process_results_openai(openai_client, keyword, user_prompt, text):
    try:
        # Modify the user prompt to clarify the context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Respond as if the user is asking for their own preferences or "
                    "context based on the provided information."
                ),
            },
            {
                "role": "user",
                "content": f"{user_prompt}\n\nHere is some information about '{keyword}' that might help:\n{text}",
            },
        ]
        chat_completion = openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error processing with OpenAI: {e}"

