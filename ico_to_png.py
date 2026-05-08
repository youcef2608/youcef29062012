from PIL import Image
import os

def ico_to_png():
    try:
        img = Image.open('icon.ico')
        # Extract the largest size for the PNG
        img.save('icon.png', 'PNG')
        print("Icon converted to PNG successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ico_to_png()
