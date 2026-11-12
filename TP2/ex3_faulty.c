#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main(int argc, char *argv[])
{
    char *chaine;
    char *chaine2;
    int i;

    if (argc != 2) {
        printf("il faut 1 argument\n");
        return 1;
    }

    printf("Allocation, copie, affichage, liberation chaine 1\n");
    chaine = malloc(strlen(argv[1]));
    strcpy(chaine, argv[1]);
    printf("Chaine : %s\n", chaine);
    free(chaine);

    printf("Allocation, copie, affichage, liberation chaine 2\n");
    chaine2 = malloc(10);
    for (i = 0; i < 10; i++) {
        *chaine2 = 'a';
        chaine2++;
    }
    free(chaine2);
    return 0;
}
