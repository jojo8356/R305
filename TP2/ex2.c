#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef NB_BLOCS
#define NB_BLOCS 6000
#endif
#define TAILLE_BLOC (1024u * 1024u)

int main(void)
{
    char *bloc[NB_BLOCS];
    int i;
    int nb_alloc = 0;
    int ecriture_ok = 1;
    void *ret;

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

    printf("Ecriture dans les blocs\nPassage en memoire physique\n");
    for (i = 0; i < nb_alloc; i++) {
        ret = memset(bloc[i], 1, TAILLE_BLOC);
        if (i % 10 == 0) {
            printf("%d ", i);
            fflush(stdout);
        }
        if (ret == NULL) {
            fprintf(stderr, "Echec pour i = %d\n", i);
            ecriture_ok = 0;
            break;
        }
    }
    putchar('\n');

    for (i = 0; i < nb_alloc; i++) {
        free(bloc[i]);
    }
    return (nb_alloc == NB_BLOCS && ecriture_ok) ? EXIT_SUCCESS : EXIT_FAILURE;
}
