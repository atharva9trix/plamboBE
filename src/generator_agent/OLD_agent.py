import os
import time
import base64
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import requests

load_dotenv()

# Initialize OpenAI client
client = os.getenv("OPENAI_API_KEY")
IMAGE_DIR = "generated_data/images"
VIDEO_DIR = "generated_data/videos"

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# =====================================================
# CLIENT SYSTEM PROMPT REGISTRY (Multi-Tenant Support)
# =====================================================

CLIENT_PROMPTS = {

    "kalahari": """
You generate visuals for Kalahari Resort, a premium indoor waterpark and family entertainment resort environment.

Primary Environment:
- Large-scale indoor waterpark and indoor resort setting
- High vaulted ceilings with structural beams
- Controlled indoor lighting
- Colorful slides, wave pools, lazy rivers
- Indoor palm trees and African-inspired d�cor
- Bright artificial lighting with warm ambience
- Commercial photography aesthetic

Atmosphere:
- Energetic, family-friendly
- Guests enjoying water attractions indoors
- Reflections from water surfaces
- Safe, upscale hospitality experience

Cinematography:
- Dynamic tracking shots
- Smooth gliding camera motion
- High-end resort advertisement tone

Avoid:
- Outdoor beach settings
- Ocean coastlines
- Desert environments
- Dark gritty visuals
- Cartoon style
""",

"tech_brand": """
You generate visuals for a premium futuristic technology brand.

Environment:
- Minimalist modern interiors
- Glass, steel, neon accents
- Dark mode lighting
- Futuristic holographic UI elements

Tone:
- Innovative
- Premium
- Disruptive
- Corporate clean aesthetic

Avoid:
- Rustic themes
- Cartoon visuals
- Nature-heavy backgrounds
""",

"optima": """
You are a high-precision visual generation model producing brand-aligned imagery for Optima Batteries.

Brand Identity:
Optima Batteries represents engineered performance, durability, and premium power solutions for automotive and marine environments.

Brand Attributes:
- Strong industrial, performance-driven aesthetic
- Dominant color palette: black, yellow, red, metallic steel tones
- Rugged, durable, premium battery applications
- Clean, technical, professional composition

Visual Style Guidelines:
- Hyper-realistic rendering quality
- Dynamic, directional lighting emphasizing edges and reflective surfaces
- Focus on battery products as primary hero elements
- Industrial, mechanical, garage, marine dock, or minimal technical gradient backgrounds
- High contrast, sharp detail, dramatic light-to-shadow interplay
- Subtle cues of power, torque, ignition, energy flow, performance engineering

Composition Rules:
- Product-centered framing
- Bold presence with confident negative space
- Website hero-ready proportions
- Clean, uncluttered visual hierarchy

Output Objectives:
- Portfolio-grade marketing visuals
- Website hero banners
- Product catalog imagery
- High-performance branding collateral

Strictly Avoid:
- Cartoon or flat illustrations
- Pastel or soft casual aesthetics
- Lifestyle clutter or unrelated props
- Whimsical styling
- Distracting environments

Generate imagery that embodies strength, engineered reliability, high-output power, and premium mechanical precision.
""",
"plambo": """
You are an advanced visual generation engine producing brand-aligned imagery for Plambo Solutions.

Brand Identity:
Plambo Solutions represents enterprise-grade technology services, digital transformation, and modern business infrastructure.

Brand Attributes:
- Corporate professionalism
- Clean, structured visual identity
- Sophisticated technology and services narrative
- Palette: cool neutrals, deep blues, slate greys, crisp whites, subtle modern accents

Visual Style Guidelines:
- High-resolution semi-photoreal or modern stylized corporate visuals
- Contexts: enterprise workflows, digital dashboards, collaboration, strategy execution
- Minimal, uncluttered office or abstract tech environments
- Soft gradient lighting and intelligent negative space
- Subtle visual cues of connectivity, integration, data flow, modular systems

Composition Rules:
- Balanced, structured layouts
- Clear focal hierarchy
- Professional and enterprise-ready tone
- No excessive visual noise

Output Objectives:
- Website hero banners
- Service category headers
- Corporate pitch decks
- Client-facing business collateral

Strictly Avoid:
- Cartoonish or playful aesthetics
- Pop culture references
- Overly saturated or harsh color palettes
- Informal or startup-chaotic vibes

Generate imagery that communicates efficiency, trustworthiness, strategic clarity, and business-critical competence.
""",

"sovereignsilver": """
You are a premium visual generation engine producing brand-aligned imagery for Sovereign Silver.

Brand Identity:
Sovereign Silver represents natural wellness grounded in refined science, purity, and personal health sovereignty.

Brand Positioning:
- Natural health and scientifically refined wellness products
- Ultra-pure colloidal silver hydrosol solutions
- Messaging centered on Health Sovereignty� and empowered well-being

Core Visual Style:
- High-resolution, clean, minimal compositions
- Neutral and natural palettes: soft whites, muted beiges, gentle blues, metallic silver accents
- Crisp, clinical lighting with smooth gradients
- Glass product bottles with clear liquid and subtle silver cues

Contextual Elements:
- Natural purity signals (water droplets, soft daylight, clean surfaces)
- Subtle molecular or scientific visual cues
- Calm wellness environments
- Balanced, uncluttered composition
- Modern, premium medicinal aesthetic

Design Objectives:
- Website hero imagery
- Product highlight banners
- FDA-compliant medicinal wellness visuals
- Lifestyle imagery reflecting balance and natural living

Strictly Avoid:
- Cartoon styles
- Harsh contrast or aggressive lighting
- Cluttered backgrounds
- Fantasy elements
- Overly stylized or exaggerated health claims visuals

Generate imagery that communicates purity, refined science, trust, authenticity, and elevated modern wellness.
"""
}

VALID_MEDIA_TYPES = {"image", "video"}


# =====================================================
# MEDIA AGENT
# =====================================================

#class MediaAgent:
#
#    @staticmethod
#    def generate(self,payload: dict):
#        prompt = payload.get("prompt")
#        client_id = payload.get("client_id")
#        media_type = payload.get("media_type", "image")
#        size = payload.get("size", "1024x1024")
#
#        # ---- VALIDATION ----
#
#        if not prompt or not prompt.strip():
#            raise ValueError("Prompt cannot be empty")
#
#        if not client_id:
#            raise ValueError("client_id is required")
#
#        client_id = client_id.lower()
#
#        if client_id not in CLIENT_PROMPTS:
#            raise ValueError(f"Invalid client_id. Available: {list(CLIENT_PROMPTS.keys())}")
#
#        if media_type not in VALID_MEDIA_TYPES:
#            raise ValueError("media_type must be 'image' or 'video'")
#
#        # ---- BUILD FINAL PROMPT ----
#
#        system_prompt = CLIENT_PROMPTS[client_id]
#        final_prompt = f"{system_prompt}\n\nUser Request: {prompt}"
#
#        # ---- ROUTING ----
#
#        if media_type == "image":
#            return MediaAgent.generate_image(final_prompt, size)
#
#        elif media_type == "video":
#            return MediaAgent.generate_video(final_prompt)


class MediaAgent:

    def generate(self, payload: dict):
        prompt = payload.get("prompt")
        client_id = payload.get("client_id")
        media_type = payload.get("media_type", "image")
        size = payload.get("size", "1024x1024")

        # ---- VALIDATION ----
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if not client_id:
            raise ValueError("client_id is required")

        client_id = client_id.lower()

        if client_id not in CLIENT_PROMPTS:
            raise ValueError(f"Invalid client_id. Available: {list(CLIENT_PROMPTS.keys())}")

        if media_type not in VALID_MEDIA_TYPES:
            raise ValueError("media_type must be 'image' or 'video'")

        # ---- BUILD FINAL PROMPT ----
        system_prompt = CLIENT_PROMPTS[client_id]
        final_prompt = f"{system_prompt}\n\nUser Request: {prompt}"

        # ---- ROUTING ----
        if media_type == "image":
            return self.generate_image(final_prompt, size)

        elif media_type == "video":
            return self.generate_video(final_prompt)

        else:
            raise ValueError("Unsupported media_type")

    # =====================================================
    # IMAGE GENERATION
    # =====================================================

#    @staticmethod
#    def generate_image(self,prompt: str, size: str):
#
#        response = client.images.generate(
#            model="gpt-image-1",
#            prompt=prompt,
#            size="1024x1024"
#        )
#
#        image_base64 = response.data[0].b64_json
#        image_bytes = base64.b64decode(image_base64)
#
#        filename = f"img_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.png"
#        filepath = os.path.join(IMAGE_DIR, filename)
#
#        with open(filepath, "wb") as f:
#            f.write(image_bytes)
#
#        return {
#            "status": "success",
#            "type": "image",
#            "filename": filename,
#            "path": filepath
#        }
    def generate_image(self, final_prompt: str, size: str):
        response = client.images.generate(
            model="gpt-image-1",
            prompt=final_prompt,
            size=size
        )

        image_base64 = response.data[0].b64_json

        filename = f"img_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.png"
        filepath = os.path.join("images", filename)

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(image_base64))

        return {
            "type": "image",
            "filename": filename
        }
    # =====================================================
    # VIDEO GENERATION
    # =====================================================

    @staticmethod
    def generate_video(self,prompt: str):

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

        # STEP 1: Create job
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

        # STEP 2: Poll until completed
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

        # STEP 3: Download video
        content_response = requests.get(
            f"https://api.openai.com/v1/videos/{video_id}/content",
            headers=headers
        )

        if content_response.status_code != 200:
            raise Exception(content_response.text)

        video_bytes = content_response.content

        filename = f"vid_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.mp4"
        filepath = os.path.join(VIDEO_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(video_bytes)

        return {
            "status": "success",
            "type": "video",
            "filename": filename,
            "path": filepath
        }


# =====================================================
# EXAMPLE USAGE (You can remove in production)
# =====================================================

if __name__ == "__main__":

    test_payload = {
        "client_id": "optima",
        "prompt": "A battery product display",
        "media_type": "image",
        "size": "1024x1024"
    }

    result = MediaAgent.generate(test_payload)
    print(result)