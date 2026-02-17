import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
try:
    from main import EgzaminAnalyzer
    analyzer = EgzaminAnalyzer()
    stats = analyzer.statystyki()
    print('\n--- STATYSTYKI BAZY ---')
    print(f"Liczba dokumentów w bazie: {stats['total_count']}")
    print(f"Lata w bazie: {stats['years']}")
    print(f"Przedmioty w bazie: {stats['subjects']}")
except Exception as e:
    print(f'Błąd podczas sprawdzania bazy: {e}')