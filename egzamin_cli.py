from main import EgzaminAnalyzer
import os
import sys
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)

def main():
    try:
        analyzer = EgzaminAnalyzer(load_llm=True)
    except Exception as e:
        print(f'❌ Błąd inicjalizacji: {e}')
        return
    os.system('cls' if os.name == 'nt' else 'clear')
    print('=' * 60)
    print('🤖 ASYSTENT INFORMATYCZNY (OFFLINE)')
    print('=' * 60)
    print('Wklej treść zadania lub zadaj pytanie i naciśnij ENTER dwa razy.')
    print("Wpisz 'wyjdz', aby zamknąć program.")
    print('=' * 60)
    while True:
        print('\n� TWOJE PYTANIE / ZADANIE:')
        lines = []
        while True:
            try:
                line = input()
                if line.lower() == 'wyjdz':
                    print('👋 Do widzenia!')
                    sys.exit(0)
                if line == '':
                    break
                lines.append(line)
            except EOFError:
                break
        pytanie = '\n'.join(lines).strip()
        if not pytanie:
            continue
        zadania = analyzer.parsuj_egzamin_pytania(pytanie)
        if len(zadania) > 1:
            print(f'\n📝 Wykryto arkusz egzaminacyjny ({len(zadania)} zadań).')
            print('Generuję odpowiedzi dla wszystkich części...\n')
            for i, zadanie in enumerate(zadania):
                print(f"👉 Analizuję: {zadanie['numer']}...")
                odpowiedz = analyzer.odpowiedz_na_pytanie(zadanie['tresc'], forced_type=zadanie.get('typ'))
                print('\n' + '=' * 60)
                print(f"💡 ODPOWIEDŹ DLA: {zadanie['numer']}")
                print('=' * 60)
                print(odpowiedz)
                print('=' * 60 + '\n')
        else:
            odpowiedz = analyzer.odpowiedz_na_pytanie(pytanie)
            print('\n' + '=' * 60)
            print('💡 ODPOWIEDŹ:')
            print('=' * 60)
            print(odpowiedz)
            print('=' * 60)
if __name__ == '__main__':
    main()