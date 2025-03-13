import os
import fitz
import gc
import img2pdf
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from io import BytesIO
from PyPDF2 import PdfWriter, PdfMerger, PdfReader
from pdf2image import convert_from_path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tqdm import tqdm

# ---------- Enhanced PDF Functions ----------
def process_image(img, contrast=2.0, sharpness=200):
    """Simple pipeline: Invert colors → Boost contrast → Sharpen"""
    try:
        inverted = ImageOps.invert(img.convert("RGB"))
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(contrast)
        sharpened = contrasted.filter(ImageFilter.UnsharpMask(
            radius=1.5, 
            percent=sharpness, 
            threshold=2
        ))
        return sharpened
    except Exception as e:
        print(f"Image error: {str(e)}")
        return None
    finally:
        gc.collect()

def enhance_pdf(input_path, output_path, dpi=300):
    """PDF processing with minimal filters"""
    doc = fitz.open(input_path)
    writer = PdfWriter()
    
    for page_num in range(len(doc)):
        try:
            pix = doc[page_num].get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            processed = process_image(img)
            if not processed:
                continue
                
            with BytesIO() as buffer:
                processed.save(buffer, format="PNG", dpi=(dpi, dpi))
                pdf_bytes = img2pdf.convert(
                    buffer.getvalue(),
                    layout_fun=img2pdf.get_fixed_dpi_layout_fun((dpi, dpi)),
                    width=img2pdf.mm_to_pt(processed.width/dpi*25.4),
                    height=img2pdf.mm_to_pt(processed.height/dpi*25.4)
                )
                writer.append(BytesIO(pdf_bytes))
        except Exception as e:
            print(f"Page {page_num+1} error: {str(e)}")
            continue
        finally:
            if 'pix' in locals(): del pix
            if 'img' in locals(): del img
            if 'processed' in locals(): del processed
            if page_num % 10 == 0:
                gc.collect()
    
    with open(output_path, "wb") as f:
        writer.write(f)
    doc.close()

# ---------- Merge Slides Functions ----------
def process_slides_to_pdf(slides, output_path, dpi=300):
    A4_WIDTH, A4_HEIGHT = 2480, 3508  # 8.27" x 11.69" @300DPI
    SLIDES_PER_PAGE = 3
    output_pages = []

    for i in range(0, len(slides), SLIDES_PER_PAGE):
        page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))
        y_cursor = 0
        
        for slide in slides[i:i+SLIDES_PER_PAGE]:
            if slide.mode == 'RGBA':
                slide = slide.convert('RGB')
            
            orig_width, orig_height = slide.size
            target_height = A4_HEIGHT // SLIDES_PER_PAGE
            
            scale_factor = target_height / orig_height
            scaled_width = int(orig_width * scale_factor)
            
            if scaled_width > A4_WIDTH:
                scale_factor = A4_WIDTH / orig_width
                scaled_width = A4_WIDTH
                target_height = int(orig_height * scale_factor)
            
            resized = slide.resize((scaled_width, target_height), Image.LANCZOS)
            x_pos = (A4_WIDTH - scaled_width) // 2
            page.paste(resized, (x_pos, y_cursor))
            y_cursor += target_height
        
        output_pages.append(page)

    with open(output_path, "wb") as f:
        images_bytes = []
        for img in output_pages:
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95, dpi=(dpi, dpi))
            images_bytes.append(img_byte_arr.getvalue())
        
        pdf_bytes = img2pdf.convert(images_bytes, layout_fun=img2pdf.get_layout_fun(
            (img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69))
        ))
        f.write(pdf_bytes)

# ---------- Page Number Functions ----------
def get_page_number_position(position, page_width, page_height):
    positions = {
        "bottom left": (10, 10),
        "bottom right": (page_width - 30, 10),
        "top left": (10, page_height - 20),
        "top right": (page_width - 30, page_height - 20),
        "top middle": (page_width / 2 - 10, page_height - 20),
        "bottom middle": (page_width / 2 - 10, 10)
    }
    return positions.get(position, (10, 10))

def create_page_number_pdf(page_num, position, page_width, page_height):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    x, y = get_page_number_position(position, page_width, page_height)
    can.setFont("Helvetica", 12)
    can.drawString(x, y, str(page_num))
    can.save()
    packet.seek(0)
    return packet

def add_page_numbers(input_pdf_path, output_pdf_path, position, start_page=1):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        page_width = float(page.mediabox[2])
        page_height = float(page.mediabox[3])
        
        temp_pdf = create_page_number_pdf(start_page + i, position, page_width, page_height)
        page_number_reader = PdfReader(temp_pdf)
        page.merge_page(page_number_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)

