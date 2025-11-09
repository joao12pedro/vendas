
from supabase import create_client

url = "https://egbysxvrncockarbpsdz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVnYnlzeHZybmNvY2thcmJwc2R6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MzY0MjIsImV4cCI6MjA2MDMxMjQyMn0.V48P_us2UQj3IeMYP4scZ29la0hLMa-p1m9b1v0VEEA"

# Conexão com o banco de dados
def connect_db():
    return  create_client(url, key)