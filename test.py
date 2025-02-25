from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
import os
from datetime import datetime

def merge_images_with_custom_layout(image1_path, image2_path, image3_path=None):
    try:
        # Open the images and convert to grayscale
        id_image = Image.open(image1_path).convert("L")
        stamp_image = Image.open(image2_path).convert("L")
        
        # Only load id_back_image if image3_path is provided
        if image3_path:
            id_back_image = Image.open(image3_path).convert("L")
        else:
            id_back_image = None

        # Get the default size of each image
        id_width, id_height = id_image.size
        stamp_width, stamp_height = stamp_image.size

        if id_back_image:
            back_width, back_height = id_back_image.size
        else:
            back_width, back_height = 0, 0

        # Maximum width and height for scaling (you can adjust this limit)
        MAX_WIDTH = 600
        MAX_HEIGHT = 400

        # Scale the images if they are too large
        if id_width > MAX_WIDTH or id_height > MAX_HEIGHT:
            scale_factor = min(MAX_WIDTH / id_width, MAX_HEIGHT / id_height)
            id_image = id_image.resize((int(id_width * scale_factor), int(id_height * scale_factor)))
        
        if stamp_width > MAX_WIDTH or stamp_height > MAX_HEIGHT:
            scale_factor = min(MAX_WIDTH / stamp_width, MAX_HEIGHT / stamp_height)
            stamp_image = stamp_image.resize((int(stamp_width * scale_factor), int(stamp_height * scale_factor)))
        
        if id_back_image:
            if back_width > MAX_WIDTH or back_height > MAX_HEIGHT:
                scale_factor = min(MAX_WIDTH / back_width, MAX_HEIGHT / back_height)
                id_back_image = id_back_image.resize((int(back_width * scale_factor), int(back_height * scale_factor)))

        # Determine the canvas size
        canvas_width = max(id_image.width, stamp_image.width) + 100
        canvas_height = id_image.height + (id_back_image.height if id_back_image else 0) + stamp_image.height + 75
        white_bg = Image.new("RGB", (canvas_width, canvas_height), "white")

        # Position for id_image
        id_x = (canvas_width - id_image.width) // 2
        id_y = 25   
        white_bg.paste(id_image.convert("RGB"), (id_x, id_y)) 
        
        # Position for id_back_image (under the id_image), if provided
        if id_back_image:
            back_id_x = (canvas_width - id_back_image.width) // 2
            back_id_y = id_y + id_image.height + 10
            white_bg.paste(id_back_image.convert("RGB"), (back_id_x, back_id_y)) 
            stamp_y = back_id_y + id_back_image.height + 25
        else:
            stamp_y = id_y + id_image.height + 25
        
        # Position for the stamp_image
        stamp_x = canvas_width - stamp_image.width - 50 
        white_bg.paste(stamp_image.convert("RGB"), (stamp_x, stamp_y))  

        # Add the current date to the image
        draw = ImageDraw.Draw(white_bg)
        current_date = datetime.now().strftime("%Y-%m-%d")
        font_size = 18 
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default() 

        stamp_center_x = stamp_x + (stamp_image.width // 2)
        stamp_center_y = stamp_y + (stamp_image.height // 2)

        # Get text size for positioning
        bbox = draw.textbbox((0, 0), current_date, font=font)
        text_width = bbox[2] - bbox[0]  
        text_height = bbox[3] - bbox[1] 
        text_x = stamp_center_x - (text_width // 2) 
        text_y = stamp_center_y - (text_height // 2)   

        # Add a white background behind the text for visibility
        padding = 10  
        draw.rectangle(
            [text_x - padding, text_y - padding, text_x + text_width + padding, text_y + text_height + padding],
            fill="white"
        )

        # Draw the date text on the image
        draw.text((text_x, text_y), current_date, fill="black", font=font)

        # Save the temporary image
        temp_image_path = "merged_image.jpg"
        white_bg.save(temp_image_path) 

        # Convert the image to a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.image(temp_image_path, x=10, y=10, w=190) 
        output_pdf_path = "output.pdf"
        pdf.output(output_pdf_path) 

        # Remove the temporary image file
        os.remove(temp_image_path)

        print(f"PDF created and displayed successfully at: {output_pdf_path}")
        return output_pdf_path
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    image1_path = "face.jpg"
    image2_path = "media/stamps/stamp.jpg"
    image3_path = "face.jpg"  # Or set this to None if you don't want to provide this image
    
    output_pdf = merge_images_with_custom_layout(image1_path, image2_path, image3_path)
    print(f"PDF saved at: {output_pdf}")
