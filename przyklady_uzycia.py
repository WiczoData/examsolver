from main import EgzaminAnalyzer

def przyklad_1_dodawanie():
    analyzer = EgzaminAnalyzer()
    egzaminy = [('egzaminy/2017_pytania.pdf', 'egzaminy/2017_odp.pdf', '2017', 'maj'), ('egzaminy/2018_pytania.pdf', 'egzaminy/2018_odp.pdf', '2018', 'maj'), ('egzaminy/2019_pytania.pdf', 'egzaminy/2019_odp.pdf', '2019', 'maj')]
    for pytania, odpowiedzi, rok, miesiac in egzaminy:
        try:
            analyzer.dodaj_egzamin(pytania, odpowiedzi, rok, miesiac)
        except FileNotFoundError:
            print(f'⚠️  Pominięto {rok} - brak pliku')
    analyzer.statystyki()

def przyklad_2_wyszukiwanie():
    analyzer = EgzaminAnalyzer()
    moje_pytanie = '\n    Zadanie 2.3.\n    Dana jest dodatnia liczba całkowita k. Jaka jest najmniejsza \n    dodatnia liczba całkowita x, dla której obliczanie wartości \n    wymaga dokładnie k wywołań funkcji?\n    '
    podobne = analyzer.znajdz_podobne(moje_pytanie, n=5)
    print('🔍 ZNALEZIONE PODOBNE ZADANIA:\n')
    for i, zadanie in enumerate(podobne, 1):
        print(f"\n{'=' * 60}")
        print(f'WYNIK {i}')
        print(f"Egzamin: {zadanie['metadane']['miesiac']} {zadanie['metadane']['rok']}")
        print(f"Zadanie: {zadanie['metadane']['numer']} ({zadanie['metadane']['punkty']} pkt)")
        print(f"{'=' * 60}")
        print(zadanie['dokument'][:500] + '...')

def przyklad_3_generowanie_odpowiedzi():
    analyzer = EgzaminAnalyzer(model_path='models/model.gguf')
    pytanie = '\n    Napisz algorytm który oblicza największe pole prostokąta,\n    które nie jest podzielne przez p, a długości boków należą\n    do zbioru A i są różne.\n    '
    odpowiedz = analyzer.odpowiedz_na_pytanie(pytanie)
    print('🤖 WYGENEROWANA ODPOWIEDŹ:\n')
    print(odpowiedz)
    with open('moja_odpowiedz.txt', 'w', encoding='utf-8') as f:
        f.write(f'PYTANIE:\n{pytanie}\n\n')
        f.write(f'ODPOWIEDŹ:\n{odpowiedz}\n')
    print('\n✅ Zapisano do: moja_odpowiedz.txt')

def przyklad_4_caly_egzamin():
    analyzer = EgzaminAnalyzer()
    nowy_egzamin = 'egzaminy/egzamin_2024_maj.pdf'
    analyzer.analiza_calego_egzaminu(pdf_path=nowy_egzamin, output_file='rozwiazania_2024.txt')
    print('✅ Gotowe! Sprawdź plik: rozwiazania_2024.txt')

def przyklad_5_interaktywny():
    analyzer = EgzaminAnalyzer()
    print("💬 TRYB INTERAKTYWNY (wpisz 'exit' aby wyjść)\n")
    while True:
        print('\n' + '=' * 60)
        pytanie = input("Wklej treść zadania (lub 'exit'): ").strip()
        if pytanie.lower() == 'exit':
            break
        if not pytanie:
            continue
        podobne = analyzer.znajdz_podobne(pytanie, n=3)
        print('\n🔍 Najlepsze dopasowania:\n')
        for i, p in enumerate(podobne, 1):
            print(f"{i}. Egzamin {p['metadane']['rok']}, zadanie {p['metadane']['numer']}")
            print(f"   {p['dokument'][:200]}...\n")

def przyklad_6_eksport_json():
    import json
    analyzer = EgzaminAnalyzer()
    count = analyzer.collection.count()
    if count == 0:
        print('Baza jest pusta!')
        return
    dane = analyzer.collection.get(limit=count)
    eksport = []
    for i in range(len(dane['documents'])):
        eksport.append({'dokument': dane['documents'][i], 'metadane': dane['metadatas'][i]})
    with open('baza_egzaminow.json', 'w', encoding='utf-8') as f:
        json.dump(eksport, f, ensure_ascii=False, indent=2)
    print(f'✅ Wyeksportowano {len(eksport)} zadań do baza_egzaminow.json')

def przyklad_7_wyszukiwanie_po_roku():
    analyzer = EgzaminAnalyzer()
    szukany_rok = '2017'
    count = analyzer.collection.count()
    wszystko = analyzer.collection.get(limit=count)
    zadania_z_roku = []
    for i in range(len(wszystko['metadatas'])):
        if wszystko['metadatas'][i]['rok'] == szukany_rok:
            zadania_z_roku.append({'numer': wszystko['metadatas'][i]['numer'], 'punkty': wszystko['metadatas'][i]['punkty'], 'dokument': wszystko['documents'][i]})
    print(f'📚 Znaleziono {len(zadania_z_roku)} zadań z roku {szukany_rok}:\n')
    for z in zadania_z_roku:
        print(f"- Zadanie {z['numer']} ({z['punkty']} pkt)")
if __name__ == '__main__':
    print('\n╔════════════════════════════════════════════════════════════════╗\n║                    PRZYKŁADY UŻYCIA                            ║\n╚════════════════════════════════════════════════════════════════╝\n\nDostępne przykłady:\n\n1. Dodawanie egzaminów do bazy\n2. Wyszukiwanie podobnych zadań\n3. Generowanie odpowiedzi (wymaga LLM)\n4. Analiza całego egzaminu\n5. Tryb interaktywny\n6. Eksport do JSON\n7. Wyszukiwanie po roku\n\n')
    wybor = input('Który przykład uruchomić? (1-7, Enter = wszystkie): ').strip()
    if not wybor:
        try:
            print('\n' + '=' * 60)
            print('PRZYKŁAD 2: Wyszukiwanie')
            print('=' * 60)
            przyklad_2_wyszukiwanie()
        except Exception as e:
            print(f'Błąd: {e}')
    elif wybor == '1':
        przyklad_1_dodawanie()
    elif wybor == '2':
        przyklad_2_wyszukiwanie()
    elif wybor == '3':
        przyklad_3_generowanie_odpowiedzi()
    elif wybor == '4':
        przyklad_4_caly_egzamin()
    elif wybor == '5':
        przyklad_5_interaktywny()
    elif wybor == '6':
        przyklad_6_eksport_json()
    elif wybor == '7':
        przyklad_7_wyszukiwanie_po_roku()
    else:
        print('Nieprawidłowy wybór')
    print('\n✅ Gotowe!')