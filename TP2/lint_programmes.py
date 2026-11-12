#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
IGNORER = {".git", ".venv", "__pycache__", "node_modules", "preuves", "assets"}
VERSIONS_DE_DEMONSTRATION = {
    "ex2_original.c",
    "ex3_faulty.c",
    "ex4_bad.c",
    "ex6_initial.c",
    "ex6_sigaction.c",
}


@dataclass
class Controle:
    fichier: Path
    outil: str
    commande: list[str]
    code: int
    sortie: str
    categorie: str = "analyse"

    @property
    def anomalie(self) -> bool:
        return self.code != 0 or bool(self.sortie.strip())


def executable(nom: str) -> str | None:
    chemin = shutil.which(nom)
    if chemin:
        return chemin
    local = Path(sys.executable).parent / nom
    return str(local) if local.is_file() else None


def sources(dossier: Path) -> list[Path]:
    return sorted(
        (p for p in dossier.rglob("*") if p.suffix in {".c", ".py", ".sh"}
         and p.is_file() and not any(part in IGNORER for part in p.relative_to(dossier).parts)),
        key=lambda p: str(p.relative_to(dossier)),
    )


def lancer(fichier: Path, outil: str, commande: list[str], categorie: str) -> Controle:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    try:
        resultat = subprocess.run(
            commande,
            cwd=fichier.parent,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=45,
            check=False,
        )
        sortie = resultat.stdout
        if outil == "clang-tidy":
            sortie = "\n".join(
                ligne for ligne in sortie.splitlines()
                if not re.match(r"^\d+ warnings?(?: and \d+ errors?)? generated\.$", ligne)
                and not ligne.startswith("Suppressed ")
                and not ligne.startswith("Use -header-filter=")
            )
        if outil == "clang-format" and resultat.returncode:
            occurrences = re.findall(
                r":(\d+):\d+: error: code should be clang-formatted", sortie
            )
            if occurrences:
                numeros = sorted({int(ligne) for ligne in occurrences})
                apercu = ", ".join(str(ligne) for ligne in numeros[:12])
                suite = ", …" if len(numeros) > 12 else ""
                sortie = (
                    f"{len(occurrences)} écarts de mise en forme sur {len(numeros)} lignes "
                    f"(lignes {apercu}{suite}).\n"
                    f"Détails : clang-format --dry-run --Werror {fichier}\n"
                )
        return Controle(fichier, outil, commande, resultat.returncode, sortie, categorie)
    except subprocess.TimeoutExpired:
        return Controle(fichier, outil, commande, 124, "Analyse interrompue après 45 s.\n", categorie)


def verifier_python(fichier: Path) -> Controle:
    try:
        ast.parse(fichier.read_text(encoding="utf-8"), filename=str(fichier))
        return Controle(fichier, "ast.parse", [], 0, "", "syntaxe")
    except (SyntaxError, UnicodeError) as exc:
        return Controle(fichier, "ast.parse", [], 1, str(exc), "syntaxe")


def controles_pour(fichier: Path, outils: dict[str, str | None]) -> list[Controle]:
    verifications: list[Controle] = []
    if fichier.suffix == ".c":
        gcc = outils["gcc"]
        if gcc:
            verifications.append(lancer(fichier, "GCC + -fanalyzer", [
                gcc, "-std=c11", "-O0", "-fsyntax-only", "-fanalyzer", "-Wall", "-Wextra",
                "-Wpedantic", "-Wshadow", "-Wconversion", "-Wformat=2",
                "-Wstrict-prototypes", str(fichier),
            ], "compilation"))
        cppcheck = outils["cppcheck"]
        if cppcheck:
            verifications.append(lancer(fichier, "cppcheck", [
                cppcheck, "--quiet", "--enable=all", "--inconclusive", "--std=c11",
                "--check-level=exhaustive", "--error-exitcode=1",
                "--suppress=missingIncludeSystem", "--suppress=checkersReport",
                "--template={file}:{line}:{severity}:{id}:{message}", str(fichier),
            ], "analyse"))
        clang_tidy = outils["clang-tidy"]
        if clang_tidy:
            verifications.append(lancer(fichier, "clang-tidy", [
                clang_tidy, "-quiet",
                (
                    "-checks=-*,clang-analyzer-*,bugprone-*,"
                    "-clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling"
                ),
                str(fichier), "--", "-std=c11",
            ], "analyse"))
        clang_format = outils["clang-format"]
        if clang_format:
            verifications.append(lancer(fichier, "clang-format", [
                clang_format, "--dry-run", "--Werror", str(fichier),
            ], "mise en forme"))
    elif fichier.suffix == ".py":
        verifications.append(verifier_python(fichier))
        ruff = outils["ruff"]
        if ruff:
            verifications.append(lancer(fichier, "ruff", [
                ruff, "check", "--quiet", "--output-format=concise", str(fichier),
            ], "analyse"))
    elif fichier.suffix == ".sh":
        bash = outils["bash"]
        if bash:
            verifications.append(lancer(fichier, "bash -n", [bash, "-n", str(fichier)], "syntaxe"))
        shellcheck = outils["shellcheck"]
        if shellcheck:
            verifications.append(lancer(fichier, "shellcheck", [
                shellcheck, "-S", "warning", str(fichier),
            ], "analyse"))
    return verifications


