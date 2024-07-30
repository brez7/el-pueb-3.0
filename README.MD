docker build -t gcr.io/upbeat-button-265722/cateringapp .

docker push gcr.io/upbeat-button-265722/cateringapp


gcloud run deploy cateringapp `
    --image gcr.io/upbeat-button-265722/cateringapp `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --port 8080









docker run -p 8080:8080 cateringapp

gcloud auth login

gcloud config set project upbeat-button-265722
