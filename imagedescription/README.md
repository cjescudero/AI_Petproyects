# Image Description Generator

This project uses OpenAI's API to generate descriptions for images. It supports various image formats including JPEG, PNG, and HEIF/HEIC.

## Requirements

- Python 3.6+
- OpenAI API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/image-description-generator.git
   cd image-description-generator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY='your-api-key-here'
   ```

## Usage

Run the script with the path to your image file:

```
python describe_image.py path/to/your/image.jpg
```

The script will generate a description of the image and display it in the console.

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- HEIF/HEIC (.heic)

## Notes

- Ensure you have sufficient credits in your OpenAI account to use the API.
- The quality of descriptions may vary depending on the complexity of the image.

## Contributing

Contributions are welcome. Please open an issue to discuss major changes before submitting a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
