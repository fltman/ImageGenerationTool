import os
import base64
import uuid
import logging
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from openai import OpenAI
from app import app

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path):
    """Convert image file to base64 format"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def create_image_variants(image_path, prompt, num_variants=1):
    """Create image variants using OpenAI API based on the original code pattern"""
    try:
        # Convert image to base64
        base64_image = encode_image(image_path)
        
        generated_images = []
        
        for i in range(num_variants):
            # Using DALL-E 3 for image generation with the uploaded image as reference
            # Note: DALL-E 3 doesn't support direct image-to-image variation like the original code
            # We'll use image analysis + generation as a workaround
            
            # First, analyze the uploaded image
            analysis_response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this image and then create a detailed prompt for generating a similar image with this modification: {prompt}. Focus on describing the key elements, style, composition, and how to apply the requested changes."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            enhanced_prompt = analysis_response.choices[0].message.content
            
            # Generate new image based on the enhanced prompt
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024"
            )
            
            # Download and save the generated image
            import requests
            image_url = image_response.data[0].url
            response = requests.get(image_url)
            
            if response.status_code == 200:
                filename = f"variant_{uuid.uuid4()}_{i}.png"
                filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                generated_images.append({
                    'filename': filename,
                    'filepath': filepath
                })
        
        return generated_images
        
    except Exception as e:
        logging.error(f"Error creating image variants: {str(e)}")
        raise e

@app.route('/')
def index():
    """Main page for image upload and variant generation"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and generate variants"""
    try:
        # Check if files were uploaded
        if 'images' not in request.files:
            flash('Inga filer valda', 'error')
            return redirect(url_for('index'))
        
        files = request.files.getlist('images')
        prompt = request.form.get('prompt', '').strip()
        num_variants = int(request.form.get('num_variants', 1))
        
        # Validate inputs
        if not prompt:
            flash('Prompt måste anges', 'error')
            return redirect(url_for('index'))
        
        if not (1 <= num_variants <= 10):
            flash('Antal varianter måste vara mellan 1 och 10', 'error')
            return redirect(url_for('index'))
        
        if not files or all(f.filename == '' for f in files):
            flash('Inga filer valda', 'error')
            return redirect(url_for('index'))
        
        results = []
        
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                # Save uploaded file
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                try:
                    # Generate variants
                    variants = create_image_variants(filepath, prompt, num_variants)
                    
                    results.append({
                        'original_filename': filename,
                        'original_path': filepath,
                        'variants': variants,
                        'prompt': prompt
                    })
                    
                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}")
                    flash(f'Fel vid bearbetning av {filename}: {str(e)}', 'error')
        
        if not results:
            flash('Inga bilder kunde bearbetas', 'error')
            return redirect(url_for('index'))
        
        return render_template('results.html', results=results)
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash(f'Ett fel uppstod: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download a generated image"""
    try:
        filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            flash('Filen kunde inte hittas', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        flash(f'Fel vid nedladdning: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/image/<path:filename>')
def serve_image(filename):
    """Serve images for preview"""
    try:
        # Check both upload and generated folders
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        generated_path = os.path.join(app.config['GENERATED_FOLDER'], filename)
        
        if os.path.exists(upload_path):
            return send_file(upload_path)
        elif os.path.exists(generated_path):
            return send_file(generated_path)
        else:
            return "Bild inte funnen", 404
    except Exception as e:
        logging.error(f"Image serve error: {str(e)}")
        return "Fel vid visning av bild", 500

@app.errorhandler(413)
def too_large(e):
    flash('Filen är för stor. Maximal storlek är 50MB.', 'error')
    return redirect(url_for('index'))
