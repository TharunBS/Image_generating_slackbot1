import os
from dotenv import load_dotenv
import replicate
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

MODEL_ID = os.getenv("REPLICATE_MODEL")
API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

print("MODEL_ID:", MODEL_ID)
print("API_TOKEN LOADED:", bool(API_TOKEN))


class PromptRequest(BaseModel):
    prompt: str


@app.post("/generate")
def generate_image(data: PromptRequest):
    try:
        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": data.prompt
            }
        )
        return {"image_url": output[0].url}
    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
