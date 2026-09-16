package com.Nurgay;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00006\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003JH\u0010\u000e\u001a\u00020\u000f2\u0006\u0010\u0010\u001a\u00020\u00052\b\u0010\u0011\u001a\u0004\u0018\u00010\u00052\u0012\u0010\u0012\u001a\u000e\u0012\u0004\u0012\u00020\u0014\u0012\u0004\u0012\u00020\u000f0\u00132\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0016\u0012\u0004\u0012\u00020\u000f0\u0013H\u0096@¢\u0006\u0002\u0010\u0017R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"Lcom/Nurgay/VidNest;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Nurgay"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class VidNest extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "VidNest";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://vidnest.io";

    /* JADX INFO: renamed from: com.Nurgay.VidNest$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.VidNest", f = "Extractors.kt", i = {0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {353, 363}, m = "getUrl", n = {"url", "referer", "subtitleCallback", "callback", "docHeaders", "url", "referer", "subtitleCallback", "callback", "docHeaders", "text", "videoRegex", "labelRegex", "videoUrl", "label"}, nl = {355, 362}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Nurgay.VidNest.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.VidNest.this.getUrl(null, null, null, null, (kotlin.coroutines.Continuation) this);
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

    /* JADX WARN: Removed duplicated region for block: B:23:0x013b  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x0154  */
    /* JADX WARN: Removed duplicated region for block: B:32:0x015a  */
    /* JADX WARN: Removed duplicated region for block: B:37:0x01d6  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.Nurgay.VidNest.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        int i2;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.util.Map docHeaders;
        kotlin.text.MatchResult matchResultFind$default;
        int i3;
        java.lang.String videoUrl;
        kotlin.text.MatchResult matchResultFind$default2;
        java.lang.String label;
        java.lang.String videoUrl2;
        java.lang.Object objNewExtractorLink;
        java.lang.String label2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        kotlin.text.Regex videoRegex;
        kotlin.text.Regex labelRegex;
        java.lang.String text;
        java.lang.String text2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function16;
        java.util.Map docHeaders2;
        java.lang.String referer3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17;
        java.util.List groupValues;
        java.util.List groupValues2;
        if (continuation instanceof com.Nurgay.VidNest.AnonymousClass1) {
            anonymousClass1 = (com.Nurgay.VidNest.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Nurgay.VidNest.AnonymousClass1(continuation);
            }
        }
        com.Nurgay.VidNest.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.Map docHeaders3 = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("Referer", "https://vidnest.io/"), kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")});
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                anonymousClass12.L$3 = function12;
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(docHeaders3);
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                i = 0;
                i2 = 2;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, docHeaders3, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4092, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                function13 = function1;
                function14 = function12;
                docHeaders = docHeaders3;
                java.lang.String text3 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                kotlin.text.Regex videoRegex2 = new kotlin.text.Regex("file\\s*:\\s*[\"']([^\"']+\\.mp4[^\"']*)[\"']");
                kotlin.text.Regex labelRegex2 = new kotlin.text.Regex("label\\s*:\\s*[\"']([^\"']+)[\"']");
                matchResultFind$default = kotlin.text.Regex.find$default(videoRegex2, text3, i, i2, (java.lang.Object) null);
                if (matchResultFind$default != null || (groupValues2 = matchResultFind$default.getGroupValues()) == null) {
                    i3 = 1;
                    videoUrl = null;
                } else {
                    i3 = 1;
                    videoUrl = (java.lang.String) groupValues2.get(1);
                }
                matchResultFind$default2 = kotlin.text.Regex.find$default(labelRegex2, text3, i, i2, (java.lang.Object) null);
                if (matchResultFind$default2 != null || (groupValues = matchResultFind$default2.getGroupValues()) == null || (label = (java.lang.String) groupValues.get(i3)) == null) {
                    label = "VidNest";
                }
                if (videoUrl == null) {
                    java.lang.String name = getName();
                    java.lang.String videoUrl3 = videoUrl;
                    java.lang.String videoUrl4 = getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType extractorLinkType = com.lagradost.cloudstream3.utils.ExtractorLinkType.VIDEO;
                    com.Nurgay.VidNest.AnonymousClass2 anonymousClass2 = new com.Nurgay.VidNest.AnonymousClass2(label, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(docHeaders);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(text3);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoRegex2);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(labelRegex2);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl3);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(label);
                    anonymousClass12.L$10 = function14;
                    anonymousClass12.label = 2;
                    videoUrl2 = videoUrl3;
                    objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, videoUrl4, videoUrl2, extractorLinkType, anonymousClass2, anonymousClass12);
                    if (objNewExtractorLink == obj) {
                        return obj;
                    }
                    label2 = label;
                    function15 = function14;
                    videoRegex = videoRegex2;
                    labelRegex = labelRegex2;
                    text = text3;
                    text2 = url2;
                    function16 = function13;
                    docHeaders2 = docHeaders;
                    referer3 = referer2;
                    function17 = function15;
                    function15.invoke(objNewExtractorLink);
                    return kotlin.Unit.INSTANCE;
                }
                return kotlin.Unit.INSTANCE;
            case 1:
                java.util.Map docHeaders4 = (java.util.Map) anonymousClass12.L$4;
                function14 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                function13 = (kotlin.jvm.functions.Function1) anonymousClass12.L$2;
                referer2 = (java.lang.String) anonymousClass12.L$1;
                url2 = (java.lang.String) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                docHeaders = docHeaders4;
                i2 = 2;
                obj2 = $result;
                i = 0;
                java.lang.String text32 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                kotlin.text.Regex videoRegex22 = new kotlin.text.Regex("file\\s*:\\s*[\"']([^\"']+\\.mp4[^\"']*)[\"']");
                kotlin.text.Regex labelRegex22 = new kotlin.text.Regex("label\\s*:\\s*[\"']([^\"']+)[\"']");
                matchResultFind$default = kotlin.text.Regex.find$default(videoRegex22, text32, i, i2, (java.lang.Object) null);
                if (matchResultFind$default != null) {
                    i3 = 1;
                    videoUrl = null;
                    matchResultFind$default2 = kotlin.text.Regex.find$default(labelRegex22, text32, i, i2, (java.lang.Object) null);
                    if (matchResultFind$default2 != null) {
                        label = "VidNest";
                        if (videoUrl == null) {
                        }
                    }
                }
                return kotlin.Unit.INSTANCE;
            case 2:
                function15 = (kotlin.jvm.functions.Function1) anonymousClass12.L$10;
                label2 = (java.lang.String) anonymousClass12.L$9;
                videoUrl2 = (java.lang.String) anonymousClass12.L$8;
                labelRegex = (kotlin.text.Regex) anonymousClass12.L$7;
                videoRegex = (kotlin.text.Regex) anonymousClass12.L$6;
                text = (java.lang.String) anonymousClass12.L$5;
                docHeaders2 = (java.util.Map) anonymousClass12.L$4;
                function17 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                function16 = (kotlin.jvm.functions.Function1) anonymousClass12.L$2;
                referer3 = (java.lang.String) anonymousClass12.L$1;
                text2 = (java.lang.String) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
                function15.invoke(objNewExtractorLink);
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.VidNest$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.VidNest$getUrl$2", f = "Extractors.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $label;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, kotlin.coroutines.Continuation<? super com.Nurgay.VidNest.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$label = str;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Nurgay.VidNest.AnonymousClass2(this.$label, continuation);
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
                    $this$newExtractorLink.setReferer("https://vidnest.io/");
                    $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.ExtractorApiKt.getQualityFromName(this.$label));
                    $this$newExtractorLink.setHeaders(kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"), kotlin.TuplesKt.to("Referer", "https://vidnest.io/"), kotlin.TuplesKt.to("Accept", "*/*"), kotlin.TuplesKt.to("Origin", "https://vidnest.io"), kotlin.TuplesKt.to("Connection", "keep-alive"), kotlin.TuplesKt.to("Sec-Fetch-Dest", "video"), kotlin.TuplesKt.to("Sec-Fetch-Mode", "no-cors"), kotlin.TuplesKt.to("Sec-Fetch-Site", "same-site"), kotlin.TuplesKt.to("Priority", "u=4")}));
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }
}
