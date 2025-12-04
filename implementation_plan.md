# Enforce Strict Local LLM Usage

## Goal Description
The goal is to enforce a strict "Local LLM Only" mode when `USE_LOCAL_LLM` is set to `true`. This involves:
1.  **Strict Backend Logic**: Ensure that when `USE_LOCAL_LLM` is active, NO calls are made to Gemini or Tavily. All generation and embedding must happen locally.
2.  **UI Adaptation**: Hide Gemini and Tavily configuration and usage elements in the UI when `USE_LOCAL_LLM` is active.
3.  **Availability Check**: Verify that the local LLM service (e.g., Ollama) is running. If not, display a warning dialog to the user.

## User Review Required
> [!IMPORTANT]
> This change will completely disable Gemini and Web Search features when `USE_LOCAL_LLM` is enabled. Users will not be able to use these features even if they have API keys configured.

## Proposed Changes

### Backend Services

#### [MODIFY] [ai_local_service.py](file:///home/ribben/Desktop/synapse/services/ai_local_service.py)
- Add a `check_connection()` method to `LocalLLMService` to verify connectivity (e.g., by listing models or making a dummy request).

#### [MODIFY] [rag_service.py](file:///home/ribben/Desktop/synapse/services/rag_service.py)
- Ensure `USE_LOCAL_LLM` strictly disables Gemini fallback (already largely implemented, but will verify).

### UI Components

#### [MODIFY] [settings_dialog.py](file:///home/ribben/Desktop/synapse/ui/settings_dialog.py)
- When `USE_LOCAL_LLM` is toggled ON:
    - Hide Gemini API Key section.
    - Hide Tavily API Key section.
- When `USE_LOCAL_LLM` is toggled OFF:
    - Show Gemini and Tavily sections.

#### [MODIFY] [subject_window.py](file:///home/ribben/Desktop/synapse/ui/subject_window.py)
- In `create_web_search_option`:
    - Check `USE_LOCAL_LLM`. If true, hide the entire web search frame or disable it with a tooltip explaining why.
- In `generate_flashcards`:
    - If `USE_LOCAL_LLM` is true:
        - Initialize `LocalLLMService`.
        - Call `check_connection()`.
        - If check fails, show `QMessageBox.warning` and return.

## Verification Plan

### Manual Verification
1.  **Enable Local LLM**:
    - Open Settings.
    - Toggle "Use Local LLM" to ON.
    - Verify Gemini and Tavily sections disappear.
    - Save and close.
2.  **Check UI**:
    - Open a Subject.
    - Verify "Web Search" option is hidden or disabled in the Generate tab.
3.  **Test Availability Check (Negative Case)**:
    - Stop the local LLM service (e.g., ensure no Ollama/LM Studio is running).
    - Click "Generate Flashcards".
    - Verify a warning dialog appears saying Local LLM is not running.
4.  **Test Availability Check (Positive Case)**:
    - Start the local LLM service (e.g., `ollama serve`).
    - Click "Generate Flashcards".
    - Verify generation proceeds using the local model.
