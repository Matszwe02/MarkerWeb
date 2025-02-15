from flask import Flask, render_template, request, send_file
import os
from werkzeug.utils import secure_filename
from threading import Thread
import subprocess
import shlex
import io
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
import shutil



# os.environ['TORCH_DEVICE'] = 'cuda'

# output_format = os.environ.get('FORMAT', 'markdown')

app = Flask(__name__)

UPLOAD_FOLDER = './temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB limit


extensions = {"markdown" : "md"}

config = {
    "output_format": 'markdown',  # Default, but explicit
    "force_ocr": True,
    "cleanup_ocr": True,
}
config_parser = ConfigParser(config)

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer()
)

shutil.rmtree(app.config['UPLOAD_FOLDER'])
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



def exec_marker(filename: str, config: dict):
    
    config_parser = ConfigParser(config)

    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer()
    )
    
    rendered = converter(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    text, _, images = text_from_rendered(rendered)
    
    shutil.rmtree(app.config['UPLOAD_FOLDER'])
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename.replace('.', '_')) + "." + extensions.get(config['output_format'], config['output_format']), 'w') as f:
        f.write(text)



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        
        if 'file' not in request.files:
            return render_template('index.html', message='No file part')
        file = request.files['file']
        
        if file.filename == '':
            return render_template('index.html', message='No selected file')
        
        if file and file.filename.endswith('.pdf'):
            try:
                shutil.rmtree(app.config['UPLOAD_FOLDER'])
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            except:
                return ('Server is busy', 500)
            
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            config = {
                "output_format": request.form.get('output_format'),
                "force_ocr": request.form.get('force_ocr') == 'on',
                "strip_existing_ocr": request.form.get('strip_existing_ocr') == 'on',
                "paginate_output": request.form.get('paginate_output') == 'on',
                "disable_image_extraction": request.form.get('disable_image_extraction') == 'on',
                "page_range": request.form.get('page_range'),
                "languages": request.form.get('languages'),
                "converter_cls": request.form.get('converter_cls'),
            }
            
            print(config)

            Thread(target=lambda: exec_marker(filename, config)).start()

            return render_template('index.html', message='File uploaded successfully', download_link=f'/download/{filename}')

    return render_template('index.html', message='')



@app.route('/download/<filename>')
def download_file(filename):
    # file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file = os.listdir(app.config['UPLOAD_FOLDER'])[0]
    if filename.replace('.', '_') + '.' in file:
        print(f"sending file {os.path.join(app.config['UPLOAD_FOLDER'], file)}")
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], file), as_attachment=True)
    return ('', 404)



if __name__ == '__main__':
    app.run(debug=True)
