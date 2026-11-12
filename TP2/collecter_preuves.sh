#!/usr/bin/env bash
set -u
set -o pipefail

rapide=0
case "${1:-}" in
    '') ;;
    --quick) rapide=1 ;;
    -h|--help)
        printf 'Usage : bash %s [--quick]\n' "$0"
        printf '%s\n' 'Sans option : teste 2d si la RAM le permet et attend 30 s pour l alarme.'
        printf '%s\n' '--quick : saute le test 2d et teste l alarme en 1 s.'
        exit 0 ;;
    *) printf 'Option inconnue : %s\n' "$1" >&2; exit 1 ;;
esac
if (( $# > 1 )); then
    printf 'Une seule option est acceptee.\n' >&2
    exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$script_dir" || exit 1
sources=(ex2.c ex3_faulty.c ex3.c ex4_bad.c ex4.c ex5.c ex6.c ex7.c)
manquants=()
for src in "${sources[@]}"; do
    [[ -f "$src" ]] || manquants+=("$src")
done
if (( ${#manquants[@]} != 0 )); then
    printf 'Sources manquantes dans %s :\n' "$script_dir" >&2
    printf '  %s\n' "${manquants[@]}" >&2
    printf 'Copiez ces fichiers avec le script, puis relancez-le.\n' >&2
    exit 1
fi
for outil in gcc timeout ps awk sed mkfifo tee; do
    if ! command -v "$outil" >/dev/null 2>&1; then
        printf 'Outil manquant : %s\n' "$outil" >&2
        exit 1
    fi
done

mkdir -p preuves
rapport="$script_dir/preuves/preuves_$(date +%Y%m%d-%H%M%S).txt"
exec > >(tee "$rapport") 2>&1
ulimit -c 0
travail=$(mktemp -d)
proprietaire=$BASHPID
pid_actif=0
pid_programme_actif=0
pid_fils_actif=0
nettoyer() {
    [[ $BASHPID == "$proprietaire" ]] || return 0
    for p in "$pid_fils_actif" "$pid_programme_actif" "$pid_actif"; do
        if (( p > 0 )); then
            kill -CONT "$p" 2>/dev/null || true
            kill -TERM "$p" 2>/dev/null || true
            kill -KILL "$p" 2>/dev/null || true
        fi
    done
    if (( pid_actif > 0 )); then
        wait "$pid_actif" 2>/dev/null || true
    fi
    rm -rf -- "$travail"
}
trap nettoyer EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

titre() { printf '\n========== %s ==========\n' "$*"; }
verifier_pid() {
    ps -o pid,ppid,stat,comm -p "$1" || true
}

printf 'R3.05 - releve du %s\n' "$(date '+%F %T')"
printf 'Dossier : %s\n' "$script_dir"
printf 'Compilateur : %s\n' "$(gcc --version | head -n 1)"
printf 'Mode : %s\n' "$(if (( rapide )); then echo rapide; else echo complet; fi)"
printf 'Journal : %s\n' "$rapport"

titre 'Exercice 2d - ecriture de 6000 blocs'
if (( rapide )); then
    echo 'Test complet saute avec --quick.'
else
    dispo_kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
    besoin_kb=$((6000 * 1024))
    marge_kb=$((2 * 1024 * 1024))
    possible=1
    printf 'MemAvailable = %s kB ; besoin = %s kB + marge = %s kB.\n' \
        "$dispo_kb" "$besoin_kb" "$marge_kb"
    if (( dispo_kb < besoin_kb + marge_kb )); then
        echo 'Test saute : RAM disponible insuffisante pour un essai prudent.'
        possible=0
    fi
    if [[ -r /sys/fs/cgroup/memory.max && -r /sys/fs/cgroup/memory.current ]]; then
        limite=$(cat /sys/fs/cgroup/memory.max)
        courant=$(cat /sys/fs/cgroup/memory.current)
        if [[ "$limite" =~ ^[0-9]+$ && "$courant" =~ ^[0-9]+$ ]]; then
            reste=$((limite - courant))
            printf 'Memoire encore autorisee par le cgroup : %s octets.\n' "$reste"
            if (( reste < (besoin_kb + marge_kb) * 1024 )); then
                echo 'Test saute : limite du cgroup trop basse.'
                possible=0
            fi
        fi
    fi
    if (( possible )); then
        if gcc -std=c11 -O0 -g -Wall -Wextra ex2.c -o "$travail/ex2.out"; then
            echo 'Lancement sous timeout 120 s. Ce test ecrit environ 6 Gio de RAM.'
            timeout -k 2s 120s "$travail/ex2.out" >"$travail/ex2d.log" 2>&1
            code=$?
            cat "$travail/ex2d.log"
            printf 'Code de retour ex2d : %d\n' "$code"
            if ! grep -q 'allocation : 6000 blocs' "$travail/ex2d.log"; then
                echo 'ATTENTION : le programme n a pas confirme 6000 allocations.'
            fi
        else
            echo 'Compilation ex2.c echouee : test saute.'
        fi
    fi
fi

titre 'Exercice 3 - version erronée'
if gcc -std=c11 -O0 -g -Wall -Wextra ex3_faulty.c -o "$travail/ex3_faulty.out"; then
    timeout -k 1s 5s "$travail/ex3_faulty.out" lol
    printf 'Code de retour du programme erroné : %d\n' "$?"
    if command -v valgrind >/dev/null 2>&1; then
        valgrind --leak-check=full --error-exitcode=42 "$travail/ex3_faulty.out" lol
        printf 'Code de retour Valgrind avant correction : %d\n' "$?"
    else
        echo 'VALGRIND ABSENT : installer avec sudo apt install valgrind puis relancer.'
    fi
else
    echo 'Compilation ex3_faulty.c echouee.'
fi

titre 'Exercice 3 - version corrigée'
if gcc -std=c11 -O0 -g -Wall -Wextra ex3.c -o "$travail/ex3.out"; then
    "$travail/ex3.out" lol
    printf 'Code de retour du programme corrigé : %d\n' "$?"
    if command -v valgrind >/dev/null 2>&1; then
        valgrind --leak-check=full --error-exitcode=42 "$travail/ex3.out" lol
        printf 'Code de retour Valgrind apres correction : %d\n' "$?"
    fi
else
    echo 'Compilation ex3.c echouee.'
fi

titre 'Exercice 4 - erreur de compilation attendue'
gcc -std=c11 -O0 -g -Wall -Wextra ex4_bad.c -o "$travail/ex4_bad.out"
printf 'Code de compilation de la version erronée : %d\n' "$?"
echo 'La version erronée n est pas exécutée (pointeur de fonction non initialisé).'

titre 'Exercice 4 - version finale, saisie 11'
if gcc -std=c11 -O0 -g -Wall -Wextra ex4.c -o "$travail/ex4.out"; then
    echo 'Entree fournie au programme : 11'
    printf '11\n' | "$travail/ex4.out"
    printf 'Code de retour du programme final : %d\n' "${PIPESTATUS[1]}"
else
    echo 'Compilation ex4.c echouee.'
fi

titre 'Exercice 5a - SIGTERM, puis SIGKILL'
sleep 50 & pid_actif=$!
printf 'PID sleep SIGTERM : %d\n' "$pid_actif"
kill -SIGTERM "$pid_actif"
wait "$pid_actif"
printf 'Code wait apres SIGTERM : %d\n' "$?"
pid_actif=0
sleep 50 & pid_actif=$!
printf 'PID sleep SIGKILL : %d\n' "$pid_actif"
kill -SIGKILL "$pid_actif"
wait "$pid_actif"
printf 'Code wait apres SIGKILL : %d\n' "$?"
pid_actif=0

titre 'Exercice 5b - programme mykill'
if gcc -std=c11 -O0 -g -Wall -Wextra ex5.c -o "$travail/mykill"; then
    sleep 50 & pid_actif=$!
    printf 'PID sleep de test : %d\n' "$pid_actif"
    printf 'n\n' | "$travail/mykill" "$pid_actif"
    printf 'Réponse n : code %d ; processus encore présent : ' "${PIPESTATUS[1]}"
    if kill -0 "$pid_actif" 2>/dev/null; then echo oui; else echo non; fi
    printf 'x\n' | "$travail/mykill" "$pid_actif"
    printf 'Réponse invalide x : code %d ; processus encore présent : ' "${PIPESTATUS[1]}"
    if kill -0 "$pid_actif" 2>/dev/null; then echo oui; else echo non; fi
    printf 'o\n' | "$travail/mykill" "$pid_actif"
    printf 'Réponse o : code %d\n' "${PIPESTATUS[1]}"
    wait "$pid_actif"
    printf 'Code wait du sleep après o : %d\n' "$?"
    pid_actif=0
    "$travail/mykill" SIGTERM 277
    printf 'Arguments SIGTERM 277 : code %d\n' "$?"
    printf 'o\n' | "$travail/mykill" 99999999
    printf 'PID inexistant : code %d\n' "${PIPESTATUS[1]}"
else
    echo 'Compilation ex5.c echouee.'
fi

titre 'Exercice 6 - sigaction, pere et fils'
if gcc -std=c11 -O0 -g -Wall -Wextra ex6.c -o "$travail/ex6.out"; then
    timeout -k 2s 5s "$travail/ex6.out" >"$travail/ex6.log" 2>&1
    code=$?
    cat "$travail/ex6.log"
    printf 'Code de retour ex6 : %d (124 = timeout)\n' "$code"
    fils=$(sed -n 's/.*fils PID \([0-9][0-9]*\).*/\1/p' "$travail/ex6.log" | tail -n 1)
    if [[ -n "$fils" ]]; then
        printf 'Statut du fils %s apres la sortie du pere :\n' "$fils"
        verifier_pid "$fils"
        comm=$(ps -o comm= -p "$fils" 2>/dev/null | tr -d '[:space:]')
        if [[ "$comm" == ex6.out ]]; then
            echo 'Nettoyage d un fils encore actif.'
            kill -KILL "$fils" 2>/dev/null || true
        fi
    fi
else
    echo 'Compilation ex6.c echouee.'
fi

titre 'Exercice 7 - statut du fils avant s, apres s et apres r'
if gcc -std=c11 -O0 -g -Wall -Wextra ex7.c -o "$travail/ex7.out"; then
    mkfifo "$travail/commandes_ex7"
    "$travail/ex7.out" <"$travail/commandes_ex7" >"$travail/ex7_menu.log" 2>&1 &
    pid_actif=$!
    exec 3>"$travail/commandes_ex7"
    fils=''
    for ((n=0; n<100; n++)); do
        fils=$(sed -n 's/.*fils PID : \([0-9][0-9]*\).*/\1/p' "$travail/ex7_menu.log" | head -n 1)
        [[ -n "$fils" ]] && break
        sleep 0.05
    done
    if [[ -z "$fils" ]]; then
        echo 'Impossible de lire le PID du fils : suite des tests 7 sautée.'
        exec 3>&-
        kill -KILL "$pid_actif" 2>/dev/null || true
        wait "$pid_actif" 2>/dev/null || true
        pid_actif=0
    else
        pid_fils_actif=$fils
        printf 'Père PID : %d ; fils PID : %d\n' "$pid_actif" "$fils"
        echo 'Avant s :'
        verifier_pid "$fils"
        printf 's\n' >&3
        for ((n=0; n<40; n++)); do
            etat=$(ps -o stat= -p "$fils" 2>/dev/null | tr -d '[:space:]')
            [[ "$etat" == T* ]] && break
            sleep 0.05
        done
        echo 'Après s (T attendu) :'
        verifier_pid "$fils"
        printf 'r\n' >&3
        for ((n=0; n<40; n++)); do
            etat=$(ps -o stat= -p "$fils" 2>/dev/null | tr -d '[:space:]')
            [[ -n "$etat" && "$etat" != T* ]] && break
            sleep 0.05
        done
        echo 'Après r (R attendu) :'
        verifier_pid "$fils"
        printf 'e\n' >&3
        for ((n=0; n<40; n++)); do
            ps -p "$fils" >/dev/null 2>&1 || break
            sleep 0.05
        done
        echo 'Après e (fils absent attendu) :'
        verifier_pid "$fils"
        printf 'q\n' >&3
        exec 3>&-
        wait "$pid_actif"
        printf 'Code de retour du père après q : %d\n' "$?"
        pid_actif=0
        pid_fils_actif=0
        echo 'Sortie du programme (SIGCHLD et menu) :'
        cat "$travail/ex7_menu.log"
    fi

    titre 'Exercice 7 - q alors que le fils est actif'
    printf 'q\n' | timeout -k 2s 5s "$travail/ex7.out" >"$travail/ex7_q.log" 2>&1
    code=${PIPESTATUS[1]}
    cat "$travail/ex7_q.log"
    printf 'Code de retour avec q direct : %d\n' "$code"
    fils=$(sed -n 's/.*fils PID : \([0-9][0-9]*\).*/\1/p' "$travail/ex7_q.log" | head -n 1)
    if [[ -n "$fils" ]]; then
        echo 'Statut du fils après q (absence attendue) :'
        verifier_pid "$fils"
    fi

    titre 'Exercice 7 - alarme'
    delai=30
    if (( rapide )); then delai=1; fi
    if gcc -std=c11 -O0 -g -Wall -Wextra -DDELAI_ALARME="$delai" \
        ex7.c -o "$travail/ex7_alarme.out"; then
        printf 'Attente sans commande : %d secondes (code normal : 30).\n' "$delai"
        mkfifo "$travail/attente_alarme"
        debut=$(date +%s)
        timeout -k 2s "$((delai + 5))s" "$travail/ex7_alarme.out" \
            <"$travail/attente_alarme" >"$travail/ex7_alarme.log" 2>&1 &
        pid_actif=$!
        exec 4>"$travail/attente_alarme"
        pere=''
        fils=''
        for ((n=0; n<60; n++)); do
            pere=$(sed -n 's/.*PID : \([0-9][0-9]*\), fils PID :.*/\1/p' "$travail/ex7_alarme.log" | head -n 1)
            fils=$(sed -n 's/.*fils PID : \([0-9][0-9]*\).*/\1/p' "$travail/ex7_alarme.log" | head -n 1)
            [[ -n "$pere" && -n "$fils" ]] && break
            sleep 0.05
        done
        if [[ -n "$pere" && -n "$fils" ]]; then
            pid_programme_actif=$pere
            pid_fils_actif=$fils
        fi
        wait "$pid_actif"
        code=$?
        pid_actif=0
        exec 4>&-
        fin=$(date +%s)
        cat "$travail/ex7_alarme.log"
        printf 'Temps écoulé : %d s ; code de retour du père : %d\n' \
            "$((fin - debut))" "$code"
        if [[ -n "$fils" ]]; then
            echo 'Statut du fils après SIGALRM (absence attendue) :'
            verifier_pid "$fils"
            comm=$(ps -o comm= -p "$fils" 2>/dev/null | tr -d '[:space:]')
            if [[ "$comm" == ex7_alarme.out ]]; then
                echo 'Nettoyage d un fils resté actif après le test.'
                kill -KILL "$fils" 2>/dev/null || true
            fi
        fi
        pid_programme_actif=0
        pid_fils_actif=0
    fi
else
    echo 'Compilation ex7.c echouee.'
fi

titre 'Fin du relevé'
printf 'Journal complet : %s\n' "$rapport"
printf 'Envoyez ce fichier texte ou copiez sa sortie dans la conversation.\n'
