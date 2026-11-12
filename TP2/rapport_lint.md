# Rapport de lint — R3.05

Date : 2026-10-02 08:32 CEST. Sources examinées : **18**.

Les programmes ne sont pas exécutés : GCC, cppcheck, clang-tidy, ShellCheck et Ruff effectuent uniquement des contrôles statiques.

## Outils

- `gcc` : disponible.
- `cppcheck` : non installé.
- `clang-tidy` : non installé.
- `clang-format` : non installé.
- `bash` : disponible.
- `shellcheck` : non installé.
- `ruff` : non installé.

Si nécessaire : `sudo apt install cppcheck clang-tidy clang-format shellcheck` et `python3 -m pip install ruff`.

Les fichiers `*_faulty.c`, `*_bad.c` et certaines versions initiales contiennent des erreurs volontaires. Ils sont analysés, et leurs diagnostics sont conservés.
Un diagnostic de style n'est pas une erreur de compilation ; une alerte statique peut aussi être un faux positif. Le mode normal produit le rapport sans bloquer la génération du PDF ; `--strict` renvoie 1 pour tout diagnostic.

## Résumé

| Fichier | Type | Syntaxe/compilation | Contrôles signalés (style compris) |
| --- | --- | --- | ---: |
| `collecter_preuves.sh` | programme | OK | 0/1 |
| `convertir_pdf.py` | programme | OK | 0/1 |
| `ex2.c` | programme | OK | 0/1 |
| `ex2_alloc.c` | programme | OK | 0/1 |
| `ex2_original.c` | version pédagogique | OK (avertissements) | 1/1 |
| `ex3.c` | programme | OK | 0/1 |
| `ex3_faulty.c` | version pédagogique | OK | 0/1 |
| `ex4.c` | programme | OK | 0/1 |
| `ex4_bad.c` | version pédagogique | ÉCHEC | 1/1 |
| `ex4_initial.c` | programme | OK | 0/1 |
| `ex5.c` | programme | OK | 0/1 |
| `ex6.c` | programme | OK | 0/1 |
| `ex6_guarded.c` | programme | OK | 0/1 |
| `ex6_initial.c` | version pédagogique | OK | 0/1 |
| `ex6_sigaction.c` | version pédagogique | OK | 0/1 |
| `ex7.c` | programme | OK | 0/1 |
| `lint_programmes.py` | programme | OK | 0/1 |
| `test_ex2_c.sh` | programme | OK | 0/1 |

À lire : `ex4_bad.c` échoue normalement à la compilation (pointeurs de fonctions incompatibles). `ex3_faulty.c` est aussi volontairement fautif ; cppcheck y relève notamment des déréférencements possibles de pointeurs nuls.
Les variantes `ex6_initial.c` et `ex6_sigaction.c` peuvent lire hors du tableau à l'exécution. L'absence d'alerte statique à cet endroit ne prouve pas leur sûreté.

## Détails

### `collecter_preuves.sh`

- **bash -n** (syntaxe) : aucun diagnostic, code `0`.

### `convertir_pdf.py`

- **ast.parse** (syntaxe) : aucun diagnostic, code `0`.

### `ex2.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex2_alloc.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex2_original.c`

- **GCC + -fanalyzer** (compilation) : diagnostics, code `0`.

```text
/home/pj509414/Documents/R305/TP2/ex2_original.c: In function 'main':
/home/pj509414/Documents/R305/TP2/ex2_original.c:10:11: warning: variable 'bloc' set but not used [-Wunused-but-set-variable]
   10 |     char *bloc[NB_BLOCS];
      |           ^~~~
```

### `ex3.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex3_faulty.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex4.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex4_bad.c`

- **GCC + -fanalyzer** (compilation) : diagnostics, code `1`.

```text
/home/pj509414/Documents/R305/TP2/ex4_bad.c: In function 'main':
/home/pj509414/Documents/R305/TP2/ex4_bad.c:24:11: error: assignment to 'void (*)(int)' from incompatible pointer type 'int (*)(void)' [-Wincompatible-pointer-types]
   24 |     fptr1 = SaisirEntier;
      |           ^
```

### `ex4_initial.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex5.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex6.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex6_guarded.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex6_initial.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex6_sigaction.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `ex7.c`

- **GCC + -fanalyzer** (compilation) : aucun diagnostic, code `0`.

### `lint_programmes.py`

- **ast.parse** (syntaxe) : aucun diagnostic, code `0`.

### `test_ex2_c.sh`

- **bash -n** (syntaxe) : aucun diagnostic, code `0`.
