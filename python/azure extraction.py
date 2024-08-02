from flask import Flask, request, render_template, send_from_directory
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from pdf2image import convert_from_path
import os
import time
from dotenv import load_dotenv
from PIL import Image, ImageDraw

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Authenticate
subscription_key = os.getenv("AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY")
endpoint = os.getenv("AZURE_COMPUTER_VISION_ENDPOINT")

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

def overlay_bounding_boxes(image_path, bounding_boxes, output_folder):
    # Load the image
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Draw each bounding box
    for box in bounding_boxes:
        x_coords = [box[0], box[2], box[4], box[6]]
        y_coords = [box[1], box[3], box[5], box[7]]
        left = min(x_coords)
        right = max(x_coords)
        top = min(y_coords)
        bottom = max(y_coords)
        draw.rectangle([left, top, right, bottom], outline="red", width=3)

    # Save the image to the output folder
    output_image_path = os.path.join(output_folder, os.path.basename(image_path))
    image.save(output_image_path, "PNG")
    return output_image_path

def read_image(image_path):
    bounding_boxes = []
    print(f"\nReading {image_path}")
    with open(image_path, "rb") as image_file:
        read_response = computervision_client.read_in_stream(image_file, raw=True)
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    bounding_boxes.append(line.bounding_box)
    return bounding_boxes

def process_files(files, output_folder):
    processed_files = []
    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        if file.filename.lower().endswith('.pdf'):
            images = convert_from_path(file_path)
            for i, image in enumerate(images):
                image_path = os.path.join(output_folder, f"{os.path.splitext(file.filename)[0]}_page_{i+1}.png")
                image.save(image_path, "PNG")
                bounding_boxes = read_image(image_path)
                processed_image_path = overlay_bounding_boxes(image_path, bounding_boxes, output_folder)
                processed_files.append(processed_image_path)
        else:
            bounding_boxes = read_image(file_path)
            processed_image_path = overlay_bounding_boxes(file_path, bounding_boxes, output_folder)
            processed_files.append(processed_image_path)
    return processed_files

# Custom filter to get the basename of a file path
@app.template_filter('basename')
def basename_filter(s):
    return os.path.basename(s)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files' not in request.files:
            return "No files part"
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return "No selected file"
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
        processed_files = process_files(files, app.config['PROCESSED_FOLDER'])
        return render_template('index.html', files=processed_files)
    return render_template('index.html')

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    #app.run(debug=True)

    
