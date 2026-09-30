package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000.\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u0010\u001a\b\u0012\u0004\u0012\u00020\u00120\u00112\u0006\u0010\u0013\u001a\u00020\u00052\b\u0010\u0014\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0015R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\rR\u000e\u0010\u000e\u001a\u00020\u000fX\u0082\u0004¢\u0006\u0002\n\u0000¨\u0006\u0016"}, d2 = {"Lcom/Gayxx/GaybbExtractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "abyssExtractor", "Lcom/Gayxx/AbyssExtractor;", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class GaybbExtractor extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Gaybb";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://gaybb.net";
    private final boolean requiresReferer = true;

    @org.jetbrains.annotations.NotNull
    private final com.Gayxx.AbyssExtractor abyssExtractor = new com.Gayxx.AbyssExtractor();

    /* JADX INFO: renamed from: com.Gayxx.GaybbExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.GaybbExtractor", f = "Extractor.kt", i = {0, 0, 1, 1, 1, 1}, l = {444, 448}, m = "getUrl", n = {"url", "referer", "url", "referer", "response", "iframeUrl"}, nl = {445, -1}, s = {"L$0", "L$1", "L$0", "L$1", "L$2", "L$3"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.GaybbExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.GaybbExtractor.this.getUrl(null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getName() {
        return this.name;
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public boolean getRequiresReferer() {
        return this.requiresReferer;
    }

    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gayxx.GaybbExtractor.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        com.Gayxx.GaybbExtractor.AnonymousClass1 anonymousClass12;
        java.lang.String url2;
        java.lang.String referer2;
        java.lang.String iframeUrl;
        if (continuation instanceof com.Gayxx.GaybbExtractor.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.GaybbExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Gayxx.GaybbExtractor.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.lang.String mainUrl = getMainUrl();
                anonymousClass1.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass1.label = 1;
                com.Gayxx.GaybbExtractor.AnonymousClass1 anonymousClass13 = anonymousClass1;
                obj = coroutine_suspended;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, mainUrl, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4090, (java.lang.Object) null);
                anonymousClass12 = anonymousClass13;
                if ($result == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                break;
            case 1:
                referer2 = (java.lang.String) anonymousClass1.L$1;
                url2 = (java.lang.String) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                anonymousClass12 = anonymousClass1;
                break;
            case 2:
                kotlin.ResultKt.throwOnFailure($result);
                return $result;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) $result;
        org.jsoup.nodes.Element elementSelectFirst = response.getDocument().selectFirst("iframe[src]");
        if (elementSelectFirst == null || (iframeUrl = elementSelectFirst.attr("src")) == null) {
            return kotlin.collections.CollectionsKt.emptyList();
        }
        com.Gayxx.AbyssExtractor abyssExtractor = this.abyssExtractor;
        java.lang.String mainUrl2 = getMainUrl();
        anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
        anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
        anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeUrl);
        anonymousClass12.label = 2;
        java.lang.Object url3 = abyssExtractor.getUrl(iframeUrl, mainUrl2, anonymousClass12);
        return url3 == obj ? obj : url3;
    }
}
