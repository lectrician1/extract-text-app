import os
import time
import json
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from pdf2image import convert_from_path
from dotenv import load_dotenv
from PIL import Image, ImageDraw
import shutil
import concurrent.futures

load_dotenv()

# Authenticate
subscription_key = os.getenv("AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY")
endpoint = os.getenv("AZURE_COMPUTER_VISION_ENDPOINT")

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

def overlay_bounding_boxes(image_path, bounding_boxes, output_folder):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    for box in bounding_boxes:
        x_coords = [box[0], box[2], box[4], box[6]]
        y_coords = [box[1], box[3], box[5], box[7]]
        left = min(x_coords)
        right = max(x_coords)
        top = min(y_coords)
        bottom = max(y_coords)
        draw.rectangle([left, top, right, bottom], outline="red", width=3)

    output_image_path = os.path.join(output_folder, os.path.basename(image_path))
    image.save(output_image_path, "PNG")
    return output_image_path

def extract_text(image_path):
    text_results = []
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
                    text_results.append({
                        "text": line.text,
                        "bounding_box": line.bounding_box
                    })
    return text_results

def process_files(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)
        if filename.lower().endswith('.pdf'):
            images = convert_from_path(file_path)
            for i, image in enumerate(images):
                image_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_page_{i+1}.png")
                image.save(image_path, "PNG")
                text_results = extract_text(image_path)
                save_text_results(output_folder, filename, text_results, i+1)
        else:
            output_image_path = os.path.join(output_folder, filename)
            shutil.copy(file_path, output_image_path)
            text_results = extract_text(output_image_path)
            save_text_results(output_folder, filename, text_results, None)

def save_text_results(output_folder, filename, text_results, page):
    json_filename = f"{os.path.splitext(filename)[0]}_page_{page}.json" if page else f"{os.path.splitext(filename)[0]}.json"
    json_path = os.path.join(output_folder, json_filename)
    with open(json_path, 'w') as json_file:
        json.dump({"filename": filename, "page": page, "text_results": text_results}, json_file)

def output_bounding_boxes(output_folder, output2_folder):
    for json_file in os.listdir(output_folder):
        if json_file.endswith('.json'):
            json_path = os.path.join(output_folder, json_file)
            with open(json_path, 'r') as file:
                data = json.load(file)
                filename = data["filename"]
                text_results = data["text_results"]
                image_filename = f"{os.path.splitext(filename)[0]}_page_{data['page']}.png" if data["page"] else filename
                image_path = os.path.join(output_folder, image_filename)
                overlay_bounding_boxes(image_path, [result["bounding_box"] for result in text_results], output2_folder)

def find_text_near_keyword(output_folder, output3_folder, keyword, radius=5, delta_x=0, delta_y=0):
    def process_json_file(json_file):
        json_path = os.path.join(output_folder, json_file)
        with open(json_path, 'r') as file:
            data = json.load(file)
            text_results = data["text_results"]
            extracted_text, keyword_center = find_text_near_keyword_in_results(text_results, keyword, radius, delta_x, delta_y)
            filename = data["filename"]
            page = data["page"]
            image_filename = f"{os.path.splitext(filename)[0]}_page_{page}.png" if page else filename
            image_path = os.path.join(output_folder, image_filename)
            if keyword_center:
                output_image_with_circle(image_path, keyword_center, radius, output3_folder)
            if extracted_text:
                if page:
                    print(f"Text found in {filename}, page {page}: {extracted_text}")
                else:
                    print(f"Text found in {filename}: {extracted_text}")
            else:
                if page:
                    print(f"{keyword} not found in {filename}, page {page}")
                else:
                    print(f"{keyword} not found in {filename}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        json_files = [f for f in os.listdir(output_folder) if f.endswith('.json')]
        executor.map(process_json_file, json_files)

def find_text_near_keyword_in_results(text_results, keyword, radius=5, delta_x=0, delta_y=0):
    keyword_box = None
    for result in text_results:
        if keyword in result["text"]:
            keyword_box = result["bounding_box"]
            break

    if not keyword_box:
        return None, None

    keyword_center_x = (keyword_box[0] + keyword_box[2] + keyword_box[4] + keyword_box[6]) / 4 + delta_x
    keyword_center_y = (keyword_box[1] + keyword_box[3] + keyword_box[5] + keyword_box[7]) / 4 + delta_y

    nearby_texts = []
    for result in text_results:
        text_box = result["bounding_box"]
        text_center_x = (text_box[0] + text_box[2] + text_box[4] + text_box[6]) / 4
        text_center_y = (text_box[1] + text_box[3] + text_box[5] + text_box[7]) / 4
        if abs(text_center_x - keyword_center_x) <= radius and abs(text_center_y - keyword_center_y) <= radius:
            nearby_texts.append(result["text"])

    return "\n".join(nearby_texts), (keyword_center_x, keyword_center_y)

def output_image_with_circle(image_path, circle_center, radius, output_folder):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    draw.ellipse((circle_center[0] - radius, circle_center[1] - radius, circle_center[0] + radius, circle_center[1] + radius), outline="blue", width=3)

    output_image_path = os.path.join(output_folder, os.path.basename(image_path))
    image.save(output_image_path, "PNG")
    return output_image_path

if __name__ == '__main__':
    input_folder = 'input'
    output_folder = 'output'
    output2_folder = 'output2'
    output3_folder = 'output3'
    keyword = "WHEATON"
    radius = 40
    delta_x = 1530  # Relative units to the right
    delta_y = 200  # Relative units down

    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output2_folder, exist_ok=True)
    os.makedirs(output3_folder, exist_ok=True)

    # process_files(input_folder, output_folder)
    # output_bounding_boxes(output_folder, output2_folder)
    find_text_near_keyword(output_folder, output3_folder, keyword, radius, delta_x, delta_y)
