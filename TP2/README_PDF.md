# Export PDF et contrôle du code — R3.05

Le fichier `reponses.md` reste la source du devoir. `convertir_pdf.py` crée `reponses.pdf` avec WeasyPrint et la feuille Markdown **officielle GitHub Primer** (`assets/primer-markdown.css`, `@primer/css` 22.3.2, licence MIT incluse). Des ajustements limités sont appliqués pour l'impression A4 ; la coloration du code est ajoutée avec Pygments.

Un bloc de code qui tient sur une page n'est pas coupé : s'il manque de place, il passe entier à la page suivante avec sa phrase d'introduction. Les programmes trop longs pour une seule page commencent sur une page neuve puis continuent sur les pages suivantes. Dans `reponses.md`, `...` abrège les en-têtes déjà cités ou les fonctions inchangées ; les fichiers `.c` restent complets et doivent être utilisés pour compiler.

## Installer les dépendances

Depuis le dossier `R305/TD2` :

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-pdf.txt ruff
```

Si WeasyPrint signale l'absence de bibliothèques système sous Debian/Ubuntu :

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

Pour utiliser **tous** les outils du linter sur les programmes C et les scripts shell :

```bash
sudo apt install gcc cppcheck clang-tidy clang-format shellcheck
```

Sans ces outils facultatifs, le rapport indique lesquels manquent ; GCC, `bash -n` et l'analyse syntaxique Python contrôlent les fichiers correspondants lorsqu'ils sont disponibles.

## Générer le PDF et le rapport

```bash
python convertir_pdf.py
```

Cela génère `reponses.pdf` et `rapport_lint.md`. Le linter parcourt **tous les `.c`, `.py` et `.sh` du dossier**, y compris ses exemples volontairement fautifs. Il vérifie la compilation/syntaxe et, si les outils sont présents, utilise aussi GCC `-fanalyzer`, cppcheck en mode exhaustif, clang-tidy, clang-format, Ruff et ShellCheck. Il n'exécute **aucun** des programmes C.

Les métadonnées PDF sont : **Title** `TP3`, **Author** `Johan Polsinelli`, **Subject** `Mémoire virtuelle, processus et signaux sous Linux`, **Keywords** `TP3, R3.05, Linux, C, mémoire virtuelle, processus, signaux, Valgrind`, **Creator** `Convertisseur Markdown vers PDF` et **Producer** `Unknown`. Les dates de création et de modification sont celles de l'export, avec le fuseau Europe/Paris. Les données XMP reprennent l'auteur et les dates et indiquent `application/pdf` comme format. Le titre affiché sur la première page reste `R3.05`. Les options `--titre-pdf`, `--auteur-pdf`, `--sujet-pdf`, `--mots-cles-pdf` et `--producteur-pdf` permettent de changer ces valeurs.

Options utiles :

```bash
python convertir_pdf.py --source autre.md --sortie autre.pdf --sans-lint
python lint_programmes.py --strict
```

`--strict` renvoie le code 1 dès qu'un diagnostic est présent, y compris une différence de mise en forme ou une erreur voulue. Le fonctionnement normal laisse produire le PDF même si des erreurs attendues sont signalées. En particulier, `ex4_bad.c` ne compile pas : c'est la version incorrecte demandée par l'exercice. Le style du code C vérifié par clang-format est défini dans `.clang-format`, sans modifier les sources.
