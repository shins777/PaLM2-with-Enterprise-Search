FROM python:latest

WORKDIR /genai-chat

COPY . .

RUN pip install -I -r ./requirements.txt

EXPOSE 8501

CMD streamlit run /genai-chat/src/front/palm2_ui.py