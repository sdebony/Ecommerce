import requests

def fetch_dollar_rate():
    url = "https://lifche.qualities.com.ar/api/v1/dolar/"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error para códigos de respuesta HTTP 4xx/5xx
        data = response.json()  # Convierte la respuesta en formato JSON
        print("Respuesta de la API:", data)
    except requests.exceptions.RequestException as e:
        print(f"Error al hacer la solicitud: {e}")

if __name__ == "__main__":
    fetch_dollar_rate()
