"""
Down Memory Lane - Slack Bot
Receives mentions from Slack, generates childhood photos using Replicate, and posts them back.
"""

import os
import re
import requests
from dotenv import load_dotenv
import replicate
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_MODEL = os.getenv("REPLICATE_MODEL", "lucataco/flux-dev-lora:a22c463f11808638ad5e2ebd582e07a469031f48dd567366fb4c6fdab91d614d")
LORA_WEIGHTS_URL = os.getenv("LORA_WEIGHTS_URL")  # Your trained LoRA weights URL
TRIGGER_WORD = os.getenv("TRIGGER_WORD", "VISHYFACE")

# Set Replicate API token
if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Track processed events to avoid duplicates
processed_events = set()

# Debug: Print configuration on startup
print("=" * 50)
print("SLACK BOT CONFIGURATION")
print("=" * 50)
print(f"SLACK_BOT_TOKEN loaded: {bool(SLACK_BOT_TOKEN)}")
print(f"REPLICATE_API_TOKEN loaded: {bool(REPLICATE_API_TOKEN)}")
print(f"REPLICATE_MODEL: {REPLICATE_MODEL}")
print(f"LORA_WEIGHTS_URL: {LORA_WEIGHTS_URL}")
print(f"TRIGGER_WORD: {TRIGGER_WORD}")
print("=" * 50)


def enhance_prompt(user_prompt: str) -> str:
    """
    Enhance the user's prompt for childhood photo generation.
    Adds trigger word and styling for realistic vintage photos.
    """
    # Extract age if mentioned
    age_match = re.search(r'(\d+)[-\s]?year[-\s]?old', user_prompt.lower())
    age = age_match.group(1) if age_match else "5"
    
    # Build enhanced prompt with trigger word
    enhanced = f"A vintage photograph of {TRIGGER_WORD} as a {age}-year-old child, {user_prompt}, realistic childhood photo, natural lighting, candid moment, high quality"
    
    return enhanced


def generate_image(prompt: str) -> str:
    """
    Generate an image using Replicate.
    Returns the URL of the generated image.
    """
    enhanced_prompt = enhance_prompt(prompt)
    print(f"Generating with prompt: {enhanced_prompt}")
    
    # Build input parameters
    input_params = {
        "prompt": enhanced_prompt,
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "guidance_scale": 3.5,
        "num_inference_steps": 28
    }
    
    # Add LoRA weights if configured
    if LORA_WEIGHTS_URL:
        input_params["hf_lora"] = LORA_WEIGHTS_URL
    
    # Run the model
    output = replicate.run(REPLICATE_MODEL, input=input_params)
    
    # Extract URL from output
    if isinstance(output, list) and len(output) > 0:
        first_output = output[0]
        if hasattr(first_output, 'url'):
            return first_output.url
        elif isinstance(first_output, str):
            return first_output
        else:
            return str(first_output)
    elif hasattr(output, 'url'):
        return output.url
    elif isinstance(output, str):
        return output
    
    raise Exception(f"Unexpected output format: {output}")


def download_image(url: str) -> bytes:
    """Download image from URL and return bytes."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def send_slack_message(channel: str, thread_ts: str, text: str):
    """Send a text message to Slack."""
    try:
        slack_client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=text
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


def upload_image_to_slack(channel: str, thread_ts: str, image_bytes: bytes, prompt: str):
    """Upload the generated image to Slack in the same thread."""
    try:
        response = slack_client.files_upload_v2(
            channel=channel,
            thread_ts=thread_ts,
            file=image_bytes,
            filename="childhood_memory.webp",
            title="Your Childhood Memory",
            initial_comment=f"✨ Here's your childhood memory: _{prompt}_"
        )
        print(f"Image uploaded successfully!")
        return response
    except SlackApiError as e:
        print(f"Error uploading to Slack: {e.response['error']}")
        raise


def process_image_request(channel: str, thread_ts: str, user_prompt: str):
    """
    Background task to process image generation.
    Runs in a separate thread to avoid Slack's 3-second timeout.
    """
    try:
        # Send acknowledgment
        send_slack_message(
            channel,
            thread_ts,
            "🎨 Creating your childhood memory... This may take 30-60 seconds."
        )
        
        # Generate image
        print(f"Processing request: {user_prompt}")
        image_url = generate_image(user_prompt)
        print(f"Image generated: {image_url}")
        
        # Download image
        image_bytes = download_image(image_url)
        print(f"Image downloaded: {len(image_bytes)} bytes")
        
        # Upload to Slack
        upload_image_to_slack(channel, thread_ts, image_bytes, user_prompt)
        print("Image posted to Slack!")
        
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        send_slack_message(
            channel,
            thread_ts,
            f"❌ Sorry, I couldn't generate that image. Error: {str(e)}"
        )


def extract_prompt_from_message(text: str, bot_user_id: str) -> str:
    """Extract the actual prompt from the message, removing the bot mention."""
    # Remove bot mention
    text = re.sub(f'<@{bot_user_id}>', '', text)
    # Clean up extra whitespace
    text = ' '.join(text.split())
    return text.strip()


@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle incoming Slack events."""
    data = request.json
    
    # Handle Slack URL verification challenge
    if data.get("type") == "url_verification":
        print("URL verification challenge received")
        return jsonify({"challenge": data.get("challenge")})
    
    # Handle event callbacks
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        event_id = data.get("event_id")
        
        # Deduplicate events (Slack may retry)
        if event_id in processed_events:
            print(f"Duplicate event ignored: {event_id}")
            return jsonify({"status": "ok"})
        
        processed_events.add(event_id)
        
        # Cleanup old events (keep memory bounded)
        if len(processed_events) > 1000:
            processed_events.clear()
        
        # Handle app_mention events
        if event.get("type") == "app_mention":
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            text = event.get("text", "")
            user = event.get("user")
            
            print(f"Received mention from {user}: {text}")
            
            # Get bot's user ID
            try:
                auth_response = slack_client.auth_test()
                bot_user_id = auth_response["user_id"]
            except:
                bot_user_id = ""
            
            # Extract prompt
            user_prompt = extract_prompt_from_message(text, bot_user_id)
            print(f"Extracted prompt: {user_prompt}")
            
            if not user_prompt:
                send_slack_message(
                    channel,
                    thread_ts,
                    "👋 Hi! Please describe the childhood photo you'd like to generate.\n\n"
                    "Examples:\n"
                    "• `@MemoryBot my 2-year-old self in a backyard`\n"
                    "• `@MemoryBot my 5-year-old self on a beach`\n"
                    "• `@MemoryBot my 10-year-old self in a classroom`"
                )
                return jsonify({"status": "ok"})
            
            # Process in background thread (to avoid 3-second timeout)
            thread = threading.Thread(
                target=process_image_request,
                args=(channel, thread_ts, user_prompt)
            )
            thread.start()
        
        return jsonify({"status": "ok"})
    
    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "memory-lane-slack-bot",
        "slack_configured": bool(SLACK_BOT_TOKEN),
        "replicate_configured": bool(REPLICATE_API_TOKEN),
        "trigger_word": TRIGGER_WORD
    })


if __name__ == "__main__":
    print("\n🚀 Starting Memory Lane Slack Bot...")
    print("Server running on http://0.0.0.0:3000")
    print("Webhook endpoint: /slack/events")
    print("\nMake sure to set your Slack Event Subscription URL to:")
    print("  https://your-ngrok-url.ngrok.io/slack/events\n")
    app.run(host="0.0.0.0", port=3000, debug=True)