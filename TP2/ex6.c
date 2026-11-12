#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

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
