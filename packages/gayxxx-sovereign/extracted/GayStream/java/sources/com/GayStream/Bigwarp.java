package com.GayStream;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00006\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003JH\u0010\u0011\u001a\u00020\u00122\u0006\u0010\u0013\u001a\u00020\u00052\b\u0010\u0014\u001a\u0004\u0018\u00010\u00052\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0017\u0012\u0004\u0012\u00020\u00120\u00162\u0012\u0010\u0018\u001a\u000e\u0012\u0004\u0012\u00020\u0019\u0012\u0004\u0012\u00020\u00120\u0016H\u0096@¢\u0006\u0002\u0010\u001aR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u001b"}, d2 = {"Lcom/GayStream/Bigwarp;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GayStream"}, k = 1, mv = {2, 3, 0}, xi = 48)
public class Bigwarp extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Bigwarp";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://bigwarp.io";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.GayStream.Bigwarp$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.Bigwarp", f = "Extractors.kt", i = {0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {163, 164, 171}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "subtitleCallback", "callback", "$this", "url", "referer", "subtitleCallback", "callback", "link", "$this", "url", "referer", "subtitleCallback", "callback", "link", "source", "regex", "matchResult", "match"}, nl = {164, 165, 170}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9"}, v = 2)
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GayStream.Bigwarp.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.Bigwarp.getUrl$suspendImpl(com.GayStream.Bigwarp.this, null, null, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.Nullable
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String str, @org.jetbrains.annotations.Nullable java.lang.String str2, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return getUrl$suspendImpl(this, str, str2, function1, function12, continuation);
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

    /* JADX WARN: Removed duplicated region for block: B:21:0x011f  */
    /* JADX WARN: Removed duplicated region for block: B:24:0x0172 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:25:0x0173  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x01a9  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x01ae  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x022d  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.GayStream.Bigwarp $this, java.lang.String url, java.lang.String referer, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.GayStream.Bigwarp.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        java.lang.String url2;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        com.GayStream.Bigwarp $this2;
        java.lang.String link;
        com.GayStream.Bigwarp $this3;
        java.lang.Object obj3;
        java.lang.String url3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String link2;
        java.lang.String match;
        java.lang.String match2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16;
        java.lang.String link3;
        java.lang.String source;
        kotlin.text.Regex regex;
        java.lang.String link4;
        com.GayStream.Bigwarp $this4;
        kotlin.text.MatchResult matchResult;
        java.lang.Object obj4;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18;
        java.util.List groupValues;
        if (continuation instanceof com.GayStream.Bigwarp.AnonymousClass1) {
            anonymousClass1 = (com.GayStream.Bigwarp.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.GayStream.Bigwarp.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = url;
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                anonymousClass12.L$4 = function12;
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                i = 2;
                java.lang.Object obj5 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4062, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj5 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                function13 = function1;
                function14 = function12;
                obj2 = obj5;
                $this2 = $this;
                link = ((com.lagradost.nicehttp.NiceResponse) obj2).getHeaders().get("location");
                if (link == null) {
                    link = url2;
                }
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this2;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = function14;
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                anonymousClass12.label = i;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19 = function14;
                java.lang.String link5 = link;
                com.GayStream.Bigwarp.AnonymousClass1 anonymousClass13 = anonymousClass12;
                $this3 = $this2;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app2, link5, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass13;
                if (obj3 != obj) {
                    return obj;
                }
                url3 = url2;
                function15 = function19;
                link2 = link5;
                java.lang.String source2 = java.lang.String.valueOf(((com.lagradost.nicehttp.NiceResponse) obj3).getDocument().selectFirst("body > script"));
                kotlin.text.Regex regex2 = new kotlin.text.Regex("file:\\s*\\\"((?:https?://|//)[^\\\"]+)");
                kotlin.text.MatchResult matchResult2 = kotlin.text.Regex.find$default(regex2, source2, 0, i, (java.lang.Object) null);
                match = (matchResult2 != null || (groupValues = matchResult2.getGroupValues()) == null) ? null : (java.lang.String) groupValues.get(1);
                if (match != null) {
                    return kotlin.Unit.INSTANCE;
                }
                java.lang.String match3 = match;
                java.lang.String match4 = $this3.getName();
                java.lang.String match5 = $this3.getName();
                com.GayStream.Bigwarp.AnonymousClass2 anonymousClass2 = new com.GayStream.Bigwarp.AnonymousClass2(null);
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link2);
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(source2);
                anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(regex2);
                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(matchResult2);
                anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(match3);
                anonymousClass12.L$10 = function15;
                anonymousClass12.label = 3;
                java.lang.Object objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(match4, match5, match3, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, anonymousClass2, anonymousClass12, 8, (java.lang.Object) null);
                if (objNewExtractorLink$default == obj) {
                    return obj;
                }
                match2 = match3;
                function16 = function15;
                link3 = link2;
                source = source2;
                regex = regex2;
                link4 = referer2;
                $this4 = $this3;
                matchResult = matchResult2;
                obj4 = objNewExtractorLink$default;
                function17 = function16;
                function18 = function13;
                function17.invoke(obj4);
                return kotlin.Unit.INSTANCE;
            case 1:
                function14 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function110 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url4 = (java.lang.String) anonymousClass12.L$1;
                com.GayStream.Bigwarp $this5 = (com.GayStream.Bigwarp) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this5;
                obj = coroutine_suspended;
                obj2 = $result;
                function13 = function110;
                referer2 = referer3;
                url2 = url4;
                i = 2;
                link = ((com.lagradost.nicehttp.NiceResponse) obj2).getHeaders().get("location");
                if (link == null) {
                }
                com.lagradost.nicehttp.Requests app22 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this2;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = function14;
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                anonymousClass12.label = i;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function192 = function14;
                java.lang.String link52 = link;
                com.GayStream.Bigwarp.AnonymousClass1 anonymousClass132 = anonymousClass12;
                $this3 = $this2;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app22, link52, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass132, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass132;
                if (obj3 != obj) {
                }
                break;
            case 2:
                java.lang.String link6 = (java.lang.String) anonymousClass12.L$5;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer4 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url5 = (java.lang.String) anonymousClass12.L$1;
                com.GayStream.Bigwarp $this6 = (com.GayStream.Bigwarp) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this3 = $this6;
                obj = coroutine_suspended;
                function13 = function112;
                referer2 = referer4;
                url3 = url5;
                i = 2;
                obj3 = $result;
                function15 = function111;
                link2 = link6;
                java.lang.String source22 = java.lang.String.valueOf(((com.lagradost.nicehttp.NiceResponse) obj3).getDocument().selectFirst("body > script"));
                kotlin.text.Regex regex22 = new kotlin.text.Regex("file:\\s*\\\"((?:https?://|//)[^\\\"]+)");
                kotlin.text.MatchResult matchResult22 = kotlin.text.Regex.find$default(regex22, source22, 0, i, (java.lang.Object) null);
                if (matchResult22 != null) {
                    if (match != null) {
                    }
                }
                return kotlin.Unit.INSTANCE;
            case 3:
                function17 = (kotlin.jvm.functions.Function1) anonymousClass12.L$10;
                match2 = (java.lang.String) anonymousClass12.L$9;
                matchResult = (kotlin.text.MatchResult) anonymousClass12.L$8;
                regex = (kotlin.text.Regex) anonymousClass12.L$7;
                source = (java.lang.String) anonymousClass12.L$6;
                link3 = (java.lang.String) anonymousClass12.L$5;
                function16 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                function18 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                link4 = (java.lang.String) anonymousClass12.L$2;
                $this4 = (com.GayStream.Bigwarp) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj4 = $result;
                function17.invoke(obj4);
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.GayStream.Bigwarp$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.Bigwarp$getUrl$2", f = "Extractors.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        private /* synthetic */ java.lang.Object L$0;
        int label;

        AnonymousClass2(kotlin.coroutines.Continuation<? super com.GayStream.Bigwarp.AnonymousClass2> continuation) {
            super(2, continuation);
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.GayStream.Bigwarp.AnonymousClass2(continuation);
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
                    $this$newExtractorLink.setReferer("");
                    $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.Qualities.Unknown.getValue());
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }
}
