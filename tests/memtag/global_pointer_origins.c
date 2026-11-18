/* Each relocation names the original object, including a legal one-past value. */
_Alignas(16) unsigned char first[16] = {11};
_Alignas(16) unsigned char second[16] = {22};
unsigned char *volatile origins[6] = {
    first, first + 15, first + 16, second, second + 15, second + 16,
};
