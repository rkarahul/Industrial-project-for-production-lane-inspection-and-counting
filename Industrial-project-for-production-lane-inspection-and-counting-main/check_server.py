# server check for server error using get method at end point /ServerCheck
import requests

url = 'http://127.0.0.1:5000/ServerCheck'

response = requests.get(url)

if response.status_code == 200:
    print(" Response from server is :")
    print(response.json())
else :
    print(" Server not Running: " + response.status_code,'\n Please check server for server error using get method at end point /ServerCheck')
    
