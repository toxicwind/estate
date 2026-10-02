package com.Nurgay;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0005\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0011\u001a\u00020\u00052\u0006\u0010\u0012\u001a\u00020\u0005H\u0016J(\u0010\u0013\u001a\n\u0012\u0004\u0012\u00020\u0015\u0018\u00010\u00142\u0006\u0010\u0016\u001a\u00020\u00052\b\u0010\u0017\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0018R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u0019"}, d2 = {"Lcom/Nurgay/DoodLaExtractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getExtractorUrl", "id", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Nurgay"}, k = 1, mv = {2, 3, 0}, xi = 48)
public class DoodLaExtractor extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "DoodStream";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://dood.la";

    /* JADX INFO: renamed from: com.Nurgay.DoodLaExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.DoodLaExtractor", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {227, 237, 253}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response0", "host", "passPath", "md5Url", "$this", "url", "referer", "response0", "host", "passPath", "md5Url", "videoBase", "token", "randomStr", "trueUrl", "quality"}, nl = {230, 240, 252}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$10;
        java.lang.Object L$11;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Nurgay.DoodLaExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.DoodLaExtractor.getUrl$suspendImpl(com.Nurgay.DoodLaExtractor.this, null, null, (kotlin.coroutines.Continuation) this);
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

    @org.jetbrains.annotations.NotNull
    public java.lang.String getExtractorUrl(@org.jetbrains.annotations.NotNull java.lang.String id) {
        return getMainUrl() + "/d/" + id;
    }

    /* JADX WARN: Removed duplicated region for block: B:40:0x0226  */
    /* JADX WARN: Removed duplicated region for block: B:43:0x0298 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:44:0x0299  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Nurgay.DoodLaExtractor $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Nurgay.DoodLaExtractor.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        int i2;
        java.lang.String url2;
        java.lang.String referer2;
        java.lang.Object obj2;
        com.Nurgay.DoodLaExtractor $this2;
        kotlin.text.MatchResult matchResultFind$default;
        java.util.List groupValues;
        kotlin.text.MatchResult matchResultFind$default2;
        java.lang.String passPath;
        com.Nurgay.DoodLaExtractor $this3;
        java.lang.Object obj3;
        java.lang.String url3;
        java.lang.String url4;
        java.lang.String response0;
        java.lang.String referer3;
        java.lang.String response02;
        java.lang.Object objNewExtractorLink$default;
        java.util.List groupValues2;
        if (continuation instanceof com.Nurgay.DoodLaExtractor.AnonymousClass1) {
            anonymousClass1 = (com.Nurgay.DoodLaExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Nurgay.DoodLaExtractor.AnonymousClass1 anonymousClass12 = anonymousClass1;
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
                i = 0;
                i2 = 2;
                java.lang.Object obj4 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj4 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                obj2 = obj4;
                $this2 = $this;
                java.lang.String response03 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("https?://([^/]+)"), url2, i, i2, (java.lang.Object) null);
                if (matchResultFind$default != null || (groupValues = matchResultFind$default.getGroupValues()) == null) {
                    return null;
                }
                java.lang.String host = (java.lang.String) groupValues.get(1);
                if (host != null && (matchResultFind$default2 = kotlin.text.Regex.find$default(new kotlin.text.Regex("/pass_md5/[^'\"]+"), response03, i, i2, (java.lang.Object) null)) != null && (passPath = matchResultFind$default2.getValue()) != null) {
                    java.lang.String md5Url = "https://" + host + passPath;
                    com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    anonymousClass12.L$0 = $this2;
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = response03;
                    anonymousClass12.L$4 = host;
                    anonymousClass12.L$5 = passPath;
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url);
                    anonymousClass12.label = i2;
                    com.Nurgay.DoodLaExtractor.AnonymousClass1 anonymousClass13 = anonymousClass12;
                    $this3 = $this2;
                    obj3 = com.lagradost.nicehttp.Requests.get$default(app2, md5Url, (java.util.Map) null, url2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4090, (java.lang.Object) null);
                    anonymousClass12 = anonymousClass13;
                    if (obj3 == obj) {
                        return obj;
                    }
                    url3 = url2;
                    url4 = host;
                    response0 = response03;
                    referer3 = passPath;
                    response02 = md5Url;
                    java.lang.String videoBase = ((com.lagradost.nicehttp.NiceResponse) obj3).getText();
                    java.lang.String token = kotlin.text.StringsKt.substringAfterLast$default(referer3, "/", (java.lang.String) null, i2, (java.lang.Object) null);
                    java.lang.String trueUrl = videoBase + "zUEJeL3mUN?token=" + token;
                    kotlin.text.MatchResult matchResultFind$default3 = kotlin.text.Regex.find$default(new kotlin.text.Regex("\\d{3,4}p"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response0, "<title>", (java.lang.String) null, i2, (java.lang.Object) null), "</title>", (java.lang.String) null, i2, (java.lang.Object) null), 0, i2, (java.lang.Object) null);
                    java.lang.String quality = (matchResultFind$default3 != null || (groupValues2 = matchResultFind$default3.getGroupValues()) == null) ? null : (java.lang.String) groupValues2.get(0);
                    java.lang.String videoBase2 = $this3.getName();
                    java.lang.String token2 = $this3.getName();
                    com.Nurgay.DoodLaExtractor.AnonymousClass2 anonymousClass2 = new com.Nurgay.DoodLaExtractor.AnonymousClass2(url4, quality, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response0);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url4);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoBase);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable("zUEJeL3mUN");
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(trueUrl);
                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                    anonymousClass12.label = 3;
                    objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(videoBase2, token2, trueUrl, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, anonymousClass2, anonymousClass12, 8, (java.lang.Object) null);
                    return objNewExtractorLink$default != obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink$default);
                }
                return null;
            case 1:
                java.lang.String referer4 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url5 = (java.lang.String) anonymousClass12.L$1;
                com.Nurgay.DoodLaExtractor $this4 = (com.Nurgay.DoodLaExtractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this4;
                obj = coroutine_suspended;
                referer2 = referer4;
                url2 = url5;
                i = 0;
                obj2 = $result;
                i2 = 2;
                java.lang.String response032 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("https?://([^/]+)"), url2, i, i2, (java.lang.Object) null);
                if (matchResultFind$default != null) {
                    break;
                }
                return null;
            case 2:
                java.lang.String md5Url2 = (java.lang.String) anonymousClass12.L$6;
                java.lang.String passPath2 = (java.lang.String) anonymousClass12.L$5;
                java.lang.String host2 = (java.lang.String) anonymousClass12.L$4;
                java.lang.String response04 = (java.lang.String) anonymousClass12.L$3;
                java.lang.String referer5 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url6 = (java.lang.String) anonymousClass12.L$1;
                com.Nurgay.DoodLaExtractor $this5 = (com.Nurgay.DoodLaExtractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this3 = $this5;
                obj = coroutine_suspended;
                response0 = response04;
                referer2 = referer5;
                url3 = url6;
                obj3 = $result;
                referer3 = passPath2;
                url4 = host2;
                i2 = 2;
                response02 = md5Url2;
                java.lang.String videoBase3 = ((com.lagradost.nicehttp.NiceResponse) obj3).getText();
                java.lang.String token3 = kotlin.text.StringsKt.substringAfterLast$default(referer3, "/", (java.lang.String) null, i2, (java.lang.Object) null);
                java.lang.String trueUrl2 = videoBase3 + "zUEJeL3mUN?token=" + token3;
                kotlin.text.MatchResult matchResultFind$default32 = kotlin.text.Regex.find$default(new kotlin.text.Regex("\\d{3,4}p"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response0, "<title>", (java.lang.String) null, i2, (java.lang.Object) null), "</title>", (java.lang.String) null, i2, (java.lang.Object) null), 0, i2, (java.lang.Object) null);
                if (matchResultFind$default32 != null) {
                    java.lang.String quality2 = (matchResultFind$default32 != null || (groupValues2 = matchResultFind$default32.getGroupValues()) == null) ? null : (java.lang.String) groupValues2.get(0);
                    java.lang.String videoBase22 = $this3.getName();
                    java.lang.String token22 = $this3.getName();
                    com.Nurgay.DoodLaExtractor.AnonymousClass2 anonymousClass22 = new com.Nurgay.DoodLaExtractor.AnonymousClass2(url4, quality2, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response0);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url4);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoBase3);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token3);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable("zUEJeL3mUN");
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(trueUrl2);
                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality2);
                    anonymousClass12.label = 3;
                    objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(videoBase22, token22, trueUrl2, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, anonymousClass22, anonymousClass12, 8, (java.lang.Object) null);
                    if (objNewExtractorLink$default != obj) {
                    }
                }
            case 3:
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink$default = $result;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.DoodLaExtractor$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.DoodLaExtractor$getUrl$2", f = "Extractors.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $host;
        final /* synthetic */ java.lang.String $quality;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, kotlin.coroutines.Continuation<? super com.Nurgay.DoodLaExtractor.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$host = str;
            this.$quality = str2;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Nurgay.DoodLaExtractor.AnonymousClass2(this.$host, this.$quality, continuation);
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
                    $this$newExtractorLink.setReferer("https://" + this.$host);
                    $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.ExtractorApiKt.getQualityFromName(this.$quality));
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }
}
