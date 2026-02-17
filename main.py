import re
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent
BASE_DIR = get_base_dir()
if getattr(sys, 'frozen', False):
    bundle_dir = Path(getattr(sys, '_MEIPASS', BASE_DIR))
    possible_lib_paths = [bundle_dir / 'llama_cpp' / 'lib', bundle_dir / '_internal' / 'llama_cpp' / 'lib', BASE_DIR / 'llama_cpp' / 'lib']
    for lib_path in possible_lib_paths:
        if lib_path.exists():
            os.environ['PATH'] = str(lib_path) + os.pathsep + os.environ.get('PATH', '')
            try:
                os.add_dll_directory(str(lib_path))
            except Exception:
                pass
            break
if sys.version_info >= (3, 13):
    try:
        import pydantic.v1.fields as pydantic_fields
        import typing
        original_infer = pydantic_fields.ModelField.infer

        @classmethod
        def patched_infer(cls, *args, **kwargs):
            try:
                return original_infer(*args, **kwargs)
            except Exception:
                if 'annotation' in kwargs:
                    kwargs['annotation'] = typing.Any
                elif len(args) > 2:
                    args = list(args)
                    args[2] = typing.Any
                return original_infer(*args, **kwargs)
        pydantic_fields.ModelField.infer = patched_infer
    except ImportError:
        pass
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print('Błąd: Nie znaleziono chromadb.')
    chromadb = None
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print('Błąd: Nie znaleziono sentence-transformers.')
    SentenceTransformer = None
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class EgzaminAnalyzer:

    def __init__(self, model_path: str=None, baza_path: str=None, load_llm: bool=True):
        print('🚀 Inicjalizacja systemu...')
        if not model_path:
            model_path = str(BASE_DIR / 'models' / 'Qwen2.5-7B-Instruct-Q4_K_M.gguf')
        if not baza_path:
            baza_path = str(BASE_DIR / 'baza_wiedzy')
        print('📊 Ładuję model embeddings (może to zająć chwilę przy pierwszym uruchomieniu)...')
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.client = chromadb.PersistentClient(path=baza_path)
        self.collection = self.client.get_or_create_collection(name='egzaminy_maturalne', metadata={'hnsw:space': 'cosine'})
        self.llm = None
        if load_llm:
            if Llama:
                print(f'🤖 Ładuję model LLM z {model_path}...')
                try:
                    self.llm = Llama(model_path=model_path, n_ctx=8192, n_threads=os.cpu_count() or 4, verbose=False)
                    print('✅ Model LLM załadowany!')
                except Exception as e:
                    print(f'❌ Błąd podczas ładowania LLM: {e}')
            else:
                print('⚠️ Nie można załadować LLM (brak llama-cpp-python)')
        print('✅ System gotowy!\n')

    def wyciagnij_tekst_z_pdf(self, sciezka_pdf: str) -> str:
        tekst = ''
        try:
            import pdfplumber
            with pdfplumber.open(sciezka_pdf) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        tekst += t + '\n'
        except Exception:
            pass
        if not tekst.strip():
            try:
                with open(sciezka_pdf, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            tekst += t + '\n'
            except Exception:
                pass
        if not tekst.strip():
            print(f'   🔍 Wykryto skan lub brak tekstu w {os.path.basename(sciezka_pdf)}. Uruchamiam OCR (może to potrwać)...')
            try:
                from pdf2image import convert_from_path
                import easyocr
                import numpy as np
                from PIL import Image
                poppler_path = str(BASE_DIR / 'bin' / 'poppler' / 'poppler-24.08.0' / 'Library' / 'bin')
                pages = convert_from_path(sciezka_pdf, 300, poppler_path=poppler_path)
                reader = easyocr.Reader(['pl', 'en'])
                total_pages = len(pages)
                for i, page in enumerate(pages):
                    print(f'      📄 Przetwarzam stronę {i + 1}/{total_pages}...')
                    page_array = np.array(page)
                    results = reader.readtext(page_array, detail=0)
                    if results:
                        tekst += ' '.join(results) + '\n'
            except Exception as e:
                print(f'   ❌ Błąd OCR (EasyOCR): {e}. Upewnij się, że biblioteki są zainstalowane.')
        return tekst

    def parsuj_egzamin_pytania(self, tekst: str) -> List[Dict]:
        zadania = []
        keywords = '(?:Zadanie|Pytanie|Zapytanie|Skrypt|Styl(?: CSS)?|Witryna(?: internetowa)?|Cechy(?: witryny)?)'
        pattern_num = '(?:^|\\n)[ \\t]*[‒–—\\-\\*•]?\\s*(' + keywords + ')(?=\\s*[:\\d\\n])\\s*:?\\s*(\\d+)?(?:\\.(\\d+))?\\.?\\s*(?:\\(0–(\\d+)\\))?(.*?)(?=(?:\\n[ \\t]*[‒–—\\-\\*•]?\\s*' + keywords + '(?=\\s*[:\\d\\n]))|Wypełnia\\s+egzaminator|BRUDNOPIS|Strona\\s+\\d+|$)'
        pattern_prac = 'Zadanie\\s+egzaminacyjne\\s*(.*?)(?=(?:^|\\n)[ \\t]*[‒–—\\-\\*•]?\\s*' + keywords + '(?=\\s*[:\\d\\n])|Wypełnia\\s+egzaminator|BRUDNOPIS|Strona\\s+\\d+|$)'
        matches_num = list(re.finditer(pattern_num, tekst, re.DOTALL | re.IGNORECASE))
        for match in matches_num:
            keyword = match.group(1)
            major = match.group(2) or ''
            minor = match.group(3) or ''
            punkty = match.group(4) or '1'
            tresc = match.group(5).strip()
            if major:
                numer = f'{keyword} {major}.{minor}' if minor else f'{keyword} {major}'
            else:
                numer = keyword
            tresc = self._wyczysc_tresc(tresc)
            if len(tresc) > 5 and (not any((z['tresc'][:100] == tresc[:100] for z in zadania))):
                task_type = None
                if 'Zapytanie' in keyword:
                    task_type = 'SQL'
                elif 'Skrypt' in keyword:
                    if any((x in tresc.lower() for x in ['php', 'mysqli', 'serwer', 'baza', 'query'])):
                        task_type = 'PHP'
                    elif any((x in tresc.lower() for x in ['javascript', 'js', 'onclick', 'zdarzenie', 'alert', 'document.'])):
                        task_type = 'JS'
                    else:
                        task_type = 'PHP'
                elif 'Styl' in keyword:
                    task_type = 'CSS'
                elif 'Witryna' in keyword or 'Cechy' in keyword:
                    task_type = 'HTML'
                zadania.append({'numer': numer, 'punkty': int(punkty), 'tresc': tresc[:4000], 'typ': task_type})
        if not zadania:
            matches_prac = list(re.finditer(pattern_prac, tekst, re.DOTALL | re.IGNORECASE))
            for i, match in enumerate(matches_prac):
                tresc = match.group(1).strip()
                tresc = self._wyczysc_tresc(tresc)
                if len(tresc) > 100:
                    zadania.append({'numer': 'Praktyczne', 'punkty': 40, 'tresc': tresc[:8000]})
        return zadania

    def _wyczysc_tresc(self, tresc: str) -> str:
        tresc = re.sub('Strona\\s+\\d+\\s+z\\s+\\d+', '', tresc)
        tresc = re.sub('MIN_\\w+', '', tresc)
        tresc = re.sub('\\s+', ' ', tresc).strip()
        return tresc

    def parsuj_egzamin_odpowiedzi(self, tekst: str) -> Dict[str, str]:
        odpowiedzi = {}
        pattern = 'Zadanie\\s+(\\d+)(?:\\.(\\d+))?\\.?\\s*(?:\\(0–\\d+\\))?(.*?)(?=Zadanie\\s+\\d+|Strona\\s+\\d+|$)'
        matches = re.finditer(pattern, tekst, re.DOTALL | re.IGNORECASE)
        for match in matches:
            major = match.group(1)
            minor = match.group(2)
            numer = f'{major}.{minor}' if minor else major
            tresc = match.group(3)
            odp_match = re.search('(?:Poprawna odpowiedź|Zasady oceniania|Schemat punktowania)[:\\s]*(.*?)(?=Zadanie|Strona|$)', tresc, re.DOTALL | re.IGNORECASE)
            if odp_match:
                odpowiedz = odp_match.group(1).strip()
                odpowiedz = re.sub('\\s+', ' ', odpowiedz)
                odpowiedzi[numer] = odpowiedz[:1000]
            else:
                odpowiedzi[numer] = tresc.strip()[:1000]
        return odpowiedzi

    def dodaj_zadanie_recznie(self, tresc: str, rozwiazanie: str, rok: str, numer: str, miesiac: str='maj', punkty: int=1):
        pelny_tekst = f'EGZAMIN: {miesiac} {rok}\nZADANIE: {numer} ({punkty} pkt)\n\nTREŚĆ ZADANIA:\n{tresc}\n\nROZWIĄZANIE / KOD:\n{rozwiazanie}\n'
        embedding = self.embedder.encode(pelny_tekst).tolist()
        doc_id = f'{rok}_{miesiac}_{numer}_manual'
        self.collection.add(documents=[pelny_tekst], embeddings=[embedding], metadatas=[{'rok': rok, 'miesiac': miesiac, 'numer': numer, 'punkty': punkty}], ids=[doc_id])

    def dodaj_egzamin(self, pdf_pytania: str, pdf_odpowiedzi: str, rok: str, miesiac: str='maj'):
        print(f'\n📚 Przetwarzam egzamin: {miesiac} {rok}')
        tekst_pytania = self.wyciagnij_tekst_z_pdf(pdf_pytania)
        tekst_odpowiedzi = self.wyciagnij_tekst_z_pdf(pdf_odpowiedzi)
        zadania = self.parsuj_egzamin_pytania(tekst_pytania)
        odpowiedzi = self.parsuj_egzamin_odpowiedzi(tekst_odpowiedzi)
        print(f'   Znaleziono {len(zadania)} zadań')
        print(f'   Znaleziono {len(odpowiedzi)} odpowiedzi')
        dodano = 0
        for zadanie in zadania:
            numer = zadanie['numer']
            pelny_tekst = f"EGZAMIN: {miesiac} {rok}\nZADANIE: {numer} ({zadanie['punkty']} pkt)\n\nTREŚĆ ZADANIA:\n{zadanie['tresc']}\n\nODPOWIEDŹ:\n{odpowiedzi.get(numer, 'Brak odpowiedzi')}\n"
            embedding = self.embedder.encode(pelny_tekst).tolist()
            doc_id = f'{rok}_{miesiac}_{numer}'
            try:
                self.collection.add(documents=[pelny_tekst], embeddings=[embedding], metadatas=[{'rok': rok, 'miesiac': miesiac, 'numer': numer, 'punkty': zadanie['punkty']}], ids=[doc_id])
                dodano += 1
            except Exception as e:
                print(f'   ⚠️  Błąd przy dodawaniu {doc_id}: {e}')
        print(f'   ✅ Dodano {dodano} zadań do bazy\n')

    def masowy_import(self, folder_sciezka: str):
        folder = Path(folder_sciezka)
        if not folder.exists():
            print(f'❌ Folder nie istnieje: {folder_sciezka}')
            return
        print(f'📂 Rozpoczynam masowy import z: {folder_sciezka}')
        arkusze = list(folder.glob('*-rozszerzona.pdf')) + list(folder.glob('*-podstawowa.pdf'))
        for arkusz_path in arkusze:
            nazwa = arkusz_path.stem
            odp_nazwa = f'{nazwa}-odpowiedzi.pdf'
            odp_path = folder / odp_nazwa
            if odp_path.exists():
                czesci = nazwa.split('-')
                rok = next((c for c in czesci if c.isdigit()), '2024')
                miesiac = 'maj'
                if 'czerwiec' in nazwa:
                    miesiac = 'czerwiec'
                if 'sierpien' in nazwa:
                    miesiac = 'sierpien'
                self.dodaj_egzamin(str(arkusz_path), str(odp_path), rok, miesiac)
            else:
                print(f'⚠️ Pominąłem {nazwa} (brak pliku odpowiedzi: {odp_nazwa})')

    def znajdz_podobne(self, pytanie: str, n: int=5) -> List[Dict]:
        embedding = self.embedder.encode(pytanie).tolist()
        wyniki = self.collection.query(query_embeddings=[embedding], n_results=n)
        podobne = []
        for i in range(len(wyniki['documents'][0])):
            podobne.append({'dokument': wyniki['documents'][0][i], 'metadane': wyniki['metadatas'][0][i], 'odleglosc': wyniki['distances'][0][i] if 'distances' in wyniki else None})
        return podobne

    def odpowiedz_na_pytanie(self, pytanie: str, n_przykladow: int=3, forced_type: str=None) -> str:
        podobne = self.znajdz_podobne(pytanie, n_przykladow)
        max_doc_len = 1000
        kontekst_czesci = []
        for i, p in enumerate(podobne):
            doc_text = p['dokument']
            if len(doc_text) > max_doc_len:
                doc_text = doc_text[:max_doc_len] + '...'
            meta = p['metadane']
            if meta.get('typ') == 'podrecznik':
                source_info = f"PODRĘCZNIK: {meta.get('tytul', 'brak')}, fragment {meta.get('fragment', 'brak')}"
            else:
                source_info = f"EGZAMIN: {meta.get('miesiac', 'maj')} {meta.get('rok', 'brak')}, zadanie {meta.get('numer', 'brak')}"
            kontekst_czesci.append(f'ŹRÓDŁO {i + 1} ({source_info}):\n{doc_text}')
        kontekst = '\n\n' + '-' * 30 + '\n\n'.join(kontekst_czesci)
        if not self.llm:
            return f'🔍 ZNALAZŁEM PODOBNE ZADANIA Z ARCHIWUM:\n{kontekst}\n\n💡 WSKAZÓWKA: Przeanalizuj powyższe przykłady aby rozwiązać swoje zadanie.\n(Uwaga: Model językowy nie został załadowany, więc nie mogę wygenerować pełnej analizy).\n'
        if len(pytanie) > 15000:
            pytanie = pytanie[:15000] + '... [TREŚĆ OBCIĘTA ZE WZGLĘDU NA DŁUGOŚĆ]'
        pytanie_lower = pytanie.lower()
        current_type = forced_type
        if not current_type:
            if any((x in pytanie_lower for x in ['css', 'styl', 'arkusz stylów', 'formatowanie'])):
                current_type = 'CSS'
            elif any((x in pytanie_lower for x in ['sql', 'kwerenda', 'zapytanie', 'insert into', 'select ', 'update ', 'delete from'])):
                current_type = 'SQL'
            elif any((x in pytanie_lower for x in ['php', 'mysqli', 'serwerowe', 'baza', 'połączenie z bazą'])):
                current_type = 'PHP'
            elif any((x in pytanie_lower for x in ['javascript', 'js', 'onclick', 'zdarzenie', 'klient', 'alert', 'document.'])):
                current_type = 'JS'
            elif 'skrypt' in pytanie_lower:
                if any((x in pytanie_lower for x in ['baza', 'sql', 'tabeli', 'rekord', 'mysqli'])):
                    current_type = 'PHP'
                else:
                    current_type = 'JS'
            elif any((x in pytanie_lower for x in ['html', 'witryna', 'struktura'])):
                current_type = 'HTML'
        if current_type == 'CSS':
            task_type = 'CSS'
            instructions = 'Twoim zadaniem jest wygenerowanie WYŁĄCZNIE kodu CSS. \nZASADY:\n1. TŁUMACZENIE TERMINÓW: \n   - "margines wewnętrzny" = padding\n   - "margines zewnętrzny" = margin\n   - "odstęp między literami" = letter-spacing\n   - "czcionka" = font-family\n   - "kolor pisma/tekstu" = color\n2. Używaj DOKŁADNYCH nazw klas (.) i identyfikatorów (#) z treści zadania.\n3. NIE PISZ kodu HTML, PHP ani SQL. TYLKO CSS.\n4. NIE PISZ żadnych instrukcji ani wyjaśnień.\n5. TYLKO KOD CSS w bloku ```css ... ```.'
        elif current_type == 'JS':
            task_type = 'JavaScript'
            instructions = 'Twoim zadaniem jest wygenerowanie skryptu JavaScript (po stronie klienta).\nZASADY:\n1. Używaj czystego JavaScript (Vanilla JS) chyba że zadanie prosi o bibliotekę.\n2. Skup się na manipulacji DOM (document.getElementById, addEventListener, itp.).\n3. NIE PISZ kodu PHP ani SQL.\n4. NIE PISZ żadnych instrukcji ani wyjaśnień.\n5. TYLKO KOD JS w bloku ```javascript ... ```.'
        elif current_type == 'HTML':
            task_type = 'HTML'
            instructions = 'Twoim zadaniem jest wygenerowanie struktury HTML5 zgodnie z wytycznymi.\nZASADY:\n1. Stosuj semantyczne tagi HTML5 (header, main, footer, nav, section).\n2. Podaj kompletny szkielet dokumentu (DOCTYPE, html lang="pl", head, body).\n3. Dołączaj linki do arkuszy stylów i skryptów wymienionych w zadaniu.\n4. Skup się na strukturze opisanej w sekcji "Cechy witryny" lub "Witryna internetowa".\n5. TYLKO KOD HTML w bloku ```html ... ```.'
        elif current_type == 'SQL':
            task_type = 'SQL'
            instructions = 'Twoim zadaniem jest wygenerowanie WYŁĄCZNIE czystego kodu SQL.\nZASADY:\n1. Używaj DOKŁADNYCH nazw tabel i pól z treści zadania.\n2. ABSOLUTNY ZAKAZ PISANIA KODU PHP (np. mysqli_query, $db). \n3. Jeśli zadanie to "Zapytanie X", podaj tylko treść kwerendy.\n4. NIE PISZ żadnych komentarzy ani wyjaśnień przed ani po kodzie.\n5. TYLKO KOD SQL w bloku ```sql ... ```.'
        elif current_type == 'PHP':
            task_type = 'PHP'
            instructions = 'Twoim zadaniem jest wygenerowanie skryptu PHP.\nZASADY:\n1. Używaj standardowych funkcji mysqli (połączenie: localhost, root, bez hasła).\n2. Pisz czysty, techniczny kod. Unikaj zbędnych transformacji danych, jeśli zadanie o nie nie prosi.\n3. Jeśli zadanie wymaga wyświetlenia danych w tabeli lub liście, wygeneruj odpowiedni kod HTML wewnątrz PHP.\n4. TYLKO KOD PHP w bloku ```php ... ```.'
        else:
            task_type = 'General IT'
            instructions = 'Podaj konkretną i krótką odpowiedź. Jeśli zadanie wymaga kodu, podaj tylko kod. Bez zbędnych wstępów.'
        system_msg = f'Jesteś elitarnym ekspertem IT rozwiązującym zadania egzaminacyjne (INF.03/EE.09/Matura).\nJesteś systemem "CODE-ONLY". Twoim jedynym celem jest podanie technicznego, gotowego do użycia rozwiązania.\n{instructions}'
        user_msg = f"Poniżej znajduje się kontekst z bazy wiedzy (użyj go TYLKO jako inspiracji technicznej, nie kopiuj danych jeśli nie pasują do zadania):\n{(kontekst[:2500] if kontekst else 'Brak')}\n\nGŁÓWNE ZADANIE DO ROZWIĄZANIA (Priorytet):\n{pytanie}\n\nPamiętaj: Rozwiąż powyższe zadanie DOKŁADNIE według jego wytycznych.\nROZWIĄZANIE TECHNICZNE:"
        full_prompt = f'<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n'
        try:
            res = self.llm(full_prompt, max_tokens=2048, temperature=0.0, repeat_penalty=1.1, top_p=0.9, stop=['<|im_end|>', '<|im_start|>', 'PYTANIE UŻYTKOWNIKA:', '```\n\n\n'], echo=False)
            tekst_odp = res['choices'][0]['text'].strip()
            if not tekst_odp:
                return '⚠️ Model nie wygenerował odpowiedzi.'
            verify_prompt = f'<|im_start|>system\nJesteś surowym audytorem technicznym. Sprawdzasz zgodność kodu z treścią zadania.\nZASADA: Jeśli kod jest poprawny, odpowiadasz tylko słowem "POPRAWNE". \nJeśli znajdziesz błąd, podaj TYLKO poprawiony kod w bloku ```.<|im_end|>\n<|im_start|>user\nZADANIE:\n{pytanie}\n\nWYGENEROWANE ROZWIĄZANIE:\n{tekst_odp}\n\nCzy rozwiązanie spełnia WSZYSTKIE wytyczne zadania? Sprawdź typ skryptu (JS/PHP), kolory i nazwy.<|im_end|>\n<|im_start|>assistant\n'
            res_verify = self.llm(verify_prompt, max_tokens=2048, temperature=0.0, repeat_penalty=1.1, stop=['<|im_end|>', '<|im_start|>'], echo=False)
            weryfikacja = res_verify['choices'][0]['text'].strip()
            if 'POPRAWNE' not in weryfikacja.upper() and ('```' in weryfikacja or len(weryfikacja) > 20):
                return weryfikacja
            return tekst_odp
        except Exception as e:
            return f'❌ Błąd: {e}'

    def generuj_nowe_zadanie(self, temat: str) -> str:
        if not self.llm:
            return '❌ Model LLM nie jest załadowany. Nie mogę wygenerować nowego zadania.'
        podobne = self.znajdz_podobne(temat, n=2)
        kontekst = '\n\n'.join([p['dokument'] for p in podobne])
        system_msg = 'Jesteś elitarnym architektem edukacyjnym i przewodniczącym komisji egzaminacyjnej. \nTwoim zadaniem jest tworzenie unikalnych, ambitnych i bezbłędnych merytorycznie zadań egzaminacyjnych.\n\nWYMAGANIA DOTYCZĄCE ZADANIA:\n1. UNIKALNOŚĆ: Nie kopiuj istniejących zadań. Stwórz coś nowego, co sprawdza głębokie zrozumienie tematu.\n2. STRUKTURA: Zadanie musi mieć jasny opis, dane wejściowe/wyjściowe, punktację i kompletne, wzorcowe rozwiązanie (kod lub opis).\n3. POZIOM: Dopasuj poziom do matury rozszerzonej lub egzaminu zawodowego (INF.03).\n4. PRECYZJA: Każde polecenie musi być jednoznaczne. Nie może być wątpliwości, co uczeń ma wykonać.\n\nStyl: Profesjonalny, egzaminacyjny język polski.'
        user_msg = f'Na podstawie poniższych przykładów dla inspiracji (ale nie kopiuj ich!):\n{kontekst}\n\nSTWÓRZ NOWE ZADANIE NA TEMAT: {temat}\n\nTwoja propozycja powinna zawierać:\n- Tytuł zadania\n- Pełną treść\n- Przykładowe dane\n- Szczegółowy schemat oceniania\n- Wzorcowe rozwiązanie'
        full_prompt = f'<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\nOto autorskie zadanie egzaminacyjne:\n\n'
        try:
            print(f'⏳ Generowanie nowego zadania na temat: {temat}...')
            res = self.llm(full_prompt, max_tokens=2048, temperature=0.8, stop=['<|im_end|>', '<|im_start|>'], echo=False)
            return res['choices'][0]['text'].strip()
        except Exception as e:
            return f'❌ Błąd generowania zadania: {e}'

    def analiza_calego_egzaminu(self, pdf_path: str, output_file: str='wyniki.txt'):
        print(f'\n📝 Analizuję egzamin: {pdf_path}')
        tekst = self.wyciagnij_tekst_z_pdf(pdf_path)
        zadania = self.parsuj_egzamin_pytania(tekst)
        print(f'   Znaleziono {len(zadania)} zadań\n')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write('ANALIZA EGZAMINU MATURALNEGO Z INFORMATYKI\n')
            f.write(f'Wygenerowano przez System RAG\n')
            f.write('=' * 80 + '\n\n')
            for zadanie in zadania:
                print(f"   Analizuję zadanie {zadanie['numer']}...")
                f.write('\n' + '=' * 80 + '\n')
                f.write(f"ZADANIE {zadanie['numer']} ({zadanie['punkty']} pkt)\n")
                f.write('=' * 80 + '\n\n')
                f.write(f"TREŚĆ:\n{zadanie['tresc']}\n\n")
                odpowiedz = self.odpowiedz_na_pytanie(zadanie['tresc'], forced_type=zadanie.get('typ'))
                f.write(odpowiedz + '\n\n')
        print(f'\n✅ Wyniki zapisane do: {output_file}')

    def statystyki(self):
        count = self.collection.count()
        print(f'\n📊 STATYSTYKI BAZY WIEDZY:')
        print(f'   Łączna liczba fragmentów: {count}')
        lata = {}
        przedmioty = set()
        podreczniki = {}
        if count > 0:
            sample = self.collection.get(include=['metadatas'])
            for meta in sample['metadatas']:
                if meta.get('typ') == 'podrecznik':
                    tytul = meta.get('tytul', 'Nieznany')
                    podreczniki[tytul] = podreczniki.get(tytul, 0) + 1
                else:
                    rok = meta.get('rok', 'Nieznany')
                    lata[rok] = lata.get(rok, 0) + 1
                    przedmiot = meta.get('przedmiot', 'Nieznany')
                    przedmioty.add(przedmiot)
            if lata:
                print(f'   Egzaminy w bazie:')
                for rok in sorted(lata.keys()):
                    print(f'      - {rok}: {lata[rok]} zadań')
            if podreczniki:
                print(f'   Podręczniki w bazie:')
                for tytul in sorted(podreczniki.keys()):
                    print(f'      - {tytul}: {podreczniki[tytul]} fragmentów')
            if przedmioty:
                print(f"   Przedmioty: {', '.join(sorted(przedmioty))}")
        print()
        return {'total_count': count, 'years': sorted(lata.keys()), 'textbooks': sorted(podreczniki.keys()), 'subjects': sorted(list(przedmioty))}

def main():
    print('\n╔════════════════════════════════════════════════════════════════╗\n║     SYSTEM RAG DO ANALIZY EGZAMINÓW MATURALNYCH                ║\n║                  Z INFORMATYKI                                  ║\n╚════════════════════════════════════════════════════════════════╝\n')
    analyzer = EgzaminAnalyzer(model_path=None, baza_path='./baza_egzaminow')
    print('📖 KROK 1: Dodawanie egzaminów do bazy wiedzy')
    print('-' * 60)
    analyzer.dodaj_egzamin(pdf_pytania='/mnt/user-data/uploads/informatyka-2017-maj-matura-rozszerzona.pdf', pdf_odpowiedzi='/mnt/user-data/uploads/informatyka-2017-maj-matura-rozszerzona-odpowiedzi.pdf', rok='2017', miesiac='maj')
    analyzer.statystyki()
    print('\n🔍 KROK 2: Testowanie wyszukiwania podobnych zadań')
    print('-' * 60)
    przyklad_pytanie = '\n    Dana jest dodatnia liczba całkowita k. \n    Jaka jest najmniejsza dodatnia liczba całkowita x, \n    dla której obliczanie wartości wymaga dokładnie k wywołań funkcji?\n    '
    podobne = analyzer.znajdz_podobne(przyklad_pytanie, n=3)
    print(f'Pytanie: {przyklad_pytanie}')
    print(f'\nZnaleziono {len(podobne)} podobnych zadań:\n')
    for i, p in enumerate(podobne, 1):
        print(f"{i}. Egzamin: {p['metadane']['miesiac']} {p['metadane']['rok']}, zadanie {p['metadane']['numer']} ({p['metadane']['punkty']} pkt)")
        print(f"   Fragment: {p['dokument'][:200]}...")
        print()
    print('\n📝 KROK 3: Analiza nowego egzaminu (opcjonalne)')
    print('-' * 60)
    print('Aby przeanalizować nowy egzamin, użyj:')
    print('analyzer.analiza_calego_egzaminu("nowy_egzamin.pdf", "wyniki.txt")')
    print('\n' + '=' * 60)
    print('✅ GOTOWE! System działa i jest gotowy do użycia.')
    print('=' * 60)
if __name__ == '__main__':
    main()