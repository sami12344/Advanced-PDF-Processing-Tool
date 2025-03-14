# 📄 Advanced PDF Processing Tool

## 🚀 Overview
This tool is a powerful and automated solution for processing PDF files. Whether you need to enhance PDFs, merge slides, or add page numbers, this tool has got you covered! Designed for both technical and non-technical users, it simplifies PDF workflows with an easy-to-use interface.

## ✨ Features
✔️ **Enhance PDFs** – Improve contrast, sharpness, and readability.  
✔️ **Merge Slides** – Combine multiple slides into an A4 PDF layout.  
✔️ **Add Page Numbers** – Customize page numbering in different positions.  
✔️ **Convert Images to PDF** – Easily create PDFs from image files.  
✔️ **Full Workflow Automation** – Perform all steps in one go.  

---

## 🛠️ How to Use
Run the script and follow the prompts to select an operation.

### 1️⃣ Full Workflow (Enhance → Merge → Add Page Numbers)
🔹 **Step 1:** Place your PDFs in a folder.  
🔹 **Step 2:** Run the script and select **Full Workflow**.  
🔹 **Step 3:** Provide input folder, output directory, and base filename.  
🔹 **Step 4:** Choose where to place page numbers (e.g., bottom right).  
🔹 **Step 5:** Wait for processing to complete. 🎉 Done!  

### 2️⃣ Enhance PDFs Only
🔹 **Step 1:** Select the option **Enhance PDFs only**.  
🔹 **Step 2:** Provide the folder containing PDFs.  
🔹 **Step 3:** Choose an output directory.  
🔹 **Step 4:** Optionally, combine enhanced PDFs into one file.  
🔹 **Step 5:** Wait for processing. 🎉 Done!

### 3️⃣ Merge Slides into A4 Pages
🔹 **Step 1:** Select the **Merge PDF pages into slides** option.  
🔹 **Step 2:** Choose a PDF file or a folder with slides.  
🔹 **Step 3:** Provide an output filename and directory.  
🔹 **Step 4:** Wait for processing. 🎉 Done!

### 4️⃣ Add Page Numbers
🔹 **Step 1:** Choose the **Add page numbers** option.  
🔹 **Step 2:** Select the PDF file.  
🔹 **Step 3:** Choose a numbering position (bottom left, top right, etc.).  
🔹 **Step 4:** Set the starting page number.  
🔹 **Step 5:** Wait for processing. 🎉 Done!

### 5️⃣ Convert Images to PDF with Page Numbers
🔹 **Step 1:** Choose **Convert images to PDF with page numbers**.  
🔹 **Step 2:** Provide the folder containing images.  
🔹 **Step 3:** Select an output filename.  
🔹 **Step 4:** Choose the position for page numbers.  
🔹 **Step 5:** Wait for processing. 🎉 Done!

---

## 🔧 Requirements
Ensure you have the following installed before running the script:
- Python 3.x
- Required Libraries:
  ```sh
  pip install pymupdf pillow img2pdf pypdf pdf2image reportlab tqdm
  ```
- **For Windows Users:** Install `poppler` for `pdf2image`. ([Download here](https://github.com/oschwartz10612/poppler-windows/releases))

---

## 📌 Running the Script
1. Open a terminal or command prompt.
2. Navigate to the folder containing the script.
3. Run:
   ```sh
   python main.py
   ```
4. Follow the on-screen instructions. 🎉

---

## 🤖 Automation Possibilities
You can automate the script by passing arguments instead of user input. Example:
```sh
python script.py --enhance "input_folder" --merge "output_folder" --numbering "bottom right" --start 1
```

---

## 🎯 Use Cases
✔️ **Students & Teachers** – Enhance study materials and create organized PDFs.  
✔️ **Business Professionals** – Format presentations and add branding.  
✔️ **Researchers** – Improve document readability and organization.  
✔️ **General Users** – Quickly process PDFs without hassle.  

---

## 💡 Contribute & Improve
We welcome improvements! Feel free to fork, modify, and submit pull requests.

📩 **Have questions?** Open an issue or reach out! Happy processing! 🚀

