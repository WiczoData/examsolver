import os
import re
import sys
from pathlib import Path
from main import EgzaminAnalyzer

def import_podreczniki():
    analyzer = EgzaminAnalyzer(load_llm=False)
    podreczniki_dir = Path('e:/szpont/podreczniki')
    if not podreczniki_dir.exists():
        print(f'❌ Folder {podreczniki_dir} nie istnieje!')
        return
    print(f'🚀 Rozpoczynam skanowanie folderu: {podreczniki_dir}')
    pdf_files = list(podreczniki_dir.rglob('*.pdf'))
    print(f'📄 Znaleziono {len(pdf_files)} plików PDF.')
    total_chunks = 0
    stats = analyzer.statystyki()
    juz_w_bazie = set(stats.get('textbooks', []))
    for pdf_path in pdf_files:
        if pdf_path.stem in juz_w_bazie:
            print(f'⏭️  Pomijam {pdf_path.name} (już jest w bazie)')
            continue
        print(f'\n📖 Przetwarzam: {pdf_path.name}')
        try:
            tekst = analyzer.wyciagnij_tekst_z_pdf(str(pdf_path))
            if not tekst.strip():
                print(f'⚠️  Pusty tekst w {pdf_path.name}, pomijam.')
                continue
            chunk_size = 1500
            overlap = 200
            chunks = []
            for i in range(0, len(tekst), chunk_size - overlap):
                chunks.append(tekst[i:i + chunk_size])
            print(f'   Podzielono na {len(chunks)} fragmentów.')
            for i, chunk in enumerate(chunks):
                doc_id = f'podrecznik_{pdf_path.stem}_{i}'
                full_doc = f'ŹRÓDŁO: Podręcznik {pdf_path.stem}\n\nTREŚĆ:\n{chunk}'
                embedding = analyzer.embedder.encode(full_doc).tolist()
                analyzer.collection.add(documents=[full_doc], embeddings=[embedding], metadatas=[{'typ': 'podrecznik', 'tytul': pdf_path.stem, 'fragment': i, 'rok': 'brak', 'miesiac': 'brak', 'numer': 'brak', 'punkty': 0, 'przedmiot': 'PODRECZNIK'}], ids=[doc_id])
                total_chunks += 1
            print(f'   ✅ Zaimportowano {pdf_path.name}')
        except Exception as e:
            print(f'   ❌ Błąd podczas przetwarzania {pdf_path.name}: {e}')
    print(f'\n✨ ZAKOŃCZONO IMPORT PODRĘCZNIKÓW ✨')
    print(f'Suma dodanych fragmentów: {total_chunks}')
if __name__ == '__main__':
    import_podreczniki()