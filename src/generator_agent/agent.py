import os
import time
import base64
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

IMAGE_DIR = "generated_data/images"
VIDEO_DIR = "generated_data/videos"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# =====================================================
# CLIENT SYSTEM PROMPT REGISTRY
# =====================================================

CLIENT_PROMPTS = {
    "kalahari": """
You generate visuals for Kalahari Resort, a premium indoor waterpark and family entertainment resort environment.
Large indoor waterpark setting with vaulted ceilings, artificial lighting, colorful slides, wave pools, lazy rivers, and upscale family hospitality tone.
Avoid outdoor beaches, oceans, deserts, dark gritty visuals, or cartoon styles.
""",

    "tech_brand": """
You generate visuals for a premium futuristic technology brand.
Minimalist interiors, glass, steel, neon accents, dark mode lighting, holographic UI elements.
Avoid rustic themes, cartoons, or nature-heavy backgrounds.
""",

    "optima": """
You generate brand-aligned imagery for Optima Batteries.
Industrial, rugged, high-performance battery visuals.
Black, yellow, red, metallic steel tones.
Hyper-realistic lighting, product-centered composition.
Avoid cartoons, pastel tones, lifestyle clutter.
""",

    "plambo": """
You generate enterprise-grade corporate visuals for Plambo Solutions.
Clean structured layouts, deep blues, slate greys, minimal modern environments.
Avoid playful, cartoonish, or chaotic startup aesthetics.
""",

    "sovereignsilver": """
You generate premium wellness imagery for Sovereign Silver.
Clean minimal compositions, neutral palettes, refined science aesthetic.
Avoid fantasy elements, clutter, cartoon styles, or exaggerated claims.
"""
}

VALID_MEDIA_TYPES = {"image", "video"}


# =====================================================
# MEDIA AGENT
# =====================================================

class MediaAgent:

    def generate(self, payload: dict):
        prompt = payload.get("prompt")
        client_id = payload.get("client_id")
        media_type = payload.get("media_type", "image")
        size = payload.get("size", "1024x1024")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if not client_id:
            raise ValueError("client_id is required")

        client_id = client_id.lower()

        if client_id not in CLIENT_PROMPTS:
            raise ValueError(f"Invalid client_id. Available: {list(CLIENT_PROMPTS.keys())}")

        if media_type not in VALID_MEDIA_TYPES:
            raise ValueError("media_type must be 'image' or 'video'")

        system_prompt = CLIENT_PROMPTS[client_id]
        final_prompt = f"{system_prompt}\n\nUser Request: {prompt}"

        if media_type == "image":
            return self.generate_image(final_prompt, size)

        if media_type == "video":
            return self.generate_video(final_prompt)

        raise ValueError("Unsupported media_type")

    # =====================================================
    # IMAGE GENERATION
    # =====================================================

    def generate_image(self, final_prompt: str, size: str):

        response = client.images.generate(
            model="gpt-image-1",
            prompt=final_prompt,
            size=size
        )

        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        filename = f"img_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.png"
        filepath = os.path.join(IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return {
            "type": "image",
            "file_folder":IMAGE_DIR,
            "filename": filename,
            "path": filepath
        }

    # =====================================================
    # VIDEO GENERATION
    # =====================================================

    def generate_video(self, prompt: str):

        api_key = os.getenv("OPENAI_API_KEY")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "sora-2-pro",
            "prompt": prompt,
            "size": "1792x1024"
        }

        create_response = requests.post(
            "https://api.openai.com/v1/videos",
            headers=headers,
            json=payload
        )

        if create_response.status_code != 200:
            raise Exception(create_response.text)

        job = create_response.json()
        video_id = job.get("id")

        if not video_id:
            raise Exception("Video job creation failed")

        while True:
            poll_response = requests.get(
                f"https://api.openai.com/v1/videos/{video_id}",
                headers=headers
            )

            if poll_response.status_code != 200:
                raise Exception(poll_response.text)

            result = poll_response.json()
            status = result.get("status")

            if status == "completed":
                break

            if status == "failed":
                raise Exception("Video generation failed")

            time.sleep(3)

        content_response = requests.get(
            f"https://api.openai.com/v1/videos/{video_id}/content",
            headers=headers
        )

        if content_response.status_code != 200:
            raise Exception(content_response.text)

        filename = f"vid_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.mp4"
        filepath = os.path.join(VIDEO_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(content_response.content)

        return {
            "type": "video",
            "filename": filename,
            "path": filepath
        }


# =====================================================
# LOCAL TEST
# =====================================================

if __name__ == "__main__":

    agent = MediaAgent()

    test_payload = {
        "client_id": "optima",
        "prompt": "High performance battery product showcase",
        "media_type": "image",
        "size": "1024x1024"
    }

    result = agent.generate(test_payload)
    print(result)