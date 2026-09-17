package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\u0014\n\u0000\n\u0002\u0010 \n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\u001a\u001e\u0010\u0000\u001a\b\u0012\u0004\u0012\u00020\u00020\u00012\u0006\u0010\u0003\u001a\u00020\u00022\b\b\u0002\u0010\u0004\u001a\u00020\u0005¨\u0006\u0006"}, d2 = {"reconstructDataUris", "", "", "text", "maxCollect", "", "Jayboys"}, k = 2, mv = {2, 3, 0}, xi = 48)
public final class ExtractorsKt {
    public static /* synthetic */ java.util.List reconstructDataUris$default(java.lang.String str, int i, int i2, java.lang.Object obj) {
        if ((i2 & 2) != 0) {
            i = 300000;
        }
        return reconstructDataUris(str, i);
    }

    @org.jetbrains.annotations.NotNull
    public static final java.util.List<java.lang.String> reconstructDataUris(@org.jetbrains.annotations.NotNull java.lang.String text, int maxCollect) {
        java.util.List out = new java.util.ArrayList();
        int idx = kotlin.text.StringsKt.indexOf$default(text, "data:video/", 0, false, 6, (java.lang.Object) null);
        while (idx >= 0) {
            int baseStart = kotlin.text.StringsKt.indexOf$default(text, "base64,", idx, false, 4, (java.lang.Object) null);
            if (baseStart < 0) {
                break;
            }
            java.lang.String prefix = text.substring(idx, baseStart + 7);
            kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(prefix, "substring(...)");
            java.lang.StringBuilder sb = new java.lang.StringBuilder();
            int i = baseStart + 7;
            int collected = 0;
            while (true) {
                if (i >= text.length() || collected >= maxCollect) {
                    break;
                }
                char c = text.charAt(i);
                if (!('A' <= c && c < '[')) {
                    if (!('a' <= c && c < '{')) {
                        if (!('0' <= c && c < ':') && c != '+' && c != '/' && c != '=') {
                            if (c == '\'' || c == '\"' || c == '+' || kotlin.text.CharsKt.isWhitespace(c)) {
                                i++;
                            } else {
                                if (((c == '<' || c == '>') && collected > 8) || (!java.lang.Character.isLetterOrDigit(c) && collected > 8)) {
                                    break;
                                }
                                i++;
                            }
                        }
                    }
                }
                sb.append(c);
                collected++;
                i++;
            }
            if (sb.length() > 0) {
                out.add(prefix + ((java.lang.Object) sb));
            }
            int nextFrom = i <= idx ? idx + 1 : i;
            idx = kotlin.text.StringsKt.indexOf$default(text, "data:video/", nextFrom, false, 4, (java.lang.Object) null);
        }
        return out;
    }
}
