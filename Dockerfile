FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bundle pre-fetched data so the container does not call CMS on every cold start.
# Refresh locally with: python data_ingestion.py --refresh
RUN test -f data/facilities.csv || python data_ingestion.py --refresh

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]