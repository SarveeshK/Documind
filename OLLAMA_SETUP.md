# How to Setup Ollama (Free Local Brain)
Since we are switching to a free local LLM, you need to run the "brain" on your own computer.

## 1. Download Ollama
1.  Go to [ollama.com](https://ollama.com).
2.  Download the **Windows** version and install it.
3.  Once installed, you should see a little llama icon in your system tray.

## 1.5 Change Download Location (Optional but Recommended)
If your C: drive is full, perform these steps **BEFORE** pulling the model:
1.  Open PowerShell as Administrator.
2.  Run this command to tell Ollama to save models in `S:\OllamaModels`:
    ```powershell
    [System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "S:\OllamaModels", "User")
    ```
3.  **Restart Ollama:**
    *   Click the `^` arrow in your Windows taskbar (bottom right).
    *   Right-click the Llama icon -> **Quit**.
    *   Open Start Menu -> Type "Ollama" -> Launch it again.
4.  Restart your terminal/VS Code for the settings to take effect.

## 2. Pull the Model
Open a **new terminal** (PowerShell or Command Prompt) and run:
```powershell
ollama pull llama3
```
*   This will download about 4.7 GB.
*   Wait for it to reach 100%.

## 3. Verify It Works
Run this command to test it:
```powershell
ollama run llama3 "Hello, are you ready?"
```
*   If it replies, you are good to go!
*   Type `/bye` to exit the chat.

## 4. Run DocuMind Retrieval
Now your Python code can talk to Ollama:
```powershell
.\.venv\Scripts\python retrieval.py
```
