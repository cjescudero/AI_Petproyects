import os
import sys
from openai import OpenAI

# Configure input and output languages
input_language = "English"  # Input language
output_language = "Spanish"  # Output language

# Paragraph separators
input_paragraph = ".\n"  # Input paragraph separator
output_paragraph = "\n\n"  # Output paragraph separator

# Configure input and output file names
input_file = "file_input.txt"  # Input file name
output_file = "file_translation.txt"  # Output file name

# Configure OpenAI API key in the shell
api_key = os.getenv("OPENAI_API_KEY_traductor")  # Get API key from environment variable


def translate_paragraph(paragraph, context=""):
    if not api_key:
        print("OpenAI API key is not configured.")
        print(
            "Please configure the OpenAI API key using the following command in your terminal:"
        )
        print("export OPENAI_API_KEY_traductor='your_api_key_here'")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    # Call the GPT model to translate the paragraph
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use the correct model
        messages=[
            {
                "role": "system",
                "content": f"You are an expert translator from {input_language} to {output_language}.",
            },
            {
                "role": "user",
                "content": f"Translate the following paragraph to Spanish. Use the provided context if necessary for a more accurate translation. Only give me the translated paragraph, as I will copy and paste it directly into a document.\n\nContext: {context}\n\nParagraph to translate: {paragraph}",
            },
        ],
        temperature=0.3,  # Reduce temperature for more consistent results
    )
    # Return the translated text
    return response.choices[0].message.content


def translate_file(input_file, output_file):
    # Read the content of the input file
    with open(input_file, "r") as f:
        content = f.read()

    # Split the content into paragraphs
    paragraphs = content.split(input_paragraph)

    # Translate and save to the output file
    with open(output_file, "w") as f:
        context = ""
        for paragraph in paragraphs:
            if paragraph.strip():  # If the paragraph is not empty
                translation = translate_paragraph(paragraph, context)
                f.write(translation + output_paragraph)
                # Update the context with the last 2 translated paragraphs
                context = (context + " " + translation).split()[-200:]
                context = " ".join(context)


def get_input_file():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return input("Please enter the path and name of the file to translate: ")


def get_output_file(input_file):
    input_path = os.path.dirname(input_file)
    input_filename = os.path.basename(input_file)
    output_filename = (
        os.path.splitext(input_filename)[0]
        + "_translated"
        + os.path.splitext(input_filename)[1]
    )
    return os.path.join(input_path, output_filename)


if __name__ == "__main__":
    input_file = get_input_file()
    output_file = get_output_file(input_file)
    translate_file(input_file, output_file)
    print(f"Translation completed. The translated file is located at: {output_file}")
