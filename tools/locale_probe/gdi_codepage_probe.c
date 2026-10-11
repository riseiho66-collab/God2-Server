#include <windows.h>
#include <stdio.h>
#include <stdint.h>

static uint64_t raster(HDC dc, const char *ansi, const wchar_t *wide, int count) {
    uint64_t hash = UINT64_C(14695981039346656037);
    int x, y;
    PatBlt(dc, 0, 0, 200, 60, WHITENESS);
    if (ansi) TextOutA(dc, 4, 4, ansi, count);
    else TextOutW(dc, 4, 4, wide, count);
    for (y = 0; y < 60; ++y) for (x = 0; x < 200; ++x) {
        hash ^= GetPixel(dc, x, y);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

int main(int argc, char **argv) {
    static const char gbk[] = "\xbc\xf2\xcc\xe5\xd6\xd0\xce\xc4";
    static const wchar_t correct[] = L"\x7b80\x4f53\x4e2d\x6587";
    static const wchar_t wrong[] = L"\x6f60\x6781\x7b22\x6045";
    HDC dc;
    HBITMAP bitmap, previous_bitmap;
    HFONT font, previous_font;
    FILE *output;
    uint64_t ansi_hash, correct_hash, wrong_hash;
    if (argc != 2) return 2;
    dc = CreateCompatibleDC(NULL);
    bitmap = CreateBitmap(200, 60, 1, 32, NULL);
    font = CreateFontW(24, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, 0, 0, L"Microsoft YaHei");
    if (!dc || !bitmap || !font) return 3;
    previous_bitmap = (HBITMAP) SelectObject(dc, bitmap);
    previous_font = (HFONT) SelectObject(dc, font);
    SetTextColor(dc, RGB(0, 0, 0));
    SetBkColor(dc, RGB(255, 255, 255));
    ansi_hash = raster(dc, gbk, NULL, 8);
    correct_hash = raster(dc, NULL, correct, 4);
    wrong_hash = raster(dc, NULL, wrong, 4);
    output = fopen(argv[1], "wb");
    if (!output) return 4;
    fprintf(output, "GetACP=%lu\nTextOutA=%016llx\nTextOutW_CP936=%016llx\nTextOutW_CP950=%016llx\n",
        (unsigned long) GetACP(), (unsigned long long) ansi_hash,
        (unsigned long long) correct_hash, (unsigned long long) wrong_hash);
    fclose(output);
    SelectObject(dc, previous_font);
    SelectObject(dc, previous_bitmap);
    DeleteObject(font);
    DeleteObject(bitmap);
    DeleteDC(dc);
    return 0;
}