# ---------- Main Workflow ----------
def get_poppler_path():
    """Helper function to get Poppler path from user"""
    return input("Enter path to Poppler's bin directory (e.g., C:\\poppler\\Library\\bin): ").strip()

def main():
    print("=== PDF Processing Tool ===")
    print("Choose an operation:")
    print("1. Full Workflow: Enhance PDFs → Merge Slides → Add Page Numbers")
    print("2. Enhance PDFs only")
    print("3. Merge PDF pages into 3 slides per A4 page")
    print("4. Add page numbers to a PDF")
    print("5. Convert images to PDF with page numbers")
    choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        input_folder = input("Enter path to folder containing PDFs: ").strip()
        output_dir = input("Enter output directory path: ").strip()
        base_name = input("Enter base name for output file (without extension): ").strip()
        position = input("Page number position (bottom left, bottom right, top left, top right, top middle, bottom middle): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())
        poppler_path = get_poppler_path()

        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Enhance all PDFs
        temp_enhanced_dir = os.path.join(output_dir, "temp_enhanced_pdfs")
        os.makedirs(temp_enhanced_dir, exist_ok=True)

        pdf_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')])
        if not pdf_files:
            print("No PDF files found in the input folder.")
            return

        print("\nEnhancing PDFs...")
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            input_path = os.path.join(input_folder, pdf_file)
            output_path = os.path.join(temp_enhanced_dir, f"enhanced_{pdf_file}")
            enhance_pdf(input_path, output_path)

        # Step 2: Convert all enhanced PDF pages to images
        all_slides = []
        enhanced_pdfs = sorted([f for f in os.listdir(temp_enhanced_dir) if f.endswith('.pdf')])

        print("\nConverting enhanced PDFs to slides...")
        for enhanced_pdf in tqdm(enhanced_pdfs, desc="Converting PDFs"):
            pdf_path = os.path.join(temp_enhanced_dir, enhanced_pdf)
            all_slides.extend(convert_from_path(
                pdf_path, 
                dpi=300, 
                fmt='jpeg',
                poppler_path=poppler_path
            ))

        # Step 3: Merge slides into 3 per page
        temp_merged_path = os.path.join(output_dir, "temp_merged.pdf")
        print("\nMerging slides into 3 per page...")
        process_slides_to_pdf(all_slides, temp_merged_path)

        # Step 4: Add page numbers
        final_output_path = os.path.join(output_dir, f"{base_name}.pdf")
        print("\nAdding page numbers...")
        add_page_numbers(temp_merged_path, final_output_path, position, start_page)

        # Cleanup
        for f in os.listdir(temp_enhanced_dir):
            os.remove(os.path.join(temp_enhanced_dir, f))
        os.rmdir(temp_enhanced_dir)
        os.remove(temp_merged_path)

        print(f"\nProcessing complete! Final output saved to: {final_output_path}")

    elif choice == '2':
        input_folder = input("Enter path to folder containing PDFs: ").strip()
        output_folder = input("Enter output directory path: ").strip()
        base_name = input("Enter base name for output files: ").strip()
        combine = input("Combine enhanced PDFs into one? (yes/no): ").lower() == 'yes'
        os.makedirs(output_folder, exist_ok=True)

        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("No PDFs found.")
            return

        if combine:
            merger = PdfMerger()
            temp_folder = os.path.join(output_folder, "temp_enhanced")
            os.makedirs(temp_folder, exist_ok=True)

            for pdf_file in tqdm(pdf_files, desc="Enhancing PDFs"):
                input_path = os.path.join(input_folder, pdf_file)
                temp_output = os.path.join(temp_folder, f"enhanced_{pdf_file}")
                enhance_pdf(input_path, temp_output)
                merger.append(temp_output)

            final_output = os.path.join(output_folder, f"{base_name}_combined.pdf")
            merger.write(final_output)
            merger.close()
            print(f"Combined enhanced PDF saved to {final_output}")
            # Cleanup
            for f in os.listdir(temp_folder):
                os.remove(os.path.join(temp_folder, f))
            os.rmdir(temp_folder)
        else:
            for pdf_file in tqdm(pdf_files, desc="Enhancing PDFs"):
                input_path = os.path.join(input_folder, pdf_file)
                output_path = os.path.join(output_folder, f"enhanced_{pdf_file}")
                enhance_pdf(input_path, output_path)
            print(f"Enhanced PDFs saved to {output_folder}")

    elif choice == '3':
        input_path = input("Enter path to PDF file or folder: ").strip()
        output_folder = input("Enter output directory path: ").strip()
        output_name = input("Enter output filename (without extension): ").strip() + ".pdf"
        output_path = os.path.join(output_folder, output_name)
        poppler_path = get_poppler_path()
        os.makedirs(output_folder, exist_ok=True)

        if os.path.isdir(input_path):
            pdf_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.pdf')]
        else:
            pdf_files = [input_path]

        all_slides = []
        for pdf_file in pdf_files:
            all_slides.extend(convert_from_path(
                pdf_file, 
                dpi=300, 
                fmt='jpeg',
                poppler_path=poppler_path
            ))

        process_slides_to_pdf(all_slides, output_path)
        print(f"Merged slides PDF saved to {output_path}")

    elif choice == '4':
        input_pdf = input("Enter path to PDF file: ").strip()
        output_pdf = input("Enter output PDF path: ").strip()
        position = input("Page number position (bottom left, etc.): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())

        add_page_numbers(input_pdf, output_pdf, position, start_page)
        print(f"Page numbers added. Saved to {output_pdf}")

    elif choice == '5':
        image_folder = input("Enter path to image folder: ").strip()
        output_pdf = input("Enter output PDF path: ").strip()
        position = input("Page number position (bottom left, etc.): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())
        dpi = 300

        images = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if not images:
            print("No images found.")
            return

        # Create temporary PDF
        temp_pdf = os.path.join(os.path.dirname(output_pdf), "temp_no_numbers.pdf")
        with open(temp_pdf, "wb") as f:
            images_bytes = []
            for img_file in images:
                img_path = os.path.join(image_folder, img_file)
                img = Image.open(img_path)
                img = img.convert('RGB')
                buf = BytesIO()
                img.save(buf, format='JPEG', dpi=(dpi, dpi))
                images_bytes.append(buf.getvalue())
            pdf_bytes = img2pdf.convert(images_bytes)
            f.write(pdf_bytes)

        # Add page numbers
        add_page_numbers(temp_pdf, output_pdf, position, start_page)
        os.remove(temp_pdf)
        print(f"PDF with page numbers saved to {output_pdf}")

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()import os
import fitz
import gc
import img2pdf
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from io import BytesIO
from PyPDF2 import PdfWriter, PdfMerger, PdfReader
from pdf2image import convert_from_path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from tqdm import tqdm

# ---------- Enhanced PDF Functions ----------
def process_image(img, contrast=2.0, sharpness=200):
    """Simple pipeline: Invert colors → Boost contrast → Sharpen"""
    try:
        inverted = ImageOps.invert(img.convert("RGB"))
        enhancer = ImageEnhance.Contrast(inverted)
        contrasted = enhancer.enhance(contrast)
        sharpened = contrasted.filter(ImageFilter.UnsharpMask(
            radius=1.5, 
            percent=sharpness, 
            threshold=2
        ))
        return sharpened
    except Exception as e:
        print(f"Image error: {str(e)}")
        return None
    finally:
        gc.collect()

def enhance_pdf(input_path, output_path, dpi=300):
    """PDF processing with minimal filters"""
    doc = fitz.open(input_path)
    writer = PdfWriter()
    
    for page_num in range(len(doc)):
        try:
            pix = doc[page_num].get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            processed = process_image(img)
            if not processed:
                continue
                
            with BytesIO() as buffer:
                processed.save(buffer, format="PNG", dpi=(dpi, dpi))
                pdf_bytes = img2pdf.convert(
                    buffer.getvalue(),
                    layout_fun=img2pdf.get_fixed_dpi_layout_fun((dpi, dpi)),
                    width=img2pdf.mm_to_pt(processed.width/dpi*25.4),
                    height=img2pdf.mm_to_pt(processed.height/dpi*25.4)
                )
                writer.append(BytesIO(pdf_bytes))
        except Exception as e:
            print(f"Page {page_num+1} error: {str(e)}")
            continue
        finally:
            if 'pix' in locals(): del pix
            if 'img' in locals(): del img
            if 'processed' in locals(): del processed
            if page_num % 10 == 0:
                gc.collect()
    
    with open(output_path, "wb") as f:
        writer.write(f)
    doc.close()

# ---------- Merge Slides Functions ----------
def process_slides_to_pdf(slides, output_path, dpi=300):
    A4_WIDTH, A4_HEIGHT = 2480, 3508  # 8.27" x 11.69" @300DPI
    SLIDES_PER_PAGE = 3
    output_pages = []

    for i in range(0, len(slides), SLIDES_PER_PAGE):
        page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))
        y_cursor = 0
        
        for slide in slides[i:i+SLIDES_PER_PAGE]:
            if slide.mode == 'RGBA':
                slide = slide.convert('RGB')
            
            orig_width, orig_height = slide.size
            target_height = A4_HEIGHT // SLIDES_PER_PAGE
            
            scale_factor = target_height / orig_height
            scaled_width = int(orig_width * scale_factor)
            
            if scaled_width > A4_WIDTH:
                scale_factor = A4_WIDTH / orig_width
                scaled_width = A4_WIDTH
                target_height = int(orig_height * scale_factor)
            
            resized = slide.resize((scaled_width, target_height), Image.LANCZOS)
            x_pos = (A4_WIDTH - scaled_width) // 2
            page.paste(resized, (x_pos, y_cursor))
            y_cursor += target_height
        
        output_pages.append(page)

    with open(output_path, "wb") as f:
        images_bytes = []
        for img in output_pages:
            img_byte_arr = BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=95, dpi=(dpi, dpi))
            images_bytes.append(img_byte_arr.getvalue())
        
        pdf_bytes = img2pdf.convert(images_bytes, layout_fun=img2pdf.get_layout_fun(
            (img2pdf.in_to_pt(8.27), img2pdf.in_to_pt(11.69))
        ))
        f.write(pdf_bytes)

# ---------- Page Number Functions ----------
def get_page_number_position(position, page_width, page_height):
    positions = {
        "bottom left": (10, 10),
        "bottom right": (page_width - 30, 10),
        "top left": (10, page_height - 20),
        "top right": (page_width - 30, page_height - 20),
        "top middle": (page_width / 2 - 10, page_height - 20),
        "bottom middle": (page_width / 2 - 10, 10)
    }
    return positions.get(position, (10, 10))

def create_page_number_pdf(page_num, position, page_width, page_height):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    x, y = get_page_number_position(position, page_width, page_height)
    can.setFont("Helvetica", 12)
    can.drawString(x, y, str(page_num))
    can.save()
    packet.seek(0)
    return packet

def add_page_numbers(input_pdf_path, output_pdf_path, position, start_page=1):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        page_width = float(page.mediabox[2])
        page_height = float(page.mediabox[3])
        
        temp_pdf = create_page_number_pdf(start_page + i, position, page_width, page_height)
        page_number_reader = PdfReader(temp_pdf)
        page.merge_page(page_number_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf_path, "wb") as f:
        writer.write(f)

# ---------- Main Workflow ----------
def get_poppler_path():
    """Helper function to get Poppler path from user"""
    return input("Enter path to Poppler's bin directory (e.g., C:\\poppler\\Library\\bin): ").strip()

