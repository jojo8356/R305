#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <signal.h>

void gestionnaire1(int sig);
int k = 0, l = 0;
char buf[100] = {0};

int main(void)
{
    if (signal(SIGSEGV, gestionnaire1) == SIG_ERR) {
        printf("Erreur signal");
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