def rendre_rapport(dossier: Path, fichiers: list[Path], controles: list[Controle],
                   outils: dict[str, str | None]) -> str:
    maintenant = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M %Z")
    lignes = [
        "# Rapport de lint — R3.05",
        "",
        f"Date : {maintenant}. Sources examinées : **{len(fichiers)}**.",
        "",
        (
            "Les programmes ne sont pas exécutés : GCC, cppcheck, clang-tidy, ShellCheck et Ruff "
            "effectuent uniquement des contrôles statiques."
        ),
        "",
        "## Outils",
        "",
    ]
    for nom, chemin in outils.items():
        lignes.append(f"- `{nom}` : {'disponible' if chemin else 'non installé'}.")
    lignes.extend([
        "",
        (
            "Si nécessaire : `sudo apt install cppcheck clang-tidy clang-format shellcheck` et "
            "`python3 -m pip install ruff`."
        ),
        "",
        (
            "Les fichiers `*_faulty.c`, `*_bad.c` et certaines versions initiales contiennent "
            "des erreurs volontaires. Ils sont analysés, et leurs diagnostics sont conservés."
        ),
        (
            "Un diagnostic de style n'est pas une erreur de compilation ; une alerte statique "
            "peut aussi être un faux positif. Le mode normal produit le rapport sans bloquer "
            "la génération du PDF ; `--strict` renvoie 1 pour tout diagnostic."
        ),
        "",
        "## Résumé",
        "",
        "| Fichier | Type | Syntaxe/compilation | Contrôles signalés (style compris) |",
        "| --- | --- | --- | ---: |", 
    ])
    groupes: dict[Path, list[Controle]] = {f: [] for f in fichiers}
    for item in controles:
        groupes[item.fichier].append(item)
    for fichier, resultats in groupes.items():
        nom = fichier.relative_to(dossier).as_posix()
        etiquette = "version pédagogique" if fichier.name in VERSIONS_DE_DEMONSTRATION else "programme"
        principal = next((c for c in resultats if c.categorie in {"syntaxe", "compilation"}), None)
        etat = "outil absent" if principal is None else ("OK" if principal.code == 0 else "ÉCHEC")
        if principal and principal.code == 0 and principal.anomalie:
            etat = "OK (avertissements)"
        lignes.append(
            f"| `{nom}` | {etiquette} | {etat} | "
            f"{sum(c.anomalie for c in resultats)}/{len(resultats)} |"
        )

    lignes.extend([
        "",
        (
            "À lire : `ex4_bad.c` échoue normalement à la compilation (pointeurs de fonctions "
            "incompatibles). `ex3_faulty.c` est aussi volontairement fautif ; cppcheck y "
            "relève notamment des déréférencements possibles de pointeurs nuls."
        ),
        (
            "Les variantes `ex6_initial.c` et `ex6_sigaction.c` peuvent lire hors du tableau "
            "à l'exécution. L'absence d'alerte statique à cet endroit ne prouve pas leur sûreté."
        ),
        "",
        "## Détails",
        "",
    ])
    for fichier, resultats in groupes.items():
        nom = fichier.relative_to(dossier).as_posix()
        lignes.append(f"### `{nom}`")
        lignes.append("")
        if not resultats:
            lignes.append("Aucun outil de contrôle disponible pour ce fichier.")
            lignes.append("")
            continue
        for item in resultats:
            etat = "diagnostics" if item.anomalie else "aucun diagnostic"
            lignes.append(f"- **{item.outil}** ({item.categorie}) : {etat}, code `{item.code}`.")
            if item.anomalie:
                lignes.append("")
                lignes.append("```text")
                lignes.append(item.sortie.strip() or f"Retour non nul : {item.code}")
                lignes.append("```")
        lignes.append("")
    return "\n".join(lignes).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyse statique de tous les fichiers C, Python et shell du dossier TD2."
    )
    parser.add_argument("--root", type=Path, default=BASE)
    parser.add_argument("--output", type=Path, default=BASE / "rapport_lint.md")
    parser.add_argument("--strict", action="store_true",
                        help="Code de sortie 1 si un diagnostic est détecté, même volontaire.")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Dossier introuvable : {root}")
    outils = {nom: executable(nom) for nom in (
        "gcc", "cppcheck", "clang-tidy", "clang-format", "bash", "shellcheck", "ruff"
    )}
    fichiers = sources(root)
    manquants = []
    if any(f.suffix == ".c" for f in fichiers) and not outils["gcc"]:
        manquants.append("gcc")
    if any(f.suffix == ".sh" for f in fichiers) and not outils["bash"]:
        manquants.append("bash")
    controles = [resultat for fichier in fichiers for resultat in controles_pour(fichier, outils)]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendre_rapport(root, fichiers, controles, outils), encoding="utf-8")
    signales = sum(c.anomalie for c in controles)
    print(f"Lint : {len(fichiers)} sources, {len(controles)} contrôles, {signales} avec diagnostics.")
    print(f"Rapport : {output}")
    if manquants:
        print(f"Contrôles essentiels absents : {', '.join(manquants)}", file=sys.stderr)
        return 2
    return 1 if args.strict and signales else 0


if __name__ == "__main__":
    raise SystemExit(main())