def main():
    print("=== PDF Processing Tool ===")
    print("Choose an operation:")
    print("1. Full Workflow: Enhance PDFs → Merge Slides → Add Page Numbers")
    print("2. Enhance PDFs only")
    print("3. Merge PDF pages into 3 slides per A4 page")
    print("4. Add page numbers to a PDF")
    print("5. Convert images to PDF with page numbers")
    choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        input_folder = input("Enter path to folder containing PDFs: ").strip()
        output_dir = input("Enter output directory path: ").strip()
        base_name = input("Enter base name for output file (without extension): ").strip()
        position = input("Page number position (bottom left, bottom right, top left, top right, top middle, bottom middle): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())
        poppler_path = get_poppler_path()

        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Enhance all PDFs
        temp_enhanced_dir = os.path.join(output_dir, "temp_enhanced_pdfs")
        os.makedirs(temp_enhanced_dir, exist_ok=True)

        pdf_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')])
        if not pdf_files:
            print("No PDF files found in the input folder.")
            return

        print("\nEnhancing PDFs...")
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            input_path = os.path.join(input_folder, pdf_file)
            output_path = os.path.join(temp_enhanced_dir, f"enhanced_{pdf_file}")
            enhance_pdf(input_path, output_path)

        # Step 2: Convert all enhanced PDF pages to images
        all_slides = []
        enhanced_pdfs = sorted([f for f in os.listdir(temp_enhanced_dir) if f.endswith('.pdf')])

        print("\nConverting enhanced PDFs to slides...")
        for enhanced_pdf in tqdm(enhanced_pdfs, desc="Converting PDFs"):
            pdf_path = os.path.join(temp_enhanced_dir, enhanced_pdf)
            all_slides.extend(convert_from_path(
                pdf_path, 
                dpi=300, 
                fmt='jpeg',
                poppler_path=poppler_path
            ))

        # Step 3: Merge slides into 3 per page
        temp_merged_path = os.path.join(output_dir, "temp_merged.pdf")
        print("\nMerging slides into 3 per page...")
        process_slides_to_pdf(all_slides, temp_merged_path)

        # Step 4: Add page numbers
        final_output_path = os.path.join(output_dir, f"{base_name}.pdf")
        print("\nAdding page numbers...")
        add_page_numbers(temp_merged_path, final_output_path, position, start_page)

        # Cleanup
        for f in os.listdir(temp_enhanced_dir):
            os.remove(os.path.join(temp_enhanced_dir, f))
        os.rmdir(temp_enhanced_dir)
        os.remove(temp_merged_path)

        print(f"\nProcessing complete! Final output saved to: {final_output_path}")

    elif choice == '2':
        input_folder = input("Enter path to folder containing PDFs: ").strip()
        output_folder = input("Enter output directory path: ").strip()
        base_name = input("Enter base name for output files: ").strip()
        combine = input("Combine enhanced PDFs into one? (yes/no): ").lower() == 'yes'
        os.makedirs(output_folder, exist_ok=True)

        pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("No PDFs found.")
            return

        if combine:
            merger = PdfMerger()
            temp_folder = os.path.join(output_folder, "temp_enhanced")
            os.makedirs(temp_folder, exist_ok=True)

            for pdf_file in tqdm(pdf_files, desc="Enhancing PDFs"):
                input_path = os.path.join(input_folder, pdf_file)
                temp_output = os.path.join(temp_folder, f"enhanced_{pdf_file}")
                enhance_pdf(input_path, temp_output)
                merger.append(temp_output)

            final_output = os.path.join(output_folder, f"{base_name}_combined.pdf")
            merger.write(final_output)
            merger.close()
            print(f"Combined enhanced PDF saved to {final_output}")
            # Cleanup
            for f in os.listdir(temp_folder):
                os.remove(os.path.join(temp_folder, f))
            os.rmdir(temp_folder)
        else:
            for pdf_file in tqdm(pdf_files, desc="Enhancing PDFs"):
                input_path = os.path.join(input_folder, pdf_file)
                output_path = os.path.join(output_folder, f"enhanced_{pdf_file}")
                enhance_pdf(input_path, output_path)
            print(f"Enhanced PDFs saved to {output_folder}")

    elif choice == '3':
        input_path = input("Enter path to PDF file or folder: ").strip()
        output_folder = input("Enter output directory path: ").strip()
        output_name = input("Enter output filename (without extension): ").strip() + ".pdf"
        output_path = os.path.join(output_folder, output_name)
        poppler_path = get_poppler_path()
        os.makedirs(output_folder, exist_ok=True)

        if os.path.isdir(input_path):
            pdf_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.pdf')]
        else:
            pdf_files = [input_path]

        all_slides = []
        for pdf_file in pdf_files:
            all_slides.extend(convert_from_path(
                pdf_file, 
                dpi=300, 
                fmt='jpeg',
                poppler_path=poppler_path
            ))

        process_slides_to_pdf(all_slides, output_path)
        print(f"Merged slides PDF saved to {output_path}")

    elif choice == '4':
        input_pdf = input("Enter path to PDF file: ").strip()
        output_pdf = input("Enter output PDF path: ").strip()
        position = input("Page number position (bottom left, etc.): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())

        add_page_numbers(input_pdf, output_pdf, position, start_page)
        print(f"Page numbers added. Saved to {output_pdf}")

    elif choice == '5':
        image_folder = input("Enter path to image folder: ").strip()
        output_pdf = input("Enter output PDF path: ").strip()
        position = input("Page number position (bottom left, etc.): ").strip().lower()
        start_page = int(input("Starting page number: ").strip())
        dpi = 300

        images = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if not images:
            print("No images found.")
            return

        # Create temporary PDF
        temp_pdf = os.path.join(os.path.dirname(output_pdf), "temp_no_numbers.pdf")
        with open(temp_pdf, "wb") as f:
            images_bytes = []
            for img_file in images:
                img_path = os.path.join(image_folder, img_file)
                img = Image.open(img_path)
                img = img.convert('RGB')
                buf = BytesIO()
                img.save(buf, format='JPEG', dpi=(dpi, dpi))
                images_bytes.append(buf.getvalue())
            pdf_bytes = img2pdf.convert(images_bytes)
            f.write(pdf_bytes)

        # Add page numbers
        add_page_numbers(temp_pdf, output_pdf, position, start_page)
        os.remove(temp_pdf)
        print(f"PDF with page numbers saved to {output_pdf}")

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
