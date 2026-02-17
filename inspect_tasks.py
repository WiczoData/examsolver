import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
try:
    from main import EgzaminAnalyzer
    analyzer = EgzaminAnalyzer()
    collection = analyzer.collection
    results = collection.get()
    print(f"\n--- SZCZEGÓŁY BAZY ({len(results['ids'])} dokumentów) ---")
    exams = {}
    for i in range(len(results['ids'])):
        meta = results['metadatas'][i]
        key = f"{meta.get('rok', '???')} - {meta.get('przedmiot', '???')}"
        if key not in exams:
            exams[key] = []
        exams[key].append(results['ids'][i])
    for exam, ids in exams.items():
        print(f'Egzamin: {exam}')
        print(f'  - Liczba zadań: {len(ids)}')
        for j in range(min(3, len(ids))):
            doc_idx = results['ids'].index(ids[j])
            content = results['documents'][doc_idx][:100].replace('\n', ' ')
            print(f'    - [{ids[j]}] {content}...')
except Exception as e:
    print(f'Błąd: {e}')