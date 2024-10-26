import os
from openai import OpenAI
import base64
from PIL import Image
import argparse
import pillow_heif
from pillow_heif import register_heif_opener
import io


# Function to encode the image
def encode_image(image_path):
    # Register the HEIF opener
    register_heif_opener()

    with Image.open(image_path) as img:
        # Convert all images to JPEG
        img = img.convert("RGB")
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str


# Function to describe the image using OpenAI API
def describe_image(client, image_path, language="español"):
    base64_image = encode_image(image_path)

    prompt = "¿Qué hay en la imagen? Describe esta imagen en detalle."
    if language.lower() != "español":
        prompt = f"What's in this image? Describe this image in detail in {language}."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    return response.choices[0].message.content


# Function to check if the file is a valid image
def is_valid_image(file_path):
    try:
        register_heif_opener()
        with Image.open(file_path) as img:
            img.verify()
        return True
    except:
        return False


# Function to process images (single file or directory)
def process_images(input_path, language="english"):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    results = []

    if os.path.isfile(input_path):
        if is_valid_image(input_path):
            description = describe_image(client, input_path, language)
            print(f"\n## {os.path.basename(input_path)}")
            print(description)
            print("\n" + "-" * 50 + "\n")
            results.append((input_path, description))
        else:
            print(f"The file {input_path} is not a valid image.")
    elif os.path.isdir(input_path):
        print(f"Processing directory: {input_path}")
        image_count = 0
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if os.path.isfile(file_path) and (
                is_valid_image(file_path) or file_path.lower().endswith(".heic")
            ):
                image_count += 1
                print(f"Processing image: {file_path}")
                try:
                    description = describe_image(client, file_path, language)
                    print(f"\n## {filename}")
                    print(description)
                    print("\n" + "-" * 50 + "\n")
                    results.append((file_path, description))
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

        if image_count == 0:
            print("No valid images found in the directory.")

    return results


# Function to save results to a markdown file
def save_to_markdown(results, input_path):
    # Remove single quotes from the input path
    input_path = input_path.strip("'")

    if os.path.isdir(input_path):
        md_file_path = os.path.join(input_path, f"{os.path.basename(input_path)}.md")
    else:
        base_name = os.path.splitext(input_path)[0]
        md_file_path = f"{base_name}.md"

    with open(md_file_path, "w", encoding="utf-8") as f:
        for file_path, description in results:
            f.write(f"## {os.path.basename(file_path)}\n\n")
            f.write(f"{description}\n\n")

    print(f"Descriptions have been saved to {md_file_path}")


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Describe images using OpenAI.")
    parser.add_argument(
        "input_path",
        nargs="?",
        default=None,
        help="Path to the image file or folder (optional)",
    )
    parser.add_argument(
        "--language",
        default="español",
        help="Language for descriptions (default: español)",
    )
    args = parser.parse_args()

    # Check if the API key is configured
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: The OPENAI_API_KEY environment variable is not set.")
        print("Please set it with your OpenAI API key before running the script.")
        exit(1)

    input_path = args.input_path
    if input_path is None:
        input_path = input("Please enter the path to the image file or folder: ").strip(
            "'\""
        )

    print(f"Input path: {input_path}")
    if not os.path.exists(input_path):
        print(f"Error: The path {input_path} does not exist.")
        exit(1)

    # Check if the file is .heic or if it's a directory
    if input_path.lower().endswith(".heic") or os.path.isdir(input_path):
        print(
            "Make sure you have the pillow_heif library installed to process .heic files"
        )
        print("You can install it with: pip install pillow-heif")

    results = process_images(input_path, args.language)
    if results:
        save_to_markdown(results, input_path)
        print("Process completed.")
    else:
        print("No images were processed. No .md file will be generated.")
