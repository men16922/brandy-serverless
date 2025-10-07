#!/usr/bin/env python3
"""
Test script to generate an image with Bedrock SDXL and save it to a file
"""

import sys
import os
import base64
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'lambda'))

from shared.bedrock_client import create_bedrock_client


def generate_and_save_image():
    """Generate an image with SDXL and save it"""
    
    print("🎨 Initializing Bedrock client...")
    client = create_bedrock_client(region='us-east-1')
    
    print(f"📝 Using model: {client.sdxl_model_id}")
    
    # Generate image
    prompt = "A modern Korean restaurant signboard with elegant typography, warm lighting, professional design"
    negative_prompt = "blurry, low quality, distorted, text errors"
    
    print(f"\n🖼️  Generating image with prompt:")
    print(f"   '{prompt}'")
    print(f"\n⏳ This may take 20-30 seconds...")
    
    result = client.invoke_sdxl(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=1024,
        height=1024,
        cfg_scale=7.0,
        steps=50,
        seed=42  # For reproducibility
    )
    
    print(f"\n✅ Image generated successfully!")
    print(f"   Latency: {result['latency_ms']}ms")
    print(f"   Seed: {result['seed']}")
    print(f"   Finish reason: {result['finish_reason']}")
    
    # Decode and save image
    image_data = base64.b64decode(result['image_base64'])
    
    # Create output directory if it doesn't exist
    output_dir = "generated_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/bedrock_sdxl_{timestamp}_seed{result['seed']}.png"
    
    # Save image
    with open(filename, 'wb') as f:
        f.write(image_data)
    
    print(f"\n💾 Image saved to: {filename}")
    print(f"   File size: {len(image_data):,} bytes")
    
    return filename


if __name__ == '__main__':
    try:
        filename = generate_and_save_image()
        print(f"\n🎉 Success! Open the image:")
        print(f"   open {filename}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
