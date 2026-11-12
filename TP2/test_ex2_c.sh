#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_c=${1:-"$script_dir/ex2_alloc.c"}

if [[ ! -f "$source_c" ]]; then
    printf 'Fichier introuvable : %s\n' "$source_c" >&2
    printf 'Placez ex2_alloc.c dans le meme dossier que ce script, ou passez son chemin en argument.\n' >&2
    exit 1
fi
if ! command -v gcc >/dev/null 2>&1; then
    printf 'gcc est necessaire pour lancer ce test.\n' >&2
    exit 1
fi
if grep -Eq 'memset[[:space:]]*\(' "$source_c"; then
    printf 'Utilisez la version sans memset (question c), et non celle de la question d.\n' >&2
    exit 1
fi

tmpdir=$(mktemp -d)
pid=''
nettoyer() {
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill -CONT "$pid" 2>/dev/null || true
        kill -TERM "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    fi
    rm -rf -- "$tmpdir"
}
trap nettoyer EXIT

printf 'Compilation : %s\n' "$source_c"
gcc -std=c11 -O0 -Wall -Wextra "$source_c" -o "$tmpdir/ex2_alloc.out"

if command -v stdbuf >/dev/null 2>&1; then
    stdbuf -oL "$tmpdir/ex2_alloc.out" >"$tmpdir/sortie.txt" 2>&1 &
else
    "$tmpdir/ex2_alloc.out" >"$tmpdir/sortie.txt" 2>&1 &
fi
pid=$!

message_trouve=0
for ((n = 0; n < 200; n++)); do
    if grep -q '^allocation :' "$tmpdir/sortie.txt"; then
        message_trouve=1
        break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
        printf 'Le programme s est termine avant la mesure. Sa sortie :\n' >&2
        cat "$tmpdir/sortie.txt" >&2
        exit 1
    fi
    sleep 0.05
done
if (( message_trouve == 0 )); then
    printf 'Aucun message allocation apres 10 secondes. Verifiez le sleep(5) et l affichage du programme.\n' >&2
    cat "$tmpdir/sortie.txt" >&2
    exit 1
fi

if ! kill -STOP "$pid" 2>/dev/null; then
    printf 'Le programme s est termine avant de pouvoir etre suspendu.\n' >&2
    cat "$tmpdir/sortie.txt" >&2
    exit 1
fi

printf '\n=== Programme suspendu (PID %s) ===\n' "$pid"
cat "$tmpdir/sortie.txt"
printf '\n=== Memoire du processus (/proc/%s/status) ===\n' "$pid"
grep -E '^(Name|State|Pid|VmSize|VmRSS|VmData|VmSwap):' "/proc/$pid/status"

if command -v top >/dev/null 2>&1; then
    printf '\n=== top -b -n 1 -p %s ===\n' "$pid"
    top -b -n 1 -p "$pid" || true
fi

printf '\n=== Memoire physique et swap de la machine ===\n'
grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo
free -h

mem_total=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
awk -v total="$mem_total" '
    /^VmSize:/ { virt = $2 }
    /^VmRSS:/ { ram = $2 }
    END {
        if (total > 0 && virt > 0) {
            printf "\nComparaison : virtuel = %.2f Gio ; RAM totale = %.2f Gio ; RES = %.1f Mio\n", \
                virt / 1048576, total / 1048576, ram / 1024
        }
    }
' "/proc/$pid/status"

printf '\nReprise du programme...\n'
kill -CONT "$pid"
if wait "$pid"; then
    code=0
else
    code=$?
fi
pid=''
printf 'Code de retour du programme : %s\n' "$code"
printf 'Vous pouvez me transmettre toute cette sortie.\n'
