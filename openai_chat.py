import os
from groq import Groq
from rich import print
import tiktoken


# def num_tokens_from_messages(messages, model='llama3-70b-8192'):
#     try:
#         encoding = tiktoken.encoding_for_model(model)
#         num_tokens = 0
#         for message in messages:
#             num_tokens += 4
#             for key, value in message.items():
#                 num_tokens += len(encoding.encode(value))
#                 if key == "name":
#                     num_tokens += -1
#         num_tokens += 2
#         return num_tokens
#     except Exception:
#         raise NotImplementedError(f"num_tokens_from_messages() is not presently implemented for model {model}.")


class GroqAiManager:

    def __init__(self):
        self.chat_history = []
        try:
            self.client = Groq(api_key=os.environ['GROQ_API_KEY'])
        except TypeError:
            exit("Ooops! You forgot to set GROQ_API_KEY in your environment!")

    def chat(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        chat_question = [{"role": "user", "content": prompt}]
        # if num_tokens_from_messages(chat_question) > 8000:
        #     print("The length of this chat question is too large for the Groq model")
        #     return

        print("[yellow]\nAsking Groq LLM a question...")
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": str(chat_question)}]
        )

        response = completion.choices[0].message.content
        print(f"[green]\n{response}\n")
        return response

    def chat_with_history(self, prompt=""):
        if not prompt:
            print("Didn't receive input!")
            return

        self.chat_history.append({"role": "user", "content": prompt})

        #print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}")
        # while num_tokens_from_messages(self.chat_history) > 8000:
        #     self.chat_history.pop(1)
        #     print(f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}")

        print("[yellow]\nAsking Groq LLM a question...")
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": str(self.chat_history)}]
        )

        self.chat_history.append({
            "role": completion.choices[0].message.role,
            "content": completion.choices[0].message.content
        })

        response = completion.choices[0].message.content
        print(f"[green]\n{response}\n")
        return response


if __name__ == '__main__':
    groq_manager = GroqAiManager()

    # CHAT TEST
    chat_without_history = groq_manager.chat("Hey Groq, what is 2 + 2? But tell it to me as Yoda")

    # CHAT WITH HISTORY TEST
    FIRST_SYSTEM_MESSAGE = {"role": "system", "content": "Act like you are Captain Jack Sparrow from the Pirates of the Caribbean movie series!"}
    FIRST_USER_MESSAGE = {"role": "user", "content": "Ahoy there! Who are you, and what are you doing in these parts? Please give me a 1 sentence background on how you got here."}
    groq_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)
    groq_manager.chat_history.append(FIRST_USER_MESSAGE)

    while True:
        new_prompt = input("\nType out your next question Jack Sparrow, then hit enter: \n\n")
        groq_manager.chat_with_history(new_prompt)