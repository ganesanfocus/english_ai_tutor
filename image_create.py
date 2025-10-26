from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = "a stylish eco-friendly water bottle on a moss-covered rock in a forest, glowing in sunlight"

response = client.images.generate(
    model="dall-e-2",  # Explicitly specify DALL-E 2
    prompt=prompt,
    n=1,  # Number of images to generate
    size="512x512"  # Image resolution
)

# Extract and display the image URL
image_url = response.data[0].url
print("Generated image URL:", image_url)