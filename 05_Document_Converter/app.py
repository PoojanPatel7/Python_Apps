import os
import tempfile
from flask import Flask, request, send_file, render_template_string
import pypandoc
from docx2pdf import convert as convert_to_pdf

# Automatically fix the Pandoc error by downloading it if it's missing!
print("Checking for Pandoc installation...")
try:
    pypandoc.get_pandoc_version()
except OSError:
    print("Pandoc not found. Downloading it automatically... (This may take a minute)")
    pypandoc.download_pandoc()
    print("Pandoc downloaded successfully!")

app = Flask(__name__)

# ==========================================
# 1. HTML, CSS, and JS (Frontend)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline Document Converter</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 500px; text-align: center; }
        h1 { color: #2c3e50; font-size: 24px; }
        p { color: #7f8c8d; font-size: 14px; margin-bottom: 20px; }
        select, input[type="file"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background-color: #3498db; color: white; border: none; padding: 12px 20px; width: 100%; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; transition: background 0.3s; }
        button:hover { background-color: #2980b9; }
        #status { margin-top: 15px; font-weight: bold; font-size: 14px; }
        .error { color: #e74c3c; }
        .success { color: #2ecc71; }
    </style>
</head>
<body>

<div class="container">
    <h1>🔄 Universal Converter</h1>
    <p>Convert TXT, DOCX, MD, HTML, RTF offline.</p>
    
    <form id="convertForm">
        <input type="file" id="fileInput" name="file" required>
        
        <label for="outputFormat" style="display:block; text-align:left; margin-top:10px; font-weight:bold;">Convert to:</label>
        <select id="outputFormat" name="output_ext">
            <option value="pdf">PDF (Requires MS Word installed)</option>
            <option value="docx">Word (DOCX)</option>
            <option value="txt">Plain Text (TXT)</option>
            <option value="md">Markdown (MD)</option>
            <option value="html">HTML</option>
            <option value="rtf">Rich Text (RTF)</option>
        </select>
        
        <button type="submit" id="submitBtn">Convert Document</button>
    </form>
    
    <div id="status"></div>
</div>

<script>
    const form = document.getElementById('convertForm');
    const status = document.getElementById('status');
    const btn = document.getElementById('submitBtn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files.length === 0) {
            status.innerHTML = '<span class="error">Please select a file first.</span>';
            return;
        }

        status.innerHTML = '<span style="color:#f39c12;">⏳ Converting... Please wait.</span>';
        btn.disabled = true;

        const formData = new FormData(form);

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText);
            }

            // Handle the file download via JavaScript
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // Try to extract the correct filename from headers
            const disposition = response.headers.get('Content-Disposition');
            let filename = "converted_file";
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const matches = /filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            status.innerHTML = '<span class="success">✅ Success! Download starting.</span>';
        } catch (error) {
            status.innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
        } finally {
            btn.disabled = false;
        }
    });
</script>

</body>
</html>
"""

# ==========================================
# 2. Web Routes & Python Logic (Backend)
# ==========================================
@app.route('/')
def home():
    # Serve the HTML page
    return render_template_string(HTML_PAGE)

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return "No file uploaded", 400
        
    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    output_ext = request.form.get('output_ext', 'pdf').lower()
    input_ext = file.filename.split('.')[-1].lower()
    
    # ---------------------------------------------------------
    # THE FIX: Map file extensions to strict Pandoc format names
    # ---------------------------------------------------------
    input_format_map = {'txt': 'markdown', 'md': 'markdown'}
    output_format_map = {'txt': 'plain', 'md': 'markdown'}
    
    pandoc_in = input_format_map.get(input_ext, input_ext)
    pandoc_out = output_format_map.get(output_ext, output_ext)

    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_ext}") as temp_in:
            file.save(temp_in.name)
            temp_in_path = temp_in.name
            
        temp_out_path = os.path.join(tempfile.gettempdir(), f"converted_output.{output_ext}")

        # Conversion Logic
        if output_ext == 'pdf':
            if input_ext == 'docx':
                convert_to_pdf(temp_in_path, temp_out_path)
            else:
                temp_docx = os.path.join(tempfile.gettempdir(), "temp_step.docx")
                # Explicitly tell Pandoc the format to avoid "Got txt" errors
                pypandoc.convert_file(temp_in_path, 'docx', format=pandoc_in, outputfile=temp_docx)
                convert_to_pdf(temp_docx, temp_out_path)
                if os.path.exists(temp_docx):
                    os.remove(temp_docx)
        else:
            # General Conversion: Explicitly tell Pandoc both input and output formats
            pypandoc.convert_file(temp_in_path, pandoc_out, format=pandoc_in, outputfile=temp_out_path)

        # Send the file back to the browser
        final_filename = f"converted_{file.filename.rsplit('.', 1)[0]}.{output_ext}"
        
        response = send_file(temp_out_path, as_attachment=True, download_name=final_filename)
        return response

    except Exception as e:
        error_msg = str(e)
        if "com_error" in error_msg or "docx2pdf" in error_msg:
            return "PDF conversion failed. Ensure Microsoft Word is installed and closed.", 500
        return f"Conversion failed: {error_msg}", 500
    finally:
        # Cleanup temporary files just in case
        if 'temp_in_path' in locals() and os.path.exists(temp_in_path):
            os.remove(temp_in_path)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Server starting! Open this link in your browser:")
    print("👉 http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)