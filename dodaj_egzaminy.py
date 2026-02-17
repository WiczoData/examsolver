from main import EgzaminAnalyzer
import os
import glob

def dodaj_wszystkie_egzaminy(folder: str='.'):
    print('🔍 Szukam plików PDF w folderze:', folder)
    pdfy = glob.glob(os.path.join(folder, '*.pdf'))
    print(f'   Znaleziono {len(pdfy)} plików PDF\n')
    pary = []
    for pdf in pdfy:
        nazwa = os.path.basename(pdf).lower()
        if 'odpowied' in nazwa or 'odp' in nazwa or 'answer' in nazwa:
            continue
        bez_rozszerzenia = pdf[:-4]
        mozliwe_odpowiedzi = [bez_rozszerzenia + '-odpowiedzi.pdf', bez_rozszerzenia + '_odpowiedzi.pdf', bez_rozszerzenia + '-odp.pdf', bez_rozszerzenia + '_odp.pdf']
        plik_odp = None
        for mozliwa in mozliwe_odpowiedzi:
            if os.path.exists(mozliwa):
                plik_odp = mozliwa
                break
        if plik_odp:
            import re
            match = re.search('(\\d{4})', nazwa)
            rok = match.group(1) if match else 'nieznany'
            miesiac = 'maj'
            if 'czerwiec' in nazwa or 'june' in nazwa:
                miesiac = 'czerwiec'
            elif 'styczen' in nazwa or 'january' in nazwa:
                miesiac = 'styczeń'
            pary.append((pdf, plik_odp, rok, miesiac))
    if not pary:
        print('❌ Nie znaleziono par plików (pytania + odpowiedzi)')
        print('\nSprawdź czy pliki mają format:')
        print('  - nazwa.pdf')
        print('  - nazwa-odpowiedzi.pdf')
        return
    print(f'✅ Znaleziono {len(pary)} par plików:\n')
    for i, (pytania, odp, rok, miesiac) in enumerate(pary, 1):
        print(f'{i}. {os.path.basename(pytania)}')
        print(f'   → {os.path.basename(odp)}')
        print(f'   Rok: {rok}, Miesiąc: {miesiac}\n')
    odpowiedz = input('Dodać wszystkie do bazy? (t/n): ').strip().lower()
    if odpowiedz != 't':
        print('Anulowano.')
        return
    print('\n🚀 Inicjalizacja systemu...')
    analyzer = EgzaminAnalyzer()
    sukces = 0
    bledy = 0
    for pytania, odp, rok, miesiac in pary:
        try:
            analyzer.dodaj_egzamin(pytania, odp, rok, miesiac)
            sukces += 1
        except Exception as e:
            print(f'❌ Błąd przy {rok}: {e}')
            bledy += 1
    print('\n' + '=' * 60)
    print('PODSUMOWANIE')
    print('=' * 60)
    print(f'✅ Pomyślnie dodano: {sukces}')
    print(f'❌ Błędy: {bledy}')
    print('=' * 60 + '\n')
    analyzer.statystyki()

def dodaj_recznie():
    print('📝 RĘCZNE DODAWANIE EGZAMINÓW\n')
    print('Podaj listę egzaminów w formacie:')
    print('pytania.pdf, odpowiedzi.pdf, rok, miesiąc')
    print('\nPrzykład:')
    print('egzamin_2017.pdf, odp_2017.pdf, 2017, maj')
    print('egzamin_2018.pdf, odp_2018.pdf, 2018, maj')
    print('\n(zakończ pustą linią)\n')
    egzaminy = []
    while True:
        linia = input().strip()
        if not linia:
            break
        try:
            czesci = [c.strip() for c in linia.split(',')]
            if len(czesci) != 4:
                print('❌ Błąd: potrzebuję 4 wartości (pytania, odpowiedzi, rok, miesiąc)')
                continue
            egzaminy.append(tuple(czesci))
        except Exception as e:
            print(f'❌ Błąd parsowania: {e}')
    if not egzaminy:
        print('Nie dodano żadnych egzaminów')
        return
    print(f'\n✅ Przygotowano {len(egzaminy)} egzaminów do dodania')
    print('\n🚀 Inicjalizacja systemu...')
    analyzer = EgzaminAnalyzer()
    for pytania, odp, rok, miesiac in egzaminy:
        if not os.path.exists(pytania):
            print(f'⚠️  Plik nie istnieje: {pytania}, pomijam...')
            continue
        if not os.path.exists(odp):
            print(f'⚠️  Plik nie istnieje: {odp}, pomijam...')
            continue
        try:
            analyzer.dodaj_egzamin(pytania, odp, rok, miesiac)
        except Exception as e:
            print(f'❌ Błąd przy {rok}: {e}')
    print()
    analyzer.statystyki()

def main():
    print('\n╔════════════════════════════════════════════════════════════════╗\n║        MASOWE DODAWANIE EGZAMINÓW DO BAZY                      ║\n╚════════════════════════════════════════════════════════════════╝\n\nWybierz opcję:\n\n1. 🔍 Automatycznie znajdź i dodaj wszystkie PDFy z folderu\n2. ✍️  Dodaj ręcznie (podaj listę plików)\n3. ❌ Anuluj\n\n')
    wybor = input('Wybór (1-3): ').strip()
    if wybor == '1':
        folder = input('\nFolder z PDFami (Enter = bieżący folder): ').strip()
        folder = folder if folder else '.'
        dodaj_wszystkie_egzaminy(folder)
    elif wybor == '2':
        dodaj_recznie()
    else:
        print('Anulowano')
if __name__ == '__main__':
    main()