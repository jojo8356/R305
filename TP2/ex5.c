#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

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
