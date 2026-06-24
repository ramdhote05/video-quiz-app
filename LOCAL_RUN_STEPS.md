# Local Run Steps

Use these steps whenever you want to run this project on your own computer.

## 1. Open the Project Folder

Open PowerShell or Command Prompt inside this folder:

```txt
C:\Users\ROG\Downloads\quiz app\video-quiz-app
```

If you are not already inside the folder, run:

```powershell
cd "C:\Users\ROG\Downloads\quiz app\video-quiz-app"
```

## 2. Activate the Virtual Environment

Run:

```powershell
.\.venv\Scripts\activate
```

After activation, your terminal should show something like:

```txt
(.venv)
```

## 3. Run the Local Server

Recommended command:

```powershell
python run_server.py
```

Alternative command:

```powershell
python app.py
```

The server will start on:

```txt
http://127.0.0.1:5000/
```

## 4. Open the App in Browser

Open this link:

```txt
http://127.0.0.1:5000/
```

You can upload a video from there.

## 5. Stop the Server

Go back to the terminal and press:

```txt
Ctrl + C
```

## 6. If Dependencies Are Missing

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

## 7. Important Notes

- FFmpeg must be installed and available in PATH for video audio extraction.
- Add your Groq API key in `.env` if you want cloud transcription and better AI summaries/quizzes.
- Do not share your `.env` file publicly.
- If the server is already running, opening `http://127.0.0.1:5000/` should show the app directly.

## Quick Command Summary

```powershell
cd "C:\Users\ROG\Downloads\quiz app\video-quiz-app"
.\.venv\Scripts\activate
python run_server.py
```

Then open:

```txt
http://127.0.0.1:5000/
```
