from flask import Flask, render_template, request
import os
from ntfs_recover import recover_files_from_ntfs  # Import your recovery function
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder where recovered files will be temporarily stored
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recover_files', methods=['POST'])
def recover_files():
    if 'ntfs_image_file' not in request.files:
        return 'No NTFS image file provided!', 400

    ntfs_image_file = request.files['ntfs_image_file']
    if ntfs_image_file.filename == '':
        return 'No selected NTFS image file!', 400

    save_folder = request.form.get('save_folder')
    if not save_folder:
        return 'No save folder selected!', 400

    # Save the NTFS image file
    filename = secure_filename(ntfs_image_file.filename)
    ntfs_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    ntfs_image_file.save(ntfs_image_path)

    try:
        # Call the recovery function
        det = recover_files_from_ntfs(ntfs_image_path, save_folder, recover_deleted=False)
    except Exception as e:
        return f"Error during file recovery: {str(e)}", 500

    return {
        "message": "File recovery completed successfully!",
        "files_recovered": det["total"],  # Example response, you can send back actual counts
        "files_skipped": det["skip"],
        "errors": det["error"]
    }

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
