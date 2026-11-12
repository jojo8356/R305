#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <sys/wait.h>

int main(void) {
    pid_t pid_fils;
    pid_fils = fork();
    if (pid_fils == -1) {
        printf("fork impossible code d'erreur %d\n", errno);
        return 1;
    }
    else if (pid_fils == 0) { /* processus fils */
        printf("Fils : mon PID=%d, PPID pere=%d\n",
        getpid(), getppid());
        sleep(10);
        return 0;
    }
    else { /* processus pere */
        wait(NULL);
        printf("Pere : mon PID=%d, PPID pere=%d\n",
        getpid(), getppid());
        printf("Pere : PID fils=%d\n", pid_fils);
        return 0;
    }
}
