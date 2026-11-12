# R3.05

Johan Polsinelli — BUT2 Informatique

## Exercice 1

J'ai créé le dossier `R305`, puis le dossier `TD2` à l'intérieur avec la commande `mkdir -p R305/TD2`.

### a. Mémoire centrale

La commande `free -h` indique que la machine dispose de 31 Gio de RAM : 3,8 Gio sont utilisés, 25 Gio sont libres et 27 Gio sont disponibles. Elle dispose également de 63 Gio de swap, qui n'était pas utilisé lors du relevé.

Concernant la mémoire partagée (606 Mio), elle correspond notamment aux zones utilisées par plusieurs processus et à `tmpfs`. Les tampons et le cache (2,7 Gio) servent à garder des données en mémoire afin d'accélérer les accès aux fichiers. Une grande partie de cette mémoire peut être récupérée si nécessaire.

Dans le fichier `/proc/meminfo`, j'ai relevé les valeurs suivantes :

- `MemTotal` : 32 534 076 kB, soit environ 31 Gio ;
- `VmallocTotal` : 34 359 738 367 kB, soit environ 32 Tio ;
- `VmallocUsed` : 75 540 kB, soit environ 74 Mio ;
- `VmallocChunk` : 0 kB.

En comparant les deux premières valeurs, `VmallocTotal` est environ 1 056 fois plus grand que `MemTotal`. Cette valeur correspond à un espace virtuel dont peut se servir le noyau, et non à de la RAM physique. Le `0` de `VmallocChunk` ne veut pas nécessairement dire que cet espace est plein : ce champ n'est plus renseigné de façon utile sur certains noyaux.

### b. Mémoire du processus bash

Pour bash, j'ai relevé le PID **5428** et le PPID **5418**.

La commande `top` indique `VIRT = 50804` kB, `RES = 37852` kB, `SHR = 4868` kB et `%MEM = 0,1`. Dans `/proc/5428/status`, `VmSize = 50804 kB` correspond à la mémoire virtuelle, tandis que `VmRSS = 37852 kB` correspond à la mémoire présente en RAM. Je relève aussi `VmData = 33012 kB`, `VmStk = 132 kB` et `VmSwap = 0 kB`.

Avec `/proc/5428/maps` et `pmap 5428`, on retrouve bash, ses bibliothèques, le chargeur de programme, le tas (`[heap]`, 32820 K) ainsi que la pile (`[stack]`, 132 K). Les lettres `r`, `w` et `x` indiquent respectivement la lecture, l'écriture et l'exécution. Bash apparaît sur plusieurs lignes parce que les parties du programme n'ont pas toutes les mêmes droits.

### c. Mémoire du fichier exécutable

La commande `size -G ex4.out` donne :

- `text` : 604 octets pour le code ;
- `data` : 2 094 octets pour les données globales ou statiques initialisées ;
- `bss` : 8 octets pour les données globales ou statiques non initialisées ou mises à zéro ;
- `total` : 2 706 octets.

Ces valeurs ne comprennent pas la pile ni le tas.

## Exercice 2

### a. Programme initial

Le programme demande 6 000 blocs de `1024 * 1024` octets, soit 6 000 Mio (environ 5,86 Gio). Il conserve l'adresse de chaque bloc, affiche le nombre de blocs demandés, attend 5 secondes, puis se termine. À ce stade, il n'écrit pas dans les blocs : la mémoire est réservée dans l'espace virtuel, mais elle n'est pas entièrement utilisée en RAM. Le programme initial ne vérifie pas si `malloc` échoue.

### b. Vérification de `malloc`

Pour les questions b et c, j'ai modifié le programme pour vérifier chaque allocation :

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define NB_BLOCS 6000
#define TAILLE_BLOC (1024 * 1024)

