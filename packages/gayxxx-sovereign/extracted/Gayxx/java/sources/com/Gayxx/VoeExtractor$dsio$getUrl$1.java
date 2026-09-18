package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.VoeExtractor$dsio", f = "Extractor.kt", i = {0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {72, 78, 92}, m = "getUrl", n = {"url", "referer", "url", "referer", "response0", "passMd5Path", "token", "md5Url", "url", "referer", "response0", "passMd5Path", "token", "md5Url", "res", "videoData", "randomStr", "link", "quality"}, nl = {74, 79, 91}, s = {"L$0", "L$1", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10"}, v = 2)
final class VoeExtractor$dsio$getUrl$1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
    java.lang.Object L$0;
    java.lang.Object L$1;
    java.lang.Object L$10;
    java.lang.Object L$2;
    java.lang.Object L$3;
    java.lang.Object L$4;
    java.lang.Object L$5;
    java.lang.Object L$6;
    java.lang.Object L$7;
    java.lang.Object L$8;
    java.lang.Object L$9;
    int label;
    /* synthetic */ java.lang.Object result;
    final /* synthetic */ com.Gayxx.VoeExtractor.dsio this$0;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    VoeExtractor$dsio$getUrl$1(com.Gayxx.VoeExtractor.dsio dsioVar, kotlin.coroutines.Continuation<? super com.Gayxx.VoeExtractor$dsio$getUrl$1> continuation) {
        super(continuation);
        this.this$0 = dsioVar;
    }

    @org.jetbrains.annotations.Nullable
    public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
        this.result = obj;
        this.label |= Integer.MIN_VALUE;
        return this.this$0.getUrl(null, null, (kotlin.coroutines.Continuation) this);
    }
}
