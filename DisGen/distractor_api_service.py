import os

from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename

import pandas as pd

import distractor_generator

INPUT_FOLDER = 'distractor_service_input_files'
OUTPUT_FOLDER = 'distractor_service_output_files'

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_extension(file):
    if file.filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS:
        return True
    return False

app = Flask(__name__, template_folder='distractor_service_templates')
app.config['UPLOAD_FOLDER'] = INPUT_FOLDER

## GUI For Excel i/o
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if 'contextsFile' in request.files:
            file = request.files['contextsFile']
            if file and allowed_extension(file):
                inp_filepath = os.path.join(INPUT_FOLDER, secure_filename(file.filename))
                out_filepath = os.path.join(OUTPUT_FOLDER, secure_filename(file.filename))
                file.save(inp_filepath)

                df = pd.read_excel(inp_filepath, index_col='id')
                df = distractor_generator.get_distractors(df)
                df.to_excel(out_filepath)

                attachment_name = file.filename.rsplit('.',1)[0]+'_with_distractors.xlsx'
                return send_file(out_filepath, as_attachment=True,attachment_filename=attachment_name)
                
    return render_template('index.html')

## API for JSON i/o
@app.route('/api', methods=['POST'])
def service():
    if request.method == 'POST':
        if 'contexts' in request.form:
            df = pd.DataFrame(request.form['contexts']).set_index('id')
            df = distractor_generator.get_distractors(df)
            return df.to_json(orient='records')

if __name__ == '__main__':
    app.run()