#define _GNU_SOURCE
#include <signal.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <unistd.h>

#define TAILLE_BUF 100

static volatile sig_atomic_t k = 0;
static volatile sig_atomic_t pid_fils = -1;

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
    if (sigaction(SIGSEGV, &action, NULL) == -1) {
        perror("sigaction");
        return EXIT_FAILURE;
    }

    long taille_page = sysconf(_SC_PAGESIZE);
    if (taille_page < TAILLE_BUF) {
        fprintf(stderr, "Taille de page invalide\n");
        return EXIT_FAILURE;
    }
    size_t page = (size_t)taille_page;
    void *zone = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (zone == MAP_FAILED) {
        perror("mmap");
        return EXIT_FAILURE;
    }
    if (mprotect((char *)zone + page, page, PROT_NONE) == -1) {
        perror("mprotect");
        munmap(zone, 2 * page);
        return EXIT_FAILURE;
    }
    volatile unsigned char *buf = (volatile unsigned char *)zone + page - TAILLE_BUF;

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork");
        munmap(zone, 2 * page);
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
        volatile unsigned char l = buf[k];
        (void)l;
    }
}
