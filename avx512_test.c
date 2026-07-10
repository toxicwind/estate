
  #include <immintrin.h>
  #include <stdio.h>
  int main() {
    __m512i a = _mm512_set1_epi32(1);
    __m512i b = _mm512_set1_epi32(2);
    __m512i c = _mm512_add_epi32(a, b);
    int vals[16];
    _mm512_storeu_si512(vals, c);
    printf("AVX512 add result: %d\n", vals[0]);
    return 0;
  }