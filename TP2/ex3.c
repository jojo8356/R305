#include <stdio.h>
#include <stdlib.h>
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
