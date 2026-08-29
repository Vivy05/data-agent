from pathlib import Path



def load_prompt(name:str):
    prompt = Path(__file__).parents[2]/"prompts"/f"{name}.prompt"

    return prompt.read_text(encoding="utf-8")
