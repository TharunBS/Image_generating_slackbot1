import os
from dotenv import load_dotenv
import replicate

# Load environment variables from .env
load_dotenv()

# Optional debug (remove later)
print("API TOKEN LOADED:", bool(os.getenv("REPLICATE_API_TOKEN")))

output = replicate.run(
    "tharunbs123/flux-lora-vishy:267576579ad27ce78b7f6a236b9cd3f9fd0bcb96932dcc4d6ea9963b668566f1",
    input={
        "prompt": "A realistic childhood photo of VISHYFACE as a 20-year-old sitting in a classroom"
    }
)

print(output[0].url)
