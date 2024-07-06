import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
import random
import json
import os
import io
from PIL import Image, ImageTk
import warnings

warnings.filterwarnings("ignore")

# Global variable to store generated dummy array
generated_dummy_array = None

def on_exit():
    if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit?"):
        root.quit()

# Function to open file dialog and select an image
def select_image():
    global image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if image_path:
        file_name = os.path.basename(image_path)
        file_extension = os.path.splitext(file_name)[1]
        image_label.configure(text=f"Selected Image: {file_name}\tType: {file_extension}")
        show_image(image_path, input_image_label)

def show_image(image_path, label):
    img = Image.open(image_path)
    img = img.resize((350, 350), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    label.configure(image=img_tk)
    label.image = img_tk

# Function to check server status
def check_server():
    try:
        url = 'http://127.0.0.1:5000/ServerCheck'
        response = requests.get(url)

        if response.status_code == 200:
            server_response = response.json()
            if 'message' in server_response:
                server_message = server_response['message']
                messagebox.showinfo("Server Status", "Message from server: " + server_message)
            else:
                messagebox.showerror("Response Error", "The 'message' key was not found in the response.")
        else:
            messagebox.showerror("Server Error", f"Failed to get response. Status code: {response.status_code}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Function to send image and data to server
def send_data():
    try:
        
        # Read the image file and encode it to base64
        with open(image_path, 'rb') as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        threshold_val = int(threshold_entry.get())
        user_message = message_entry.get()
        
        
        # Create the JSON payload with the base64 encoded image and dummy_array
        payload = {
            'image': image_base64,
            'threshold_val': threshold_val,
            
            'user_message': user_message
        }

        # Define the URL for the prediction endpoint
        url = 'http://127.0.0.1:5000/predict'

        # Send the POST request with the JSON payload
        response = requests.post(url, json=payload)

        # Process response
        if response.status_code == 200:
            # Receive annotated image base64 from backend
            response_data = response.json()
            annotated_image_base64 = response_data['image']
        
            # Decode base64 to image and display in output_image_label
            img_data = base64.b64decode(annotated_image_base64)
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((350, 350), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            output_image_label.configure(image=img_tk)
            output_image_label.image = img_tk 
            
            # Extract threshold_val from response data and display server_threshold_val
            threshold_val = response_data['threshold_val']
            server_threshold_val_label.configure(text=f"{threshold_val}")
            
            
            # Extract user_message from response data and display server_user_message
            server_user_message = response_data['user_message']
            server_user_message_label.configure(text=f"{server_user_message}")

        else:
            messagebox.showerror("Server Error", f"Failed to get response. Status code: {response.status_code}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# Create the main window
root = ctk.CTk()
root.title("Image Prediction Sender")
wdth = root.winfo_screenwidth()
hgt = root.winfo_screenheight()
root.geometry("%dx%d" % (wdth, hgt))

placeholder_image = tk.PhotoImage(width=200, height=200)

# Create a frame for the controls on the left side
left_frame = ctk.CTkFrame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Create a frame for the images on the right side
right_frame = ctk.CTkFrame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Controls section in the left frame
# Image selection
image_label = ctk.CTkLabel(left_frame, text="Select an image", text_color="green", font=("Helvetica", 22))
image_label.pack(pady=10)

select_button = ctk.CTkButton(left_frame, text="Browse", hover_color="green", command=select_image)
select_button.pack(pady=10)

# Threshold value input
threshold_label = ctk.CTkLabel(left_frame, text="Threshold Value", text_color="green", font=("Helvetica", 22))
threshold_label.pack(pady=10)
threshold_entry = ctk.CTkEntry(left_frame)
threshold_entry.pack(pady=10)

# User message input
message_label = ctk.CTkLabel(left_frame, text="User Message", text_color="green", font=("Helvetica", 22))
message_label.pack(pady=10)
message_entry = ctk.CTkEntry(left_frame)
message_entry.pack(pady=10)

# Server check button
server_check_button = ctk.CTkButton(left_frame, text="Check Server", hover_color="green", command=check_server)
server_check_button.pack(pady=20)

# Send button
send_button = ctk.CTkButton(left_frame, text="Send Data", hover_color="green", command=send_data)
send_button.pack(pady=20)

# Input image label
input_text = ctk.CTkLabel(master=left_frame, text="Input image", text_color="green", font=("Helvetica", 22))
input_text.place(relx=0.5, rely=0.55, anchor=ctk.CENTER)

input_image_label = ctk.CTkLabel(master=left_frame, text=" ", image=placeholder_image, anchor="nw")
input_image_label.pack(padx=0.25, pady=0.4)

# Output image label
output_text = ctk.CTkLabel(master=right_frame, text="Output image", text_color="red", font=("Helvetica", 22))
output_text.place(relx=0.45, rely=0.02)

output_image_label = ctk.CTkLabel(master=right_frame, text=" ", anchor="center")
output_image_label.place(relx=0.5, rely=0.25, anchor=ctk.CENTER)

# Display server threshold value
server_threshold_val_text = ctk.CTkLabel(master=right_frame, text="Threshold_val from server:", text_color="green", font=("Helvetica", 22))
server_threshold_val_text.place(relx=0.5, rely=0.6, anchor=ctk.CENTER)

server_threshold_val_frame = ctk.CTkFrame(master=right_frame, width=200, height=50, border_width=4, border_color="cyan", corner_radius=6)
server_threshold_val_frame.place(relx=0.5, rely=0.65, anchor=ctk.CENTER)

server_threshold_val_label = ctk.CTkLabel(master=right_frame, text="", text_color="blue", font=("Helvetica", 22))
server_threshold_val_label.place(relx=0.5, rely=0.65, anchor=ctk.CENTER)

# Display server user message
server_user_message_text = ctk.CTkLabel(master=right_frame, text="User message from server:", text_color="green", font=("Helvetica", 22))
server_user_message_text.place(relx=0.5, rely=0.79, anchor=ctk.CENTER)

server_user_message_frame = ctk.CTkFrame(master=right_frame, width=500, height=50, border_width=4, border_color="cyan", corner_radius=6)
server_user_message_frame.place(relx=0.5, rely=0.83, anchor=ctk.CENTER)

server_user_message_label = ctk.CTkLabel(master=right_frame, text="", text_color="blue", font=("Helvetica", 22))
server_user_message_label.place(relx=0.5, rely=0.83, anchor=ctk.CENTER)

exit_button = ctk.CTkButton(master=root, text="Exit", hover_color="red", command=on_exit)
exit_button.place(relx=0.9, rely=0.95, anchor=ctk.CENTER)

# Bind the window close event to the custom on_exit handler
root.protocol("WM_DELETE_WINDOW", on_exit)

# Start the GUI event loop
root.mainloop()

