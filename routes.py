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
            # Skickar förfrågan till OpenAI API för att generera ny bildvariant
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            { "type": "input_text", "text": prompt },  # Textprompt som beskriver önskad förändring
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}",  # Originalbilden i base64-format
                            },
                        ],
                    }
                ],
                tools=[{"type": "image_generation"}],  # Anger att vi vill generera bilder
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
                filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
                
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                
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
