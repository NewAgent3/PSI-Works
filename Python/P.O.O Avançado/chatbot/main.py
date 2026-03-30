import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "meta-llama/Llama-3.2-1B"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    device_map="auto"
)

print("Local Llama Chatbot Ready!")
print("Type 'exit' to quit.\n")

chat_history = ""

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    chat_history += f"User: {user_input}\nAssistant: "

    inputs = tokenizer(chat_history, return_tensors="pt").to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

    response = tokenizer.decode(output[0], skip_special_tokens=True)

    # Extract only assistant response
    response = response.split("Assistant:")[-1].strip()

    print("Bot:", response)
    chat_history += response + "\n"
