#define _POSIX_C_SOURCE 200809L
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>

void gestionnaire1(int sig);
int k = 0, l = 0;
char buf[100] = {0};

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

    for (k = 0;; k++) {
        l = buf[k];
    }
    return EXIT_SUCCESS;
}

void gestionnaire1(int sig)
{
    printf("Signal violation memoire %d pour k = %d\n", sig, k);
    exit(EXIT_FAILURE);
}
