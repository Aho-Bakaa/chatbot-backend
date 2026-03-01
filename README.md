# Chatbot  🤖

Welcome to the repository for my first-ever chatbot! This project represents a complete, full-stack implementation of a conversational interface, built from scratch. It features a robust Python backend and a lightweight, highly customizable vanilla web frontend designed to be easily injected into any existing website.

## 🚀 Overview

This project provides a deployable chatbot solution with a clean separation of concerns. The backend handles message processing and routing, while the frontend provides a sleek, responsive widget for user interaction. By utilizing Docker, the entire application can be spun up quickly in an isolated, consistent environment.

## 📁 Repository Structure

* **`chatbot.py`**: The core Python backend server responsible for handling chat logic, processing inputs, and returning responses.
* **`inject_bot.py`**: A utility script used to dynamically inject the chatbot UI into external web pages.
* **`chatbot.html`**: The structural markup for the chat widget.
* **`chatbot.css`**: The styling rules ensuring a modern, responsive, and user-friendly interface.
* **`chatbot.js`**: The vanilla JavaScript handling client-side interactions, API calls to the backend, and dynamic DOM updates.
* **`requirements.txt`**: The list of Python dependencies required to run the backend.
* **`Dockerfile`**: Container configuration to easily build and deploy the application via Docker.

## 🛠️ Technologies Used

* **Backend:** Python
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Containerization:** Docker

## ⚙️ Getting Started

### Prerequisites
* [Python 3.x](https://www.python.org/downloads/)
* [Docker](https://www.docker.com/) (Optional, but recommended for deployment)

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Aho-Bakaa/chatbot-backend.git](https://github.com/Aho-Bakaa/chatbot-backend.git)
   cd chatbot-backend
Install dependencies:
It is recommended to use a virtual environment.

Bash
pip install -r requirements.txt
Run the backend:

Bash
python chatbot.py
Launch the frontend:
Open chatbot.html in your web browser, or use the inject_bot.py script to embed the widget into a local test site.

Docker Deployment
To build and run the chatbot using Docker:

Build the image:

Bash
docker build -t chatbot-backend .
Run the container:

Bash
docker run -p 8080:8080 chatbot-backend
(Note: Adjust the port mapping based on the actual port configured in chatbot.py or your Dockerfile)

💡 Future Enhancements
As my first foray into chatbot development, this project sets the stage for future improvements such as integrating advanced Large Language Models (LLMs), adding multi-agent orchestration, and deploying scalable endpoints on cloud platforms.

👨‍💻 Author
Anmol Kumar Srivastav


*** Feel free to adjust the port numbers in the Docker section to match the specific port your application is listening on!