int main(void)
{
    char *bloc[NB_BLOCS];
    int i;
    int nb_alloc = 0;

    for (i = 0; i < NB_BLOCS; i++) {
        bloc[i] = malloc(TAILLE_BLOC);
        if (bloc[i] == NULL) {
            fprintf(stderr, "Echec pour i = %d (allocation n° %d)\n", i, i + 1);
            break;
        }
        nb_alloc++;
    }

    printf("allocation : %d blocs de 1 Mo\n", nb_alloc);
    fflush(stdout);
    sleep(5);

    for (i = 0; i < nb_alloc; i++) {
        free(bloc[i]);
    }
    return nb_alloc == NB_BLOCS ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

Si `malloc` renvoie `NULL`, le message d'échec est écrit sur la sortie d'erreur et la boucle s'arrête. `nb_alloc` correspond au nombre de blocs qui ont pu être alloués. Il sert aussi à ne libérer que ces blocs.

### c. Mémoire virtuelle et mémoire physique

J'ai lancé le test avec :

```bash
./test_ex2_c.sh
```

Le script compile le programme, attend que les 6 000 blocs soient alloués, puis le suspend pendant les 5 secondes d'attente. Il utilise le signal `STOP`, qui suspend le processus comme `Ctrl+Z`.

Pour le processus de PID **12838**, j'ai relevé :

- `VmSize` (`VIRT`) : **6 170 576 kB**, soit **5,88 Gio** de mémoire virtuelle ;
- `VmRSS` (`RES`) : **25 688 kB**, soit **25,1 Mio** présents en RAM ;
- `VmData` : 6 168 228 kB ;
- `VmSwap` : 0 kB.

La machine possède **32 534 076 kB** de RAM physique, soit **31,03 Gio**. Les 5,88 Gio de mémoire virtuelle du programme sont donc inférieurs à la RAM totale. La mémoire réellement présente en RAM reste beaucoup plus faible, car le programme n'a pas encore écrit dans les blocs. Après la reprise, le programme s'est terminé avec le code de retour **0**.

### d. Écriture dans les blocs

J'ajoute `#include <string.h>` avec les autres en-têtes pour utiliser `memset`. Après `sleep(5)` et avant la boucle qui libère les blocs, j'ajoute uniquement ces lignes :

```c
printf("Ecriture dans les blocs\nPassage en memoire physique\n");
for (i = 0; i < nb_alloc; i++) {
    void *ret = memset(bloc[i], 1, TAILLE_BLOC);
    if (i % 10 == 0) {
        printf("%d ", i);
        fflush(stdout);
    }
    if (ret == NULL) {
        fprintf(stderr, "Echec pour i = %d\n", i);
        break;
    }
}
putchar('\n');
```

Pour compiler et exécuter cette version :

```bash
gcc -std=c11 -O0 -Wall -Wextra ex2.c -o ex2.out
./ex2.out
```

La boucle utilise `nb_alloc` pour ne pas écrire dans un bloc dont l'allocation a échoué. Avec `memset`, le programme écrit réellement dans les blocs. Lors du test, `MemAvailable` valait **29 077 800 kB**, soit environ **27,7 Gio**. Les **6 000 blocs** ont été alloués, puis la progression s'est affichée de `0` à `5990` par pas de 10. Le programme s'est terminé normalement avec le **code 0**. La boucle `free` libère les blocs. Le test `ret == NULL` ne détecterait pas un manque de mémoire : pour un pointeur valide, `memset` renvoie ce même pointeur.

## Exercice 3

### a. Les deux erreurs

La première allocation réserve `strlen(argv[1])` octets. Il manque un octet pour le caractère de fin de chaîne `\0`. La copie avec `strcpy` écrit donc en dehors du bloc. L'affichage de la chaîne peut aussi lire en dehors du bloc.

Dans la seconde partie, `chaine2++` déplace le pointeur après chaque écriture. À la fin, `free(chaine2)` ne reçoit plus l'adresse renvoyée par `malloc`. La libération est incorrecte et les 10 octets alloués ne sont pas récupérés par cet appel.

### b. Exécution de la version initiale

J'ai compilé et exécuté le programme de l'énoncé avec :

```bash
gcc -std=c11 -O0 -g -Wall -Wextra ex3_faulty.c -o ex3_faulty.out
./ex3_faulty.out lol
```

Lors du relevé, le programme s'est arrêté avec `free(): invalid pointer` et le **code de retour 134**. La première erreur ne s'affiche pas forcément lors d'une exécution normale, mais elle est quand même présente.

### c. Vérification avec Valgrind et correction

Si Valgrind n'est pas installé, la commande `sudo apt install valgrind` permet de l'ajouter sur un système Debian ou Ubuntu. J'ai ensuite utilisé :

```bash
valgrind --leak-check=full --error-exitcode=42 ./ex3_faulty.out lol
```

Valgrind signale `Invalid write of size 1` et `Invalid read of size 1` pour le premier bloc : l'octet `\0` est écrit puis lu hors de la zone allouée. Il signale aussi `Invalid free` pour le second bloc et **10 octets perdus**. Le relevé indique **4 erreurs dans 4 contextes** et Valgrind renvoie le **code 42** avec l'option `--error-exitcode=42`.

J'alloue un octet de plus pour la première chaîne. Pour le second bloc, j'utilise l'indice `i` afin de ne pas modifier l'adresse à libérer. Dans les extraits suivants, `...` remplace les en-têtes déjà utilisés ou les fonctions inchangées. Les fichiers `.c` restent complets.

```c
...
#include <string.h>

int main(int argc, char *argv[])
{
    char *chaine;
    char *chaine2;
    int i;

    if (argc != 2) {
        fprintf(stderr, "il faut 1 argument\n");
        return EXIT_FAILURE;
    }

    printf("Allocation, copie, affichage, liberation chaine 1\n");
    chaine = malloc(strlen(argv[1]) + 1);
    if (chaine == NULL) {
        perror("malloc chaine");
        return EXIT_FAILURE;
    }
    strcpy(chaine, argv[1]);
    printf("Chaine : %s\n", chaine);
    free(chaine);

    printf("Allocation, remplissage, liberation chaine 2\n");
    chaine2 = malloc(10);
    if (chaine2 == NULL) {
        perror("malloc chaine2");
        return EXIT_FAILURE;
    }
    for (i = 0; i < 10; i++) {
        chaine2[i] = 'a';
    }
    free(chaine2);
    return EXIT_SUCCESS;
}
```

J'ai recompilé puis relancé le programme et Valgrind :

```bash
gcc -std=c11 -O0 -g -Wall -Wextra ex3.c -o ex3.out
./ex3.out lol
valgrind --leak-check=full --error-exitcode=42 ./ex3.out lol
```

Le programme affiche `Chaine : lol` et se termine avec le **code 0**. Valgrind indique **`ERROR SUMMARY: 0 errors`**, **0 octet encore alloué à la fin**, et renvoie également le **code 0**. Le second bloc n'est pas utilisé comme une chaîne de caractères, donc il n'a pas besoin d'un caractère `\0`.

## Exercice 4

### a. Pointeurs de fonctions

`fptr1` est un pointeur vers une fonction qui reçoit un entier et ne renvoie rien. Il pointe vers `AfficherEntier`. `fptr2` est un pointeur vers une fonction qui ne reçoit aucun argument et renvoie un entier. Il pointe vers `SaisirEntier`.

Le programme demande un entier avec `fptr2()`, puis l'affiche avec `fptr1(entier)`. Pour l'entrée `11`, l'affichage indique que l'argument vaut 11.

### b. Affectation incorrecte

J'ai remplacé `fptr2 = SaisirEntier;` par `fptr1 = SaisirEntier;`. Les types ne correspondent pas : `fptr1` attend une fonction de type `void (int)`, alors que `SaisirEntier` est de type `int (void)`.

Contrairement à ce qu'indique l'énoncé, **GCC 14.2 refuse la compilation** à cause des types incompatibles. Le code de compilation obtenu est **1** :

```bash
gcc -std=c11 -O0 -g -Wall -Wextra ex4_bad.c -o ex4_bad.out
```

La version incorrecte n'a donc pas été exécutée. `fptr2` n'a pas reçu d'adresse : si la compilation était forcée, l'appel `fptr2()` utiliserait un pointeur non initialisé et son comportement ne serait pas défini.

### c. Pointeur de fonction en paramètre

J'ai ajouté une fonction qui reçoit le pointeur `argfptr` ainsi qu'un entier. Elle transmet ensuite cet entier à la fonction pointée :

```c
...
int SaisirEntier(void) { ... }
void AfficherEntier(int n) { ... }

void ExecAfficherEntier(void (*argfptr)(int), int n)
{
    printf("ExecAfficherEntier : appel de argfptr\n");
    argfptr(n);
}

int main(void)
{
    void (*fptr1)(int);
    int (*fptr2)(void);
    int entier;

    fptr1 = AfficherEntier;
    fptr2 = SaisirEntier;
    entier = fptr2();
    ExecAfficherEntier(fptr1, entier);
    return 0;
}
```

Dans `main`, l'appel direct `fptr1(entier)` est remplacé par `ExecAfficherEntier(fptr1, entier)`. J'ai compilé et exécuté le programme avec :

```bash
gcc -std=c11 -O0 -Wall -Wextra ex4.c -o ex4.out
./ex4.out
```

Le script a transmis l'entier `11`. Le programme a affiché :

```text
SaisirEntier : veuillez entrer un entier : ExecAfficherEntier : appel de argfptr
AfficherEntier : son argument vaut 11
```

Le **code de retour est 0**. Le `11` n'apparaît pas après l'invite parce que l'entrée a été transmise au programme, et non saisie au clavier.

## Exercice 5

### a. Signaux SIGTERM et SIGKILL

J'ai lancé un processus `sleep` en arrière-plan et j'ai utilisé son PID pour lui envoyer les deux signaux :

```bash
sleep 50 & pid=$!
kill -SIGTERM "$pid"
wait "$pid"

sleep 50 & pid=$!
kill -SIGKILL "$pid"
wait "$pid"
```

Dans le relevé, `sleep 50` avait le PID **14008** pour `SIGTERM` et **14009** pour `SIGKILL`. La commande `wait` a renvoyé **143** après `SIGTERM` et **137** après `SIGKILL`. Le code correspond à 128 plus le numéro du signal : 15 pour `SIGTERM`, 9 pour `SIGKILL`.

`SIGTERM` demande au processus de se terminer. Il peut intercepter ce signal pour libérer ses ressources avant de s'arrêter, ou choisir de l'ignorer. `SIGKILL` arrête le processus de force : il ne peut pas être intercepté ou ignoré.

### b. Programme mykill

Le programme reçoit uniquement le PID en argument. Il demande ensuite une confirmation avant d'envoyer `SIGTERM` :

```c
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <sys/types.h>
...

int main(int argc, char *argv[])
{
    char *fin;
    long valeur;
    pid_t pid;
    char reponse[32];

    if (argc != 2) {
        fprintf(stderr, "Usage : %s PID\n", argv[0]);
        return 1;
    }

    errno = 0;
    valeur = strtol(argv[1], &fin, 10);
    if (errno == ERANGE || fin == argv[1] || *fin != '\0' ||
        valeur <= 0 || valeur > INT_MAX) {
        fprintf(stderr, "Usage : %s PID\n", argv[0]);
        return 1;
    }
    pid = (pid_t)valeur;

    printf("Etes vous sur de vouloir tuer le processus ? (o / n) ");
    fflush(stdout);
    if (fgets(reponse, sizeof reponse, stdin) == NULL) {
        fprintf(stderr, "Reponse invalide : saisir o ou n\n");
        return 1;
    }
    reponse[strcspn(reponse, "\r\n")] = '\0';

    if (strcmp(reponse, "n") == 0) {
        return 0;
    }
    if (strcmp(reponse, "o") != 0) {
        fprintf(stderr, "Reponse invalide : saisir o ou n\n");
        return 1;
    }

    if (kill(pid, SIGTERM) == -1) {
        perror("Erreur kill");
        return 1;
    }
    return 0;
}
```

`strtol` vérifie que l'argument est un PID positif. Cela évite d'envoyer un signal à un groupe de processus en passant `0` ou `-1`. Le programme ne vérifie pas à l'avance si le PID existe : si `kill` échoue, il affiche l'erreur. Seules les réponses exactes `o` et `n` sont acceptées. La réponse `n` et un `kill` réussi renvoient 0 ; une autre réponse ou un échec renvoie 1.

J'ai compilé et vérifié le programme avec un processus `sleep` de test :

```bash
gcc -std=c11 -O0 -Wall -Wextra ex5.c -o mykill
sleep 50 & pid=$!
printf 'n\n' | ./mykill "$pid"
printf 'x\n' | ./mykill "$pid"
printf 'o\n' | ./mykill "$pid"
```

Dans le test, la réponse `n` a renvoyé **0** et laissé le `sleep` actif. La réponse invalide `x` a renvoyé **1** sans l'arrêter. La réponse `o` a renvoyé **0** et le `sleep` s'est terminé avec le code **143**. Deux arguments (`SIGTERM 277`) ont affiché l'usage et renvoyé **1**. Un PID inexistant a produit `Erreur kill` et le code **1**.

La commande `./mykill SIGTERM 277` est incorrecte car le programme attend un seul argument, le PID. `Ctrl+C` envoie `SIGINT` au processus au premier plan et `Ctrl+Z` envoie `SIGTSTP` pour le suspendre.

## Exercice 6

### a. Programme initial

Le programme installe `gestionnaire1` pour le signal `SIGSEGV`. Ensuite, la boucle lit les cases de `buf` en augmentant `k`. Le tableau contient 100 cases : à partir de `k = 100`, la lecture sort du tableau. Si elle atteint une zone mémoire interdite, le noyau envoie `SIGSEGV` et le gestionnaire affiche le signal et la valeur de `k`, puis termine le processus.

La lecture hors du tableau est un comportement non défini. Un `SIGSEGV` n'est donc pas garanti dès `k = 100` : le programme peut continuer à lire plus loin avant de recevoir le signal, ou se comporter autrement.

### b. Remplacement de `signal` par `sigaction`

J'ai créé une structure `sigaction`, placé `gestionnaire1` dans `sa_handler`, vidé le masque avec `sigemptyset`, puis utilisé `sigaction(SIGSEGV, &action, NULL)`. Le programme enregistre ainsi le même gestionnaire avec l'interface demandée. La version complète de la question c reprend cette modification.

### c. Processus fils et gestion du signal

`fork()` crée le fils. Celui-ci effectue le calcul `j = 2 * i` tant que `i < 100000`. J'ai laissé une attente de 2 secondes après la boucle pour qu'il soit encore actif lorsque le père reçoit le signal. Le père poursuit la lecture de `buf`.

Quand le père reçoit `SIGSEGV`, le gestionnaire affiche le signal, `k` et le PID du fils. Il envoie ensuite `SIGTERM` au fils et termine le père. J'utilise `write` et `_exit` dans le gestionnaire : `printf` et `exit`, présents dans le programme initial, ne sont pas sûrs dans ce contexte.

```c
#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
...

static volatile sig_atomic_t k = 0;
static volatile sig_atomic_t pid_fils = -1;
static volatile int l = 0;
static char buf[100] = {0};

static size_t ajouter_nombre(char *texte, size_t pos, unsigned int nombre)
{
    char chiffres[16];
    size_t n = 0;
    do {
        chiffres[n++] = (char)('0' + nombre % 10);
        nombre /= 10;
    } while (nombre != 0);
    while (n != 0) {
        texte[pos++] = chiffres[--n];
    }
    return pos;
}

static void gestionnaire1(int sig)
{
    char texte[96];
    size_t pos = 0;
    const char debut[] = "Signal violation memoire ";
    const char milieu[] = " pour k = ";
    const char fin[] = " ; arret du fils PID ";

    for (size_t i = 0; i < sizeof debut - 1; i++) {
        texte[pos++] = debut[i];
    }
    pos = ajouter_nombre(texte, pos, (unsigned int)sig);
    for (size_t i = 0; i < sizeof milieu - 1; i++) {
        texte[pos++] = milieu[i];
    }
    pos = ajouter_nombre(texte, pos, (unsigned int)k);
    for (size_t i = 0; i < sizeof fin - 1; i++) {
        texte[pos++] = fin[i];
    }
    if (pid_fils > 0) {
        pos = ajouter_nombre(texte, pos, (unsigned int)pid_fils);
    } else {
        texte[pos++] = '?';
    }
    texte[pos++] = '\n';
    (void)write(STDERR_FILENO, texte, pos);

    if (pid_fils > 0) {
        (void)kill((pid_t)pid_fils, SIGTERM);
    }
    _exit(EXIT_FAILURE);
}

int main(void)
{
    struct sigaction action = {0};
    action.sa_handler = gestionnaire1;
    sigemptyset(&action.sa_mask);
    action.sa_flags = 0;
    if (sigaction(SIGSEGV, &action, NULL) == -1) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return EXIT_FAILURE;
    }
    if (pid == 0) {
        volatile int j = 0;
        for (int i = 0; i < 100000; i++) {
            j = 2 * i;
        }
        (void)j;
        sleep(2);
        _exit(EXIT_SUCCESS);
    }

    pid_fils = (sig_atomic_t)pid;
    for (k = 0;; k++) {
        l = buf[k];
    }
}
```

Compilation et exécution :

```bash
gcc -std=c11 -O0 -g -Wall -Wextra ex6.c -o ex6.out
timeout 5s ./ex6.out
```

Lors du test, le père a affiché **`Signal violation memoire 11 pour k = 3936`** et l'arrêt du fils de PID **14032**. Le père a renvoyé le **code 1**, et `ps` ne montrait plus le fils après son arrêt. Le dépassement du tableau n'a donc pas provoqué le signal dès `k = 100` ; cette valeur dépend de la mémoire du processus. La commande `timeout` évite de laisser la boucle tourner si aucun `SIGSEGV` n'arrive.

## Exercice 7

### a. Commandes du père

Le fils effectue un calcul dans une boucle sans fin. Le père affiche un menu et envoie un signal au fils selon la lettre saisie :

- `s` : `SIGSTOP` arrête temporairement le fils ;
- `r` : `SIGCONT` reprend son exécution ;
- `e` : `SIGTERM` termine le fils, mais le père reste actif ;
- `q` : `SIGKILL` tue le fils, puis le père se termine.

Si le fils est déjà terminé après `e`, la commande `q` termine simplement le père.

### b. Gestion de SIGCHLD et SIGALRM

J'ai installé les deux gestionnaires avec `sigaction`. Lorsqu'un état du fils change, le père reçoit `SIGCHLD`. Le gestionnaire affiche « Signal SIGCHLD reçu », remet l'alarme à 30 secondes et laisse le père continuer. Sans l'option `SA_NOCLDSTOP`, les commandes `s` et `r` provoquent aussi ce signal. Les commandes `e` et `q` provoquent `SIGCHLD` quand elles terminent un fils encore actif ; avec `q`, le père peut toutefois se terminer avant que le message apparaisse.

Avant chaque saisie, le père lance `alarm(30)`. Si aucune commande n'arrive dans ce délai, le gestionnaire de `SIGALRM` envoie `SIGKILL` au fils et termine le père avec le code 1.

```c
#define _POSIX_C_SOURCE 200809L
#include <sys/wait.h>
...

#ifndef DELAI_ALARME
#define DELAI_ALARME 30
#endif

static volatile sig_atomic_t pid_fils = -1;

static void gerer_sigchld(int sig)
{
    (void)sig;
    int ancien_errno = errno;
    const char message[] = "Signal SIGCHLD reçu\n";
    (void)write(STDOUT_FILENO, message, sizeof message - 1);
    alarm(DELAI_ALARME);
    errno = ancien_errno;
}

static void gerer_sigalrm(int sig)
{
    (void)sig;
    const char message[] = "Temps écoulé : arrêt du fils\n";
    (void)write(STDERR_FILENO, message, sizeof message - 1);
    if (pid_fils > 0) {
        (void)kill((pid_t)pid_fils, SIGKILL);
    }
    _exit(EXIT_FAILURE);
}

static void attendre_fils(pid_t pid)
{
    int statut;
    while (waitpid(pid, &statut, 0) == -1) {
        if (errno == EINTR) {
            continue;
        }
        if (errno != ECHILD) {
            perror("waitpid");
        }
        break;
    }
}

static void terminer_fils(int sig)
{
    if (pid_fils <= 0) {
        return;
    }
    pid_t pid = (pid_t)pid_fils;
    if (sig == SIGTERM) {
        (void)kill(pid, SIGCONT);
    }
    if (kill(pid, sig) == -1 && errno != ESRCH) {
        perror("kill");
    }
    attendre_fils(pid);
    pid_fils = -1;
}

static void verifier_fils(void)
{
    if (pid_fils <= 0) {
        return;
    }
    int statut;
    pid_t resultat = waitpid((pid_t)pid_fils, &statut, WNOHANG);
    if (resultat > 0 || (resultat == -1 && errno == ECHILD)) {
        pid_fils = -1;
        puts("Le fils est terminé.");
    }
}

int main(void)
{
    struct sigaction action_chld = {0};
    struct sigaction action_alrm = {0};

    action_chld.sa_handler = gerer_sigchld;
    sigemptyset(&action_chld.sa_mask);
    action_chld.sa_flags = SA_RESTART;
    action_alrm.sa_handler = gerer_sigalrm;
    sigemptyset(&action_alrm.sa_mask);
    if (sigaction(SIGCHLD, &action_chld, NULL) == -1 ||
        sigaction(SIGALRM, &action_alrm, NULL) == -1) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        return EXIT_FAILURE;
    }
    if (pid == 0) {
        volatile unsigned long j = 0;
        for (unsigned long i = 0;; i++) {
            j = 2UL * i;
            (void)j;
        }
    }
    pid_fils = (sig_atomic_t)pid;
    printf("Père PID : %ld, fils PID : %ld\n", (long)getpid(), (long)pid);

    char ligne[64];
    for (;;) {
        verifier_fils();
        puts("s : stopper, r : reprendre, e : terminer le fils, q : quitter");
        printf("Commande : ");
        fflush(stdout);
        alarm(DELAI_ALARME);

        errno = 0;
        if (fgets(ligne, sizeof ligne, stdin) == NULL) {
            if (ferror(stdin) && errno == EINTR) {
                clearerr(stdin);
                continue;
            }
            alarm(0);
            terminer_fils(SIGKILL);
            return EXIT_SUCCESS;
        }

        verifier_fils();
        if (ligne[1] != '\n' && ligne[1] != '\0') {
            puts("Commande inconnue.");
            continue;
        }
        switch (ligne[0]) {
        case 's':
            if (pid_fils <= 0) {
                puts("Le fils est déjà terminé.");
            } else if (kill((pid_t)pid_fils, SIGSTOP) == -1) {
                perror("kill SIGSTOP");
            }
            break;
        case 'r':
            if (pid_fils <= 0) {
                puts("Le fils est déjà terminé.");
            } else if (kill((pid_t)pid_fils, SIGCONT) == -1) {
                perror("kill SIGCONT");
            }
            break;
        case 'e':
            if (pid_fils <= 0) {
                puts("Le fils est déjà terminé.");
            } else {
                terminer_fils(SIGTERM);
                puts("Le fils a été terminé. Le père reste actif.");
            }
            break;
        case 'q':
            alarm(0);
            terminer_fils(SIGKILL);
            return EXIT_SUCCESS;
        default:
            puts("Commande inconnue.");
            break;
        }
    }
}
```

Compilation et exécution :

```bash
gcc -std=c11 -O0 -Wall -Wextra ex7.c -o ex7.out
./ex7.out
```

Le programme affiche le PID du fils. Pour vérifier son état, j'ai utilisé `ps -o pid,ppid,stat,comm -p 14051`. Le fils de PID **14051** est passé de **`R+`** à **`T+`** après `s`, puis de nouveau à **`R+`** après `r`. Après `e`, il n'apparaissait plus dans `ps`, tandis que le père restait actif. La commande `q` a ensuite terminé le père avec le **code 0**.

J'ai également testé `q` lorsque le fils était encore actif : le fils de PID **14067** a disparu et le père a renvoyé **0**. Enfin, sans commande pendant **30 secondes**, le gestionnaire de `SIGALRM` a affiché `Temps écoulé : arrêt du fils`. Le fils de PID **14085** n'apparaissait plus dans `ps` et le père a renvoyé le **code 1**.


