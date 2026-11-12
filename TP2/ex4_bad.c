#include <stdlib.h>
#include <stdio.h>

int SaisirEntier(void)
{
    int n;
    printf("SaisirEntier : veuillez entrer un entier : ");
    scanf("%d", &n);
    return n;
}

void AfficherEntier(int n)
{
    printf("AfficherEntier : son argument vaut %d\n", n);
}

int main(void)
{
    void (*fptr1)(int);
    int (*fptr2)(void);
    int entier;

    fptr1 = AfficherEntier;
    fptr1 = SaisirEntier;
    entier = fptr2();
    fptr1(entier);
    return 0;
}
