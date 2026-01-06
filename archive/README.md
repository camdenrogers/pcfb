# PCFB Project

This project includes a frontend built with React and a backend powered by FastAPI.

---

## 🖥️ Running the Frontend

1. Navigate to the frontend directory:

   ```bash
   cd pcfb-frontend
   ```

2. Install dependencies (if you haven't already):

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will typically be available at:  
👉 [http://localhost:5173](http://localhost:5173)

---

## ⚙️ Running the Backend

1. Navigate to the backend project directory:

   ```bash
   cd pcfb
   ```

2. Activate the Python virtual environment:

   ```bash
   source venv/bin/activate
   ```

3. Navigate to the API folder:

   ```bash
   cd api
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 🧪 Testing the Backend

Once the server is running, you can test the API using the interactive Swagger UI:

👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📝 Notes

- Make sure all dependencies are installed:

  - For the frontend: `npm install` inside `pcfb-frontend`
  - For the backend: `pip install -r requirements.txt` inside the virtual environment

- If you encounter a Bootstrap error, install it via:

  ```bash
  npm install bootstrap
  ```

  Then add this to the top of `src/main.tsx`:

  ```tsx
  import "bootstrap/dist/css/bootstrap.min.css";
  ```

---

## 📂 Project Structure

```
pcfb/
├── venv/
├── api/
│   └── main.py
└── ...

pcfb-frontend/
├── src/
│   └── main.tsx
├── package.json
└── ...
```
