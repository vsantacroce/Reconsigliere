"""Fabrique de petits PDF texte pour les tests, sans bibliothèque externe."""

from pathlib import Path


def _echapper(ligne: str) -> str:
    return ligne.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def ecrire_pdf(chemin: Path, pages: list[list[str]]) -> Path:
    """Écrit un PDF dont chaque page contient les lignes données (latin-1)."""
    objets: list[bytes] = []
    n = len(pages)
    # 1 catalogue, 2 pages, 3 police, puis (page, contenu) par page
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objets.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objets.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objets.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, lignes in enumerate(pages):
        flux = "BT /F1 9 Tf 40 800 Td 11 TL\n" + "".join(f"({_echapper(l)}) '\n" for l in lignes) + "ET"
        donnees = flux.encode("latin-1")
        objets.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                      f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * i} 0 R >>".encode())
        objets.append(b"<< /Length " + str(len(donnees)).encode() + b" >>\nstream\n" + donnees + b"\nendstream")
    sortie = bytearray(b"%PDF-1.4\n")
    positions = []
    for k, obj in enumerate(objets, start=1):
        positions.append(len(sortie))
        sortie += f"{k} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(sortie)
    sortie += f"xref\n0 {len(objets) + 1}\n0000000000 65535 f \n".encode()
    for p in positions:
        sortie += f"{p:010d} 00000 n \n".encode()
    sortie += f"trailer\n<< /Size {len(objets) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    chemin.write_bytes(bytes(sortie))
    return chemin
