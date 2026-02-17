# ExamSolver

System RAG (Retrieval-Augmented Generation) do analizy egzaminów maturalnych z informatyki.
Aplikacja analizuje pliki PDF (również skany) przy użyciu OCR, tworzy bazę wiedzy (ChromaDB) i wykorzystuje model językowy (LLM) do generowania odpowiedzi oraz wyszukiwania podobnych zadań.

## 📂 Opis plików w projekcie

Poniżej znajduje się opis najważniejszych plików i skryptów wchodzących w skład projektu:

### Główne komponenty
- **`main.py`**: Serce systemu. Zawiera klasę `EgzaminAnalyzer`, która odpowiada za:
  - Inicjalizację modeli AI (LLM, Embeddings).
  - Obsługę bazy danych wektorowych (ChromaDB).
  - Przetwarzanie plików PDF (wyciąganie tekstu, OCR).
  - Logikę RAG (wyszukiwanie kontekstu i generowanie odpowiedzi).
- **`egzamin_cli.py`**: Interfejs użytkownika w wierszu poleceń (Command Line Interface). Pozwala na interaktywną pracę z asystentem – wklejanie treści zadań i otrzymywanie rozwiązań.

### Narzędzia administracyjne
- **`import_podreczniki.py`**: Skrypt służący do zasilania `baza_wiedzy`. Skanuje folder `podreczniki/` (musisz go utworzyć), dzieli znalezione PDF-y na fragmenty i dodaje je do indeksu, aby AI mogło korzystać z tej wiedzy.
- **`dodaj_egzaminy.py`**: Automatyzuje proces dodawania arkuszy maturalnych do `baza_egzaminow`. Skrypt szuka par plików (arkusz pytań + arkusz odpowiedzi) i wprowadza je do bazy, umożliwiając późniejsze wyszukiwanie podobnych zadań.
- **`check_db_stats.py`**: Proste narzędzie diagnostyczne. Wyświetla statystyki bazy danych: liczbę zaindeksowanych dokumentów, dostępne roczniki egzaminów oraz przedmioty.
- **`inspect_tasks.py`**: Pozwala zajrzeć do wnętrza bazy danych. Wyświetla próbki zaindeksowanych zadań, co pomaga zweryfikować, czy import przebiegł poprawnie (np. czy OCR dobrze odczytał tekst).
- **`przyklady_uzycia.py`**: Zbiór przykładowych funkcji pokazujących, jak używać biblioteki `main.py` programistycznie. Zawiera gotowe snippety kodu do wyszukiwania, generowania odpowiedzi czy eksportu danych.

### Bazy danych
- **`baza_wiedzy/`**: Folder zawierający bazę SQLite i indeksy ChromaDB z wiedzą ogólną (np. z podręczników).
- **`baza_egzaminow/`**: Folder zawierający bazę SQLite i indeksy ChromaDB z treścią zadań egzaminacyjnych.

---

## 🚀 Jak używać?

### 1. Instalacja i Konfiguracja

1.  **Pobierz repozytorium**:
    ```bash
    git clone https://github.com/WiczoData/examsolver.git
    cd examsolver
    ```

2.  **Zainstaluj zależności**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Skonfiguruj Poppler (Wymagane do OCR)**:
    - Pobierz [Poppler dla Windows](https://github.com/oschwartz10612/poppler-windows/releases).
    - Wypakuj zawartość tak, aby pliki wykonywalne (np. `pdftoppm.exe`) znajdowały się w ścieżce:
      `bin/poppler/poppler-24.08.0/Library/bin` (względem głównego katalogu projektu).

4.  **Pobierz Model LLM**:
    - Pobierz model w formacie `.gguf` (np. `Qwen2.5-7B-Instruct-Q4_K_M.gguf`).
    - Umieść go w folderze `models/`.

### 2. Uruchomienie Asystenta (CLI)

Aby rozpocząć pracę z asystentem w trybie tekstowym:

```bash
python egzamin_cli.py
```
Program załaduje model i pozwoli Ci wpisywać pytania lub wklejać treść zadań.

### 3. Zarządzanie Bazą Wiedzy

**Dodawanie podręczników:**
1. Stwórz folder `podreczniki` w katalogu nadrzędnym (lub edytuj ścieżkę w skrypcie).
2. Wrzuć tam pliki PDF.
3. Uruchom:
   ```bash
   python import_podreczniki.py
   ```

**Dodawanie egzaminów:**
1. Przygotuj pliki PDF w formacie `nazwa.pdf` (pytania) i `nazwa-odpowiedzi.pdf` (klucz).
2. Uruchom skrypt (może wymagać edycji ścieżki do folderu z plikami):
   ```bash
   python dodaj_egzaminy.py
   ```

**Sprawdzanie stanu bazy:**
```bash
python check_db_stats.py
```

---

## 🛠️ Budowanie pliku EXE

Możesz zbudować samodzielną aplikację `.exe`, która nie wymaga instalowania Pythona na innym komputerze.

1.  Zainstaluj PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Uruchom komendę budowania:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "ExamSolver" --add-data "models;models" --add-data "bin;bin" --hidden-import "chromadb" --hidden-import "sentence_transformers" --hidden-import "llama_cpp" --collect-all "llama_cpp" --collect-all "chromadb" main.py
    ```
    *Uwaga: Budowanie z flagą `--onefile` może trwać kilka minut, a plik wynikowy będzie duży ze względu na dołączone modele.*

3.  Gotowy plik znajdziesz w folderze `dist/`.
