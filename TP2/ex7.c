#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

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
