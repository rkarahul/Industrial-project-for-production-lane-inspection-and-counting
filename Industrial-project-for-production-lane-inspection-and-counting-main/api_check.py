import requests
import base64


# Define the URL for the prediction endpoint
url = 'http://localhost:5000/predict'

# Read the image file and encode it to base64
with open(r'ng_image.jpg', 'rb') as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

# Create the JSON payload with the base64 encoded image
payload = {
    'image': image_base64
}

# Send the POST request with the JSON payload
response = requests.post(url, json=payload)

# Print the response
print(response.json())
