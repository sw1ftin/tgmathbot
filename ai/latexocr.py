import os
from PIL import Image
from pix2tex.cli import LatexOCR
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class FormulaRecognizer:
    def __init__(self):
        total_config = {
            "text_formula": {
                "language": ("en", "ru"),
            }
        }
        self.model = LatexOCR()

    def recognize_from_image(self, image_path) -> str | None:
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            latex_formula = self.model(image)

            return latex_formula

        except Exception as e:
            print(f"Error during recognition: {str(e)}")
            return None

def main():
    try:
        recognizer = FormulaRecognizer()
        image_path = r"test\formula_and_text.png"
        formula = recognizer.recognize_from_image(image_path)
        if formula:
            print(f"Recognized formula: {formula}")

    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
