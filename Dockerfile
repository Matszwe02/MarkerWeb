FROM python:3.10-bookworm

RUN apt update && apt upgrade -y
# RUN apt install libgl1 -y

RUN apt install python3-pip pipx git -y
RUN apt autoremove -y
RUN apt autoclean -y
# RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -

WORKDIR /app
# RUN git clone https://github.com/VikParuchuri/marker
# RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
RUN pip install flask werkzeug marker-pdf
RUN apt install libgl1 -y
RUN pip install --no-cache-dir gunicorn
RUN pip install flask_socketio

RUN python -c "from transformers import pipeline; pipe = pipeline('sentiment-analysis'); pipe('This is an example.')"


# Copy the pre-download script
COPY download_models.py .

# Download the models during image build
RUN python download_models.py


COPY . .
# WORKDIR /usr/src/marker 
# RUN poetry env use $(which python3)
# RUN poetry install --verbose -v
# RUN pip install marker-pdf

# RUN pip install streamlit

# Define environment variable
ENV FLASK_APP=main.py

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "--workers", "1", "main:app"]
