import os
import base64
import uuid
import logging
import json
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def encode_image(image_path):
    """Convert image file to base64 format"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def create_image_variants_async(image_path, prompt, num_variants=1, output_folder='generated'):
    """Create image variants using OpenAI API - async version"""
    try:
        generated_images = []
        
        for i in range(num_variants):
            # Konverterar originalbilden till base64-sträng
            base64_image = encode_image(image_path)

            # Skickar förfrågan till OpenAI API för att generera ny bildvariant
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            { "type": "input_text", "text": prompt },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        ],
                    }
                ],
                tools=[{"type": "image_generation"}],
            )

            # Extraherar bilddata från API-svaret
            image_data = [
                output.result
                for output in response.output
                if output.type == "image_generation_call"
            ]

            # Sparar den genererade bilden till fil om data finns
            if image_data:
                image_base64 = image_data[0]
                filename = f"variant_{uuid.uuid4()}_{i}.png"
                filepath = os.path.join(output_folder, filename)
                
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                
                generated_images.append({
                    'filename': filename,
                    'filepath': filepath
                })
        
        return {
            'success': True,
            'images': generated_images
        }
        
    except Exception as e:
        logging.error(f"Error creating image variants: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }