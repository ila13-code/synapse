# Round Robin API Key Implementation Plan

## Goal Description
Implement a round-robin mechanism for Gemini API keys in the Synapse application to distribute valid requests across multiple keys and avoid hitting rate limits. This mimics the logic present in the user's `generate_mocks` script.

## User Review Required
> [!IMPORTANT]
> The `AIService` will be modified to accept a list of API keys. The application will now look for `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc., in the `.env` file, in addition to the standard `GEMINI_API_KEY`.

## Proposed Changes

### [Services]

#### [MODIFY] [ai_service.py](file:///home/ribben/Desktop/synapse/services/ai_service.py)
- Update `__init__` to accept `api_keys` (list of strings) or a single `api_key`.
- Implement a key rotation mechanism.
- If multiple keys are provided, `_call_api` (and other generation methods) will cycle through the keys for each request.
- To avoid overhead, we can either instantiate `genai.Client` on the fly or keep a pool of clients. Given the usage, re-instantiating or maintaining a small pool is acceptable. simpler is rotating the key passed to a helper or updating the client. `genai.Client` object seems to hold the key.
- We will use a simple round-robin strategy (Request 1 -> Key 1, Request 2 -> Key 2, etc.).

### [UI]

#### [MODIFY] [subject_window.py](file:///home/ribben/Desktop/synapse/ui/subject_window.py)
- In `generate_flashcards`:
    - Retrieve all available `GEMINI_API_KEY_n` variables from the environment.
    - If `GEMINI_API_KEY` is present, include it as well (or treat it as a fallback/primary).
    - Pass the list of collected keys to the `AIService` constructor.

## Verification Plan

### Automated Tests
- There are no existing unit tests for `AIService` visible in the file list (no `tests/` directory shown in root, but I can check).
- I will verify by running the application and checking logs.

### Manual Verification
1.  **Configure Environment**: Add `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2` to `.env` (using dummy or valid keys if available, or just duplicating the existing valid key to test rotation mechanics).
2.  **Run Application**: Start `main.py`.
3.  **Generate Flashcards**: Go to a subject, click "Generate", and watch the logs (I will add print logs indicating which key is being used).
4.  **Verify Rotation**: Confirm that consecutive requests use different keys (or the same key if only one is provided).
