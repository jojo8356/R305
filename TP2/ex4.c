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

void ExecAfficherEntier(void (*argfptr)(int), int n)
{
    printf("ExecAfficherEntier : appel de argfptr\n");
    argfptr(n);
}

int main(void)
{
    void (*fptr1)(int);
    int (*fptr2)(void);
    int entier;

    fptr1 = AfficherEntier;
    fptr2 = SaisirEntier;
    entier = fptr2();
    ExecAfficherEntier(fptr1, entier);
    return 0;
}
