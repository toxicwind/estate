package com.GXtapes;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00004\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0010\u000b\n\u0002\b\b\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B%\u0012\b\b\u0002\u0010\u0002\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0004\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0005\u001a\u00020\u0006¢\u0006\u0004\b\u0007\u0010\bJH\u0010\u000e\u001a\u00020\u000f2\u0006\u0010\u0010\u001a\u00020\u00032\b\u0010\u0011\u001a\u0004\u0018\u00010\u00032\u0012\u0010\u0012\u001a\u000e\u0012\u0004\u0012\u00020\u0014\u0012\u0004\u0012\u00020\u000f0\u00132\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0016\u0012\u0004\u0012\u00020\u000f0\u0013H\u0096@¢\u0006\u0002\u0010\u0017R\u0014\u0010\u0002\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\nR\u0014\u0010\u0004\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\nR\u0014\u0010\u0005\u001a\u00020\u0006X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"Lcom/GXtapes/GXtapes88z;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "name", "", "mainUrl", "requiresReferer", "", "<init>", "(Ljava/lang/String;Ljava/lang/String;Z)V", "getName", "()Ljava/lang/String;", "getMainUrl", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GXtapes"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/GXtapes/GXtapes88z\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,138:1\n1915#2,2:139\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/GXtapes/GXtapes88z\n*L\n114#1:139,2\n*E\n"})
public final class GXtapes88z extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name;
    private final boolean requiresReferer;

    /* JADX INFO: renamed from: com.GXtapes.GXtapes88z$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes88z", f = "Extractor.kt", i = {0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {96, 118}, m = "getUrl", n = {"url", "referer", "subtitleCallback", "callback", "id", "apiUrl", "url", "referer", "subtitleCallback", "callback", "id", "apiUrl", "apiRes", "decodedBytes", "decodedText", "m3u8Regex", "matches", "$this$forEach$iv", "element$iv", "link", "$i$f$forEach", "$i$a$-forEach-GXtapes88z$getUrl$2"}, nl = {99, 117}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$13", "L$14", "I$0", "I$1"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$10;
        java.lang.Object L$11;
        java.lang.Object L$12;
        java.lang.Object L$13;
        java.lang.Object L$14;
        java.lang.Object L$15;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes88z.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes88z.this.getUrl(null, null, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    public GXtapes88z() {
        this(null, null, false, 7, null);
    }

    public GXtapes88z(@org.jetbrains.annotations.NotNull java.lang.String name, @org.jetbrains.annotations.NotNull java.lang.String mainUrl, boolean requiresReferer) {
        this.name = name;
        this.mainUrl = mainUrl;
        this.requiresReferer = requiresReferer;
    }

    public /* synthetic */ GXtapes88z(java.lang.String str, java.lang.String str2, boolean z, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? "GXtapes8z" : str, (i & 2) != 0 ? "https://88z.io" : str2, (i & 4) != 0 ? false : z);
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

    /* JADX WARN: Removed duplicated region for block: B:41:0x0215 A[Catch: Exception -> 0x038b, TRY_ENTER, TRY_LEAVE, TryCatch #4 {Exception -> 0x038b, blocks: (B:35:0x01b5, B:41:0x0215), top: B:85:0x01b5 }] */
    /* JADX WARN: Removed duplicated region for block: B:45:0x0236 A[Catch: Exception -> 0x037c, TRY_LEAVE, TryCatch #2 {Exception -> 0x037c, blocks: (B:43:0x0230, B:45:0x0236), top: B:81:0x0230 }] */
    /* JADX WARN: Removed duplicated region for block: B:65:0x036f  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /* JADX WARN: Removed duplicated region for block: B:83:0x01ec A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:54:0x0307 -> B:89:0x0328). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass1;
        com.GXtapes.GXtapes88z gXtapes88z;
        com.GXtapes.GXtapes88z gXtapes88z2;
        kotlin.coroutines.Continuation $completion;
        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass12;
        java.lang.String id;
        java.lang.String apiUrl;
        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass13;
        java.lang.Object $result;
        java.lang.String decodedText;
        java.lang.String apiUrl2;
        int i;
        java.lang.Object obj;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String apiRes;
        byte[] decodedBytes;
        java.lang.String decodedText2;
        kotlin.text.Regex m3u8Regex;
        java.util.List matches;
        kotlin.text.Regex m3u8Regex2;
        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass14;
        java.lang.String apiRes2;
        java.util.List matches2;
        java.lang.Object $this$forEach$iv;
        int $i$f$forEach;
        java.util.Iterator it;
        java.lang.String decodedText3;
        kotlin.coroutines.Continuation $completion2;
        java.lang.String url3;
        kotlin.coroutines.Continuation $completion3;
        java.lang.Object obj3;
        com.GXtapes.GXtapes88z gXtapes88z3;
        java.util.Iterator it2;
        int $i$f$forEach2;
        java.lang.Object objNewExtractorLink;
        java.lang.Object element$iv;
        java.lang.Object $result2;
        java.lang.String apiUrl3;
        kotlin.text.Regex m3u8Regex3;
        byte[] decodedBytes2;
        java.util.List matches3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String id2;
        java.lang.String id3;
        java.lang.String decodedText4;
        if (continuation instanceof com.GXtapes.GXtapes88z.AnonymousClass1) {
            anonymousClass1 = (com.GXtapes.GXtapes88z.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                gXtapes88z = this;
            } else {
                gXtapes88z = this;
                anonymousClass1 = gXtapes88z.new AnonymousClass1(continuation);
            }
        }
        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass15 = anonymousClass1;
        java.lang.Object $result3 = anonymousClass15.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass15.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result3);
                try {
                    id = kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter(url, "#", ""), "?", (java.lang.String) null, 2, (java.lang.Object) null);
                } catch (java.lang.Exception e) {
                    e = e;
                    gXtapes88z2 = this;
                    $completion = continuation;
                    anonymousClass12 = anonymousClass15;
                }
                if (!kotlin.text.StringsKt.isBlank(id)) {
                    java.lang.String apiUrl4 = gXtapes88z.getMainUrl() + "/api/v1/info?id=" + id;
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String mainUrl = gXtapes88z.getMainUrl();
                    anonymousClass15.L$0 = url;
                    anonymousClass15.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                    anonymousClass15.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                    anonymousClass15.L$3 = function12;
                    anonymousClass15.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(id);
                    anonymousClass15.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(apiUrl4);
                    anonymousClass15.label = 1;
                    apiUrl = apiUrl4;
                    anonymousClass13 = anonymousClass15;
                    $result = $result3;
                    decodedText = id;
                    apiUrl2 = null;
                    i = 2;
                    try {
                        obj = com.lagradost.nicehttp.Requests.get$default(app, apiUrl, (java.util.Map) null, mainUrl, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4090, (java.lang.Object) null);
                    } catch (java.lang.Exception e2) {
                        e = e2;
                        gXtapes88z2 = this;
                        $completion = continuation;
                        anonymousClass12 = anonymousClass13;
                        $result3 = $result;
                    }
                    if (obj == coroutine_suspended) {
                        return coroutine_suspended;
                    }
                    referer2 = referer;
                    function13 = function1;
                    function14 = function12;
                    obj2 = obj;
                    url2 = url;
                    try {
                        apiRes = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                        decodedBytes = java.util.Base64.getDecoder().decode(apiRes);
                        decodedText2 = new java.lang.String(decodedBytes, kotlin.text.Charsets.UTF_8);
                        m3u8Regex = new kotlin.text.Regex("https?://[^\\s\"'<>]+\\.m3u8[^\\s\"'<>]*");
                        matches = kotlin.sequences.SequencesKt.toList(kotlin.sequences.SequencesKt.map(kotlin.text.Regex.findAll$default(m3u8Regex, decodedText2, 0, i, apiUrl2), new kotlin.jvm.functions.Function1() { // from class: com.GXtapes.GXtapes88z$$ExternalSyntheticLambda0
                            public final java.lang.Object invoke(java.lang.Object obj4) {
                                return ((kotlin.text.MatchResult) obj4).getValue();
                            }
                        }));
                    } catch (java.lang.Exception e3) {
                        e = e3;
                        gXtapes88z2 = this;
                        $completion = continuation;
                        anonymousClass12 = anonymousClass13;
                        $result3 = $result;
                    }
                    if (matches.isEmpty()) {
                        java.util.List $this$forEach$iv2 = matches;
                        com.GXtapes.GXtapes88z.AnonymousClass1 anonymousClass16 = anonymousClass13;
                        m3u8Regex2 = m3u8Regex;
                        anonymousClass14 = anonymousClass16;
                        apiRes2 = decodedText2;
                        matches2 = matches;
                        $this$forEach$iv = $this$forEach$iv2;
                        $i$f$forEach = 0;
                        it = $this$forEach$iv2.iterator();
                        gXtapes88z2 = gXtapes88z;
                        decodedText3 = apiUrl;
                        $completion2 = continuation;
                        try {
                        } catch (java.lang.Exception e4) {
                            e = e4;
                            anonymousClass12 = anonymousClass14;
                            $completion = $completion2;
                            $result3 = $result;
                        }
                        if (it.hasNext()) {
                            try {
                                try {
                                    try {
                                        java.lang.Object element$iv2 = it.next();
                                        java.lang.String link = (java.lang.String) element$iv2;
                                        com.lagradost.api.Log.INSTANCE.i(gXtapes88z2.getName(), "Found m3u8: " + link);
                                        java.lang.String name = gXtapes88z2.getName();
                                        java.lang.String str = gXtapes88z2.getName() + " - HLS";
                                        com.lagradost.cloudstream3.utils.ExtractorLinkType extractorLinkType = com.lagradost.cloudstream3.utils.ExtractorLinkType.M3U8;
                                        obj3 = null;
                                        com.GXtapes.GXtapes88z$getUrl$2$1 gXtapes88z$getUrl$2$1 = new com.GXtapes.GXtapes88z$getUrl$2$1(gXtapes88z2, null);
                                        anonymousClass14.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                                        anonymousClass14.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                                        anonymousClass14.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                                        anonymousClass14.L$3 = function14;
                                        anonymousClass14.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(decodedText);
                                        anonymousClass14.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(decodedText3);
                                        anonymousClass14.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(apiRes);
                                        anonymousClass14.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(decodedBytes);
                                        anonymousClass14.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(apiRes2);
                                        anonymousClass14.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8Regex2);
                                        anonymousClass14.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(matches2);
                                        anonymousClass14.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEach$iv);
                                        anonymousClass14.L$12 = it;
                                        anonymousClass14.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv2);
                                        anonymousClass14.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                                        anonymousClass14.L$15 = function14;
                                        anonymousClass14.I$0 = $i$f$forEach;
                                        anonymousClass14.I$1 = 0;
                                        anonymousClass14.label = 2;
                                        objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, str, link, extractorLinkType, gXtapes88z$getUrl$2$1, anonymousClass12);
                                    } catch (java.lang.Exception e5) {
                                        e = e5;
                                        $completion = $completion3;
                                        gXtapes88z2 = gXtapes88z3;
                                        $result3 = $result;
                                    }
                                    gXtapes88z3 = gXtapes88z2;
                                    it2 = it;
                                    anonymousClass12 = anonymousClass14;
                                    $i$f$forEach2 = $i$f$forEach;
                                } catch (java.lang.Exception e6) {
                                    e = e6;
                                    anonymousClass12 = anonymousClass14;
                                    $completion = $completion3;
                                    $result3 = $result;
                                }
                                $completion3 = $completion2;
                            } catch (java.lang.Exception e7) {
                                e = e7;
                                anonymousClass12 = anonymousClass14;
                                $completion = $completion2;
                                $result3 = $result;
                            }
                            url3 = url2;
                            if (objNewExtractorLink == coroutine_suspended) {
                                return coroutine_suspended;
                            }
                            it = it2;
                            $result3 = objNewExtractorLink;
                            element$iv = $result;
                            $result2 = $this$forEach$iv;
                            apiUrl3 = decodedText3;
                            gXtapes88z2 = gXtapes88z3;
                            m3u8Regex3 = m3u8Regex2;
                            $i$f$forEach = $i$f$forEach2;
                            url2 = url3;
                            decodedBytes2 = decodedBytes;
                            matches3 = matches2;
                            function15 = function14;
                            id2 = decodedText;
                            id3 = apiRes2;
                            decodedText4 = apiRes;
                            $completion = $completion3;
                            try {
                                function15.invoke($result3);
                                $completion2 = $completion;
                                anonymousClass14 = anonymousClass12;
                                decodedBytes = decodedBytes2;
                                apiRes = decodedText4;
                                decodedText3 = apiUrl3;
                                apiRes2 = id3;
                                $this$forEach$iv = $result2;
                                decodedText = id2;
                                $result = element$iv;
                                matches2 = matches3;
                                m3u8Regex2 = m3u8Regex3;
                            } catch (java.lang.Exception e8) {
                                e = e8;
                                $result3 = element$iv;
                            }
                            if (it.hasNext()) {
                                return kotlin.Unit.INSTANCE;
                            }
                            break;
                        }
                        break;
                    } else {
                        try {
                            com.lagradost.api.Log.INSTANCE.e(gXtapes88z.getName(), "No m3u8 link found in decoded payload for " + url2);
                            return kotlin.Unit.INSTANCE;
                        } catch (java.lang.Exception e9) {
                            e = e9;
                            $completion = continuation;
                            gXtapes88z2 = gXtapes88z;
                            anonymousClass12 = anonymousClass13;
                            $result3 = $result;
                        }
                    }
                    break;
                } else {
                    try {
                        com.lagradost.api.Log.INSTANCE.e(gXtapes88z.getName(), "No id found in url: " + url);
                        return kotlin.Unit.INSTANCE;
                    } catch (java.lang.Exception e10) {
                        e = e10;
                        gXtapes88z2 = gXtapes88z;
                        anonymousClass12 = anonymousClass15;
                        $completion = continuation;
                    }
                }
                com.lagradost.api.Log.INSTANCE.e(gXtapes88z2.getName(), "Error in GXtapes88z: " + e.getMessage());
                return kotlin.Unit.INSTANCE;
            case 1:
                java.lang.String apiUrl5 = (java.lang.String) anonymousClass15.L$5;
                java.lang.String id4 = (java.lang.String) anonymousClass15.L$4;
                function14 = (kotlin.jvm.functions.Function1) anonymousClass15.L$3;
                function13 = (kotlin.jvm.functions.Function1) anonymousClass15.L$2;
                referer2 = (java.lang.String) anonymousClass15.L$1;
                java.lang.String url4 = (java.lang.String) anonymousClass15.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result3);
                    anonymousClass13 = anonymousClass15;
                    $result = $result3;
                    decodedText = id4;
                    url2 = url4;
                    apiUrl = apiUrl5;
                    obj2 = $result;
                    i = 2;
                    apiUrl2 = null;
                    apiRes = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                    decodedBytes = java.util.Base64.getDecoder().decode(apiRes);
                    decodedText2 = new java.lang.String(decodedBytes, kotlin.text.Charsets.UTF_8);
                    m3u8Regex = new kotlin.text.Regex("https?://[^\\s\"'<>]+\\.m3u8[^\\s\"'<>]*");
                    matches = kotlin.sequences.SequencesKt.toList(kotlin.sequences.SequencesKt.map(kotlin.text.Regex.findAll$default(m3u8Regex, decodedText2, 0, i, apiUrl2), new kotlin.jvm.functions.Function1() { // from class: com.GXtapes.GXtapes88z$$ExternalSyntheticLambda0
                        public final java.lang.Object invoke(java.lang.Object obj4) {
                            return ((kotlin.text.MatchResult) obj4).getValue();
                        }
                    }));
                    if (matches.isEmpty()) {
                    }
                } catch (java.lang.Exception e11) {
                    e = e11;
                    gXtapes88z2 = gXtapes88z;
                    anonymousClass12 = anonymousClass15;
                    $completion = continuation;
                }
                com.lagradost.api.Log.INSTANCE.e(gXtapes88z2.getName(), "Error in GXtapes88z: " + e.getMessage());
                return kotlin.Unit.INSTANCE;
            case 2:
                int i2 = anonymousClass15.I$1;
                int $i$f$forEach3 = anonymousClass15.I$0;
                function15 = (kotlin.jvm.functions.Function1) anonymousClass15.L$15;
                java.lang.Object obj4 = anonymousClass15.L$13;
                java.util.Iterator it3 = (java.util.Iterator) anonymousClass15.L$12;
                java.lang.Object $this$forEach$iv3 = (java.lang.Iterable) anonymousClass15.L$11;
                java.util.List matches4 = (java.util.List) anonymousClass15.L$10;
                kotlin.text.Regex m3u8Regex4 = (kotlin.text.Regex) anonymousClass15.L$9;
                java.lang.String decodedText5 = (java.lang.String) anonymousClass15.L$8;
                decodedBytes2 = (byte[]) anonymousClass15.L$7;
                decodedText4 = (java.lang.String) anonymousClass15.L$6;
                apiUrl3 = (java.lang.String) anonymousClass15.L$5;
                java.lang.String id5 = (java.lang.String) anonymousClass15.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = (kotlin.jvm.functions.Function1) anonymousClass15.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) anonymousClass15.L$2;
                java.lang.String referer3 = (java.lang.String) anonymousClass15.L$1;
                java.lang.String url5 = (java.lang.String) anonymousClass15.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result3);
                    anonymousClass12 = anonymousClass15;
                    element$iv = $result3;
                    m3u8Regex3 = m3u8Regex4;
                    $result2 = $this$forEach$iv3;
                    matches3 = matches4;
                    id2 = id5;
                    function14 = function16;
                    url2 = url5;
                    gXtapes88z2 = gXtapes88z;
                    id3 = decodedText5;
                    it = it3;
                    obj3 = null;
                    function13 = function17;
                    $completion = continuation;
                    $i$f$forEach = $i$f$forEach3;
                    referer2 = referer3;
                    function15.invoke($result3);
                    $completion2 = $completion;
                    anonymousClass14 = anonymousClass12;
                    decodedBytes = decodedBytes2;
                    apiRes = decodedText4;
                    decodedText3 = apiUrl3;
                    apiRes2 = id3;
                    $this$forEach$iv = $result2;
                    decodedText = id2;
                    $result = element$iv;
                    matches2 = matches3;
                    m3u8Regex2 = m3u8Regex3;
                    if (it.hasNext()) {
                    }
                } catch (java.lang.Exception e12) {
                    e = e12;
                    gXtapes88z2 = gXtapes88z;
                    anonymousClass12 = anonymousClass15;
                    $completion = continuation;
                    break;
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
