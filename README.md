# ExamSolver

System RAG do analizy egzaminów maturalnych z informatyki.
Analizuje pliki PDF (również skany) przy użyciu OCR, tworzy bazę wiedzy (ChromaDB) i wykorzystuje model językowy (LLM) do generowania odpowiedzi.

## Wymagania

- Python 3.10+
- System Windows (dla Poppler i bibliotek DLL)

## Instalacja

1. Sklonuj repozytorium lub pobierz kod.
2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```
3. **Konfiguracja Poppler (OCR)**:
   - Aplikacja wymaga narzędzia `pdftoppm` z pakietu Poppler.
   - Pobierz wersję `Release-24.08.0-0` (lub nowszą, ale zachowaj strukturę katalogów) z [GitHub Poppler Windows](https://github.com/oschwartz10612/poppler-windows/releases).
   - Wypakuj i umieść zawartość tak, aby pliki wykonywalne znajdowały się w ścieżce:
     `bin/poppler/poppler-24.08.0/Library/bin`
     (względem głównego katalogu projektu).

4. **Model LLM**:
   - Pobierz model w formacie GGUF (domyślnie `Qwen2.5-7B-Instruct-Q4_K_M.gguf`).
   - Umieść plik modelu w katalogu `models/`.

## Uruchamianie

Aby uruchomić aplikację w trybie skryptu Python:

```bash
python main.py
```

## Budowanie pliku EXE

Aplikacja jest przystosowana do kompilacji przy użyciu **PyInstaller**.

1. Zainstaluj PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Uruchom polecenie budowania:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --name "ExamSolver" --add-data "models;models" --add-data "bin;bin" --hidden-import "chromadb" --hidden-import "sentence_transformers" --hidden-import "llama_cpp" --collect-all "llama_cpp" --collect-all "chromadb" main.py
   ```

   **Wyjaśnienie flag:**
   - `--onefile`: Tworzy jeden plik `.exe`.
   - `--windowed`: Ukrywa konsolę (opcjonalne, usuń jeśli chcesz widzieć logi).
   - `--add-data`: Dołącza foldery `models` i `bin` do pliku wykonywalnego.
   - `--hidden-import`: Wymusza dołączenie bibliotek, których PyInstaller może nie wykryć automatycznie.
   - `--collect-all`: Zbiera wszystkie zasoby dla kluczowych bibliotek.

3. Plik wynikowy znajdziesz w folderze `dist/ExamSolver.exe`.
