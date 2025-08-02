# 🧠 Custom-Python-Socket-Server

A HTTP server built with Python sockets that supports static file serving, URL-based arithmetic operations, file uploads/downloads, redirection handling, and basic request validation — without relying on external web frameworks.

---

## ✨ Features

- 🗂 Serves static files (HTML, CSS, JS, images)
- ⬆️ File upload and ⬇️ download via POST requests
- 🔁 URL redirection handling
- 🚫 Forbidden resource protection
- 🧮 Built-in math operations:
  - `/calculate-next?num=5` → returns 6
  - `/calculate-area?height=4&width=10` → returns 20
- 📄 Custom 404 and 403 error handling
- 📦 Organized file storage with `uploads/` and `webroot/` folders

---

## 🚀 Getting Started

1. Clone the repository
2. Place your static files in `webroot/`
3. Run the server: ```python server.py```
4. Open a browser and go to ```http://127.0.0.1:8080```

## ⚠️ Disclaimer
Template Credit: Barak Gonen, Cyber Education Center.
Modified and extended for instructional purposes.
