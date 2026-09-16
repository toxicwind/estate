package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u000e\u001a\n\u0012\u0004\u0012\u00020\u0010\u0018\u00010\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0014"}, d2 = {"Lcom/Jayboys/yi069website;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public class yi069website extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "yi069website";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://1069.website";

    /* JADX INFO: renamed from: com.Jayboys.yi069website$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.yi069website", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {41, 57}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response", "document", "firstDownloadLink", "videoId", "domain", "finalLink"}, nl = {42, 56}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        java.lang.Object L$7;
        java.lang.Object L$8;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Jayboys.yi069website.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.yi069website.getUrl$suspendImpl(com.Jayboys.yi069website.this, null, null, (kotlin.coroutines.Continuation) this);
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

    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public boolean getRequiresReferer() {
        return this.requiresReferer;
    }

    /* JADX WARN: Removed duplicated region for block: B:20:0x00cf A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:21:0x00d0  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Jayboys.yi069website $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Jayboys.yi069website.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        java.lang.Object obj2;
        com.Jayboys.yi069website $this2;
        java.lang.String url2;
        java.lang.String referer2;
        java.lang.String firstDownloadLink;
        java.lang.Object objNewExtractorLink;
        if (continuation instanceof com.Jayboys.yi069website.AnonymousClass1) {
            anonymousClass1 = (com.Jayboys.yi069website.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Jayboys.yi069website.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = url;
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Document document = response.getDocument();
                firstDownloadLink = document.select("div.download-button-wrapper a:first-child").attr("href");
                if (!kotlin.text.StringsKt.isBlank(firstDownloadLink)) {
                    return null;
                }
                java.lang.String videoId = kotlin.text.StringsKt.substringAfterLast$default(firstDownloadLink, "/", (java.lang.String) null, 2, (java.lang.Object) null);
                if (kotlin.text.StringsKt.isBlank(videoId)) {
                    return null;
                }
                java.lang.String finalLink = "https://domain.com/bkg/" + videoId;
                java.lang.String domain = $this2.getName();
                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                com.Jayboys.yi069website.AnonymousClass2 anonymousClass2 = new com.Jayboys.yi069website.AnonymousClass2(url2, null);
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(firstDownloadLink);
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoId);
                anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable("https://domain.com/bkg");
                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(finalLink);
                anonymousClass12.label = 2;
                objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(domain, "yi069video", finalLink, infer_type, anonymousClass2, anonymousClass12);
                return objNewExtractorLink == obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
            case 1:
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$1;
                com.Jayboys.yi069website $this3 = (com.Jayboys.yi069website) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this3;
                obj = coroutine_suspended;
                referer2 = referer3;
                url2 = url3;
                obj2 = $result;
                com.lagradost.nicehttp.NiceResponse response2 = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Document document2 = response2.getDocument();
                firstDownloadLink = document2.select("div.download-button-wrapper a:first-child").attr("href");
                if (!kotlin.text.StringsKt.isBlank(firstDownloadLink)) {
                }
                break;
            case 2:
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.yi069website$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.yi069website$getUrl$2", f = "Extractors.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $url;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, kotlin.coroutines.Continuation<? super com.Jayboys.yi069website.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$url = str;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Jayboys.yi069website.AnonymousClass2(this.$url, continuation);
            anonymousClass2.L$0 = obj;
            return anonymousClass2;
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
                    $this$newExtractorLink.setReferer(this.$url);
                    $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.Qualities.Unknown.getValue());
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }
}
