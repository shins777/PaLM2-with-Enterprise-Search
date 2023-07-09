FROM python:latest

WORKDIR /genai

COPY . .

RUN pip install -I -r ./requirements.txt

EXPOSE 8501

CMD streamlit run /genai/src/front/palm2_ui.py