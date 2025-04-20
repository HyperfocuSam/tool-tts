# 長錄音轉錄稿生成器 - 本地端安裝與執行指南 (繁體中文)

本指南將引導您如何在自己的電腦上設定並執行「長錄音轉錄稿生成器」應用程式。

## 系統需求與事前準備

在開始之前，請確保您的電腦已安裝以下軟體：

1.  **Python**:
    *   需要 Python 3.8 或更新版本。
    *   您可以從 Python 官方網站下載並安裝：[https://www.python.org/downloads/](https://www.python.org/downloads/)
    *   安裝時，請**務必勾選**類似「Add Python to PATH」或「將 Python 加入環境變數」的選項，這會讓後續步驟更方便。
    *   安裝完成後，可以在終端機（命令提示字元或 PowerShell）輸入 `python --version` 來確認是否安裝成功及版本號。

2.  **ffmpeg**:
    *   `ffmpeg` 是一個處理音訊和視訊檔案的必要工具。
    *   **Windows**:
        *   前往 [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) 或 [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) 下載適用於 Windows 的版本（通常是 `ffmpeg-release-full.7z` 或類似名稱）。
        *   解壓縮下載的檔案。
        *   將解壓縮後資料夾內的 `bin` 資料夾路徑（例如 `C:\ffmpeg\bin`）加入到您系統的**環境變數 `Path`** 中。您可以搜尋「編輯系統環境變數」來找到設定位置。加入後需要重新開啟終端機才會生效。
    *   **macOS**:
        *   如果您使用 [Homebrew](https://brew.sh/)，可以在終端機執行：`brew install ffmpeg`
    *   **Linux (Debian/Ubuntu)**:
        *   可以在終端機執行：`sudo apt update && sudo apt install ffmpeg`
    *   安裝完成後，可以在終端機輸入 `ffmpeg -version` 來確認是否安裝成功。

3.  **Gemini API 金鑰**:
    *   本應用程式需要使用 Google Gemini API 進行轉錄。您需要擁有一個有效的 API 金鑰。
    *   您可以從 Google AI Studio 或 Google Cloud Console 取得。
    *   請妥善保管您的 API 金鑰，不要分享給他人。

## 安裝步驟

1.  **取得應用程式碼**:
    *   從提供者（您的朋友）那裡取得包含所有應用程式檔案的 `stt_webapp` 資料夾。
    *   或者，如果您熟悉 Git，可以從 GitHub 儲存庫下載或 clone：
        ```bash
        git clone https://github.com/HyperfocuSam/tool-tts.git
        cd tool-tts
        # 注意：儲存庫名稱可能不同，請使用實際的儲存庫 URL
        ```
    *   將 `stt_webapp` 資料夾放置在您電腦上方便存取的位置（例如桌面、文件資料夾等）。

2.  **開啟終端機**:
    *   **Windows**: 按下 `Win + R`，輸入 `cmd` 或 `powershell`，然後按 Enter。
    *   **macOS**: 開啟「應用程式」->「工具程式」->「終端機」。
    *   **Linux**: 通常可以在應用程式選單中找到「終端機」。

3.  **進入應用程式目錄**:
    *   在終端機中使用 `cd` 指令切換到您放置 `stt_webapp` 資料夾的路徑。例如：
        ```bash
        cd C:\Users\您的使用者名稱\Desktop\stt_webapp
        # 或
        cd /Users/您的使用者名稱/Desktop/stt_webapp
        ```
    *   請將上面的路徑替換為您實際存放資料夾的路徑。

4.  **建立並啟用虛擬環境 (建議)**:
    *   在 `stt_webapp` 目錄下執行以下指令來建立一個名為 `venv` 的虛擬環境：
        ```bash
        python -m venv venv
        ```
    *   啟用虛擬環境：
        *   **Windows (cmd.exe)**: `venv\Scripts\activate.bat`
        *   **Windows (PowerShell)**: `venv\Scripts\Activate.ps1` (如果遇到執行原則問題，可能需要先執行 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)
        *   **macOS/Linux**: `source venv/bin/activate`
    *   啟用成功後，您應該會在終端機提示符號前看到 `(venv)` 字樣。

5.  **安裝必要的 Python 套件**:
    *   確保您仍在 `stt_webapp` 目錄下且虛擬環境已啟用。
    *   執行以下指令來安裝 `requirements.txt` 檔案中列出的所有套件：
        ```bash
        pip install -r requirements.txt
        ```
    *   安裝過程可能需要一些時間。

6.  **設定 API 金鑰環境變數**:
    *   應用程式需要透過名為 `GEMINI_API_KEY` 的環境變數讀取您的 API 金鑰。設定方法依作業系統而異：
        *   **Windows (目前終端機)**:
            ```powershell
            # PowerShell
            $env:GEMINI_API_KEY = "貼上您的API金鑰於此"

            # CMD
            set GEMINI_API_KEY=貼上您的API金鑰於此
            ```
            *(注意：此方法只在目前的終端機視窗有效，關閉後需重新設定)*
        *   **Windows (永久設定)**:
            *   搜尋「編輯系統環境變數」。
            *   點擊「環境變數...」按鈕。
            *   在「使用者變數」或「系統變數」區域點擊「新增...」。
            *   變數名稱輸入 `GEMINI_API_KEY`。
            *   變數值貼上您的 API 金鑰。
            *   點擊確定。設定後需要重新開啟終端機才會生效。
        *   **macOS/Linux**:
            ```bash
            export GEMINI_API_KEY="貼上您的API金鑰於此"
            ```
            *(注意：此方法只在目前的終端機視窗有效。若要永久設定，需將此行加入您的 shell 設定檔，如 `.bashrc`, `.zshrc` 或 `.profile`，然後執行 `source ~/.bashrc` 或重新開啟終端機)*

## 執行應用程式

1.  **啟動伺服器**:
    *   確保您仍在 `stt_webapp` 目錄下，且虛擬環境已啟用，並且已設定好 `GEMINI_API_KEY` 環境變數。
    *   執行以下指令來啟動應用程式：
        ```bash
        python main.py
        ```
    *   您應該會看到類似以下的輸出訊息，表示伺服器已成功啟動：
        ```
        Starting Uvicorn server for local testing on http://127.0.0.1:8000
        Access the upload interface at http://127.0.0.1:8000/
        ...
        ```

2.  **開啟網頁介面**:
    *   打開您的網頁瀏覽器（如 Chrome, Firefox, Edge 等）。
    *   在網址列輸入：`http://127.0.0.1:8000` 或 `http://localhost:8000`
    *   按下 Enter，您應該就能看到應用程式的操作介面。

## 使用應用程式

應用程式的使用方式與線上版本相同：

1.  點擊「選擇音訊或視訊檔案」來選擇檔案。
2.  點擊「開始轉錄」按鈕。
3.  等待處理完成（會顯示載入指示器）。
4.  在下方的「轉錄結果」區域查看或複製文字稿。

詳細的操作說明可以參考 `USER_GUIDE_zh_Hant.md` 文件。

## 停止應用程式

*   回到您執行 `python main.py` 的終端機視窗。
*   按下 `Ctrl + C` 組合鍵即可停止伺服器。

## 疑難排解

*   **`python` 或 `pip` 指令找不到**：通常是因為 Python 沒有正確加入到系統 PATH 環境變數。請重新安裝 Python 並確保勾選相關選項，或手動將 Python 安裝路徑加入 PATH。
*   **`ffmpeg` 相關錯誤** (例如 `FileNotFoundError` 或 `pydub` 錯誤)：確認 `ffmpeg` 已正確安裝，並且其 `bin` 資料夾路徑已加入系統 PATH 環境變數。重新開啟終端機後再試一次。
*   **`GEMINI_API_KEY` 相關錯誤**：確認環境變數名稱完全正確 (`GEMINI_API_KEY`)，並且其值是您有效的 API 金鑰。如果是臨時設定，請確保在執行 `python main.py` 的同一個終端機視窗中設定。
*   **記憶體不足 (Out of Memory)**：如果您的電腦記憶體較少，處理非常大的檔案時可能會遇到問題。嘗試處理較小的檔案，或關閉其他耗用記憶體的程式。

希望本指南能幫助您順利在本地端執行此應用程式！
