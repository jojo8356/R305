#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define NB_BLOCS 6000

int main(void)
{
    int i;
    char *bloc[NB_BLOCS];

    for (i = 0; i < NB_BLOCS; i++) {
        bloc[i] = malloc(1024 * 1024);
    }

    printf("allocation : %d blocs de 1 Mo\n", i);
    sleep(5);
    return 0;
}
