package com.topHDgayporn;

/* JADX INFO: compiled from: topHDgayporn.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.topHDgayporn.topHDgayporn$loadLinks$7$1", f = "topHDgayporn.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
final class topHDgayporn$loadLinks$7$1 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
    final /* synthetic */ java.lang.String $data;
    final /* synthetic */ java.util.Map<java.lang.String, java.lang.String> $headers;
    final /* synthetic */ java.lang.String $url;
    private /* synthetic */ java.lang.Object L$0;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    topHDgayporn$loadLinks$7$1(java.lang.String str, java.lang.String str2, java.util.Map<java.lang.String, java.lang.String> map, kotlin.coroutines.Continuation<? super com.topHDgayporn.topHDgayporn$loadLinks$7$1> continuation) {
        super(2, continuation);
        this.$data = str;
        this.$url = str2;
        this.$headers = map;
    }

    public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
        kotlin.coroutines.Continuation<kotlin.Unit> tophdgayporn_loadlinks_7_1 = new com.topHDgayporn.topHDgayporn$loadLinks$7$1(this.$data, this.$url, this.$headers, continuation);
        tophdgayporn_loadlinks_7_1.L$0 = obj;
        return tophdgayporn_loadlinks_7_1;
    }

    public final java.lang.Object invoke(com.lagradost.cloudstream3.utils.ExtractorLink extractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return create(extractorLink, continuation).invokeSuspend(kotlin.Unit.INSTANCE);
    }

    public final java.lang.Object invokeSuspend(java.lang.Object $result) {
        com.lagradost.cloudstream3.utils.ExtractorLink $this$newExtractorLink = (com.lagradost.cloudstream3.utils.ExtractorLink) this.L$0;
        kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (this.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                $this$newExtractorLink.setReferer(this.$data);
                $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.ExtractorApiKt.getQualityFromName(this.$url));
                $this$newExtractorLink.setHeaders(this.$headers);
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
