package com.iGay69;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u0011\u001a\n\u0012\u0004\u0012\u00020\u0013\u0018\u00010\u00122\u0006\u0010\u0014\u001a\u00020\u00052\b\u0010\u0015\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0016R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u0017"}, d2 = {"Lcom/iGay69/Lulustream;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "iGay69"}, k = 1, mv = {2, 3, 0}, xi = 48)
public class Lulustream extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Lulustream";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://lulustream.com";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.iGay69.Lulustream$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.iGay69.Lulustream", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {59, 64}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response", "extractedpack", "unPacked", "link", "$i$a$-let-Lulustream$getUrl$2", "$i$a$-let-Lulustream$getUrl$2$1"}, nl = {60, 63}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "I$0", "I$1"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.iGay69.Lulustream.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.iGay69.Lulustream.getUrl$suspendImpl(com.iGay69.Lulustream.this, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.Nullable
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String str, @org.jetbrains.annotations.Nullable java.lang.String str2, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        return getUrl$suspendImpl(this, str, str2, continuation);
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getName() {
        return this.name;
    }

    public void setName(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.name = str;
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public void setMainUrl(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.mainUrl = str;
    }

    public boolean getRequiresReferer() {
        return this.requiresReferer;
    }

    /* JADX WARN: Removed duplicated region for block: B:20:0x00cf  */
    /* JADX WARN: Removed duplicated region for block: B:21:0x00d4  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.iGay69.Lulustream $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.iGay69.Lulustream.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        java.lang.Object obj2;
        com.iGay69.Lulustream $this2;
        java.lang.String url2;
        java.lang.String referer2;
        java.lang.String unPacked;
        kotlin.text.MatchResult matchResultFind$default;
        java.util.List groupValues;
        java.lang.String link;
        java.lang.Object objNewExtractorLink;
        if (continuation instanceof com.iGay69.Lulustream.AnonymousClass1) {
            anonymousClass1 = (com.iGay69.Lulustream.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.iGay69.Lulustream.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.lang.String mainUrl = $this.getMainUrl();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = referer;
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                i = 1;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, mainUrl, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4090, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                org.jsoup.nodes.Document response = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementSelectFirst = response.selectFirst("script:containsData(function(p,a,c,k,e,d))");
                java.lang.String extractedpack = java.lang.String.valueOf(elementSelectFirst == null ? elementSelectFirst.data() : null);
                unPacked = new com.lagradost.cloudstream3.utils.JsUnpacker(extractedpack).unpack();
                if (unPacked != null || (matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("sources:\\[\\{file:\"(.*?)\""), unPacked, 0, 2, (java.lang.Object) null)) == null || (groupValues = matchResultFind$default.getGroupValues()) == null || (link = (java.lang.String) groupValues.get(i)) == null) {
                    return null;
                }
                java.lang.String name = $this2.getName();
                java.lang.String name2 = $this2.getName();
                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                com.iGay69.Lulustream$getUrl$2$1$1 lulustream$getUrl$2$1$1 = new com.iGay69.Lulustream$getUrl$2$1$1(referer2, null);
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(extractedpack);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unPacked);
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                anonymousClass12.I$0 = 0;
                anonymousClass12.I$1 = 0;
                anonymousClass12.label = 2;
                objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, name2, link, infer_type, lulustream$getUrl$2$1$1, anonymousClass12);
                if (objNewExtractorLink == obj) {
                    return obj;
                }
                return kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
            case 1:
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$1;
                com.iGay69.Lulustream $this3 = (com.iGay69.Lulustream) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this3;
                obj = coroutine_suspended;
                referer2 = referer3;
                url2 = url3;
                i = 1;
                obj2 = $result;
                org.jsoup.nodes.Document response2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementSelectFirst2 = response2.selectFirst("script:containsData(function(p,a,c,k,e,d))");
                java.lang.String extractedpack2 = java.lang.String.valueOf(elementSelectFirst2 == null ? elementSelectFirst2.data() : null);
                unPacked = new com.lagradost.cloudstream3.utils.JsUnpacker(extractedpack2).unpack();
                if (unPacked != null) {
                }
                return null;
            case 2:
                int i2 = anonymousClass12.I$1;
                int i3 = anonymousClass12.I$0;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
                return kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
