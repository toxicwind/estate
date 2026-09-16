package com.GXtapes;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00004\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0010\u000b\n\u0002\b\b\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B%\u0012\b\b\u0002\u0010\u0002\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0004\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0005\u001a\u00020\u0006¢\u0006\u0004\b\u0007\u0010\bJH\u0010\u000e\u001a\u00020\u000f2\u0006\u0010\u0010\u001a\u00020\u00032\b\u0010\u0011\u001a\u0004\u0018\u00010\u00032\u0012\u0010\u0012\u001a\u000e\u0012\u0004\u0012\u00020\u0014\u0012\u0004\u0012\u00020\u000f0\u00132\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0016\u0012\u0004\u0012\u00020\u000f0\u0013H\u0096@¢\u0006\u0002\u0010\u0017R\u0014\u0010\u0002\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\nR\u0014\u0010\u0004\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\nR\u0014\u0010\u0005\u001a\u00020\u0006X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"Lcom/GXtapes/GXtapes74k;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "name", "", "mainUrl", "requiresReferer", "", "<init>", "(Ljava/lang/String;Ljava/lang/String;Z)V", "getName", "()Ljava/lang/String;", "getMainUrl", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GXtapes"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/GXtapes/GXtapes74k\n+ 2 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 3 Iterators.kt\nkotlin/collections/CollectionsKt__IteratorsKt\n*L\n1#1,138:1\n1#2:139\n32#3,2:140\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/GXtapes/GXtapes74k\n*L\n59#1:140,2\n*E\n"})
public final class GXtapes74k extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name;
    private final boolean requiresReferer;

    /* JADX INFO: renamed from: com.GXtapes.GXtapes74k$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes74k", f = "Extractor.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {54, 63}, m = "getUrl", n = {"url", "referer", "subtitleCallback", "callback", "url", "referer", "subtitleCallback", "callback", "response", "script", "unpackedScript", "links", "obj", "$this$forEach$iv", "element$iv", "it", "finalUrl", "$i$f$forEach", "$i$a$-forEach-GXtapes74k$getUrl$2"}, nl = {55, 62}, s = {"L$0", "L$1", "L$2", "L$3", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$11", "L$12", "L$13", "I$0", "I$1"}, v = 2)
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes74k.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes74k.this.getUrl(null, null, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    public GXtapes74k() {
        this(null, null, false, 7, null);
    }

    public GXtapes74k(@org.jetbrains.annotations.NotNull java.lang.String name, @org.jetbrains.annotations.NotNull java.lang.String mainUrl, boolean requiresReferer) {
        this.name = name;
        this.mainUrl = mainUrl;
        this.requiresReferer = requiresReferer;
    }

    public /* synthetic */ GXtapes74k(java.lang.String str, java.lang.String str2, boolean z, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? "GXtapes74k" : str, (i & 2) != 0 ? "https://74k.io/e/" : str2, (i & 4) != 0 ? false : z);
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

    /* JADX WARN: Removed duplicated region for block: B:21:0x012a  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x01a0  */
    /* JADX WARN: Removed duplicated region for block: B:41:0x0266  */
    /* JADX WARN: Removed duplicated region for block: B:45:0x0145 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:39:0x0244 -> B:40:0x0255). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) throws org.json.JSONException {
        com.GXtapes.GXtapes74k.AnonymousClass1 anonymousClass1;
        com.GXtapes.GXtapes74k gXtapes74k;
        java.lang.Object $result;
        com.GXtapes.GXtapes74k.AnonymousClass1 anonymousClass12;
        java.lang.Object $result2;
        boolean z;
        int i;
        java.lang.String links;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        java.lang.Object obj;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        org.jsoup.nodes.Document response;
        java.util.Iterator it;
        java.lang.Object obj2;
        org.jsoup.nodes.Element element;
        java.lang.String unpackedScript;
        java.lang.String unpackedScript2;
        java.util.Iterator<java.lang.String> itKeys;
        com.GXtapes.GXtapes74k.AnonymousClass1 anonymousClass13;
        java.lang.Object obj3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String links2;
        org.json.JSONObject obj4;
        int $i$f$forEach;
        java.lang.Object $result3;
        com.GXtapes.GXtapes74k gXtapes74k2;
        kotlin.coroutines.Continuation<? super kotlin.Unit> continuation2;
        java.util.Iterator<java.lang.String> it2;
        java.util.Iterator<java.lang.String> it3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16;
        int $i$f$forEach2;
        com.GXtapes.GXtapes74k.AnonymousClass1 anonymousClass14;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17;
        org.json.JSONObject obj5;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18;
        java.lang.Object $result4;
        if (continuation instanceof com.GXtapes.GXtapes74k.AnonymousClass1) {
            anonymousClass1 = (com.GXtapes.GXtapes74k.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                gXtapes74k = this;
            } else {
                gXtapes74k = this;
                anonymousClass1 = gXtapes74k.new AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result5 = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result5);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass1.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                anonymousClass1.L$3 = function12;
                anonymousClass1.label = 1;
                $result = $result5;
                anonymousClass12 = anonymousClass1;
                $result2 = coroutine_suspended;
                z = false;
                i = 2;
                java.lang.Object obj6 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                if (obj6 == $result2) {
                    return $result2;
                }
                links = url;
                referer2 = referer;
                function13 = function1;
                obj = obj6;
                function14 = function12;
                response = ((com.lagradost.nicehttp.NiceResponse) obj).getDocument();
                it = response.select("script").iterator();
                while (true) {
                    if (it.hasNext()) {
                        obj2 = null;
                    } else {
                        java.lang.Object next = it.next();
                        if (kotlin.text.StringsKt.contains$default(((org.jsoup.nodes.Element) next).data(), "eval", z, i, (java.lang.Object) null)) {
                            obj2 = next;
                        }
                    }
                }
                element = (org.jsoup.nodes.Element) obj2;
                if (element != null || (unpackedScript = element.data()) == null) {
                    return kotlin.Unit.INSTANCE;
                }
                java.lang.String unpackedScript3 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getAndUnpack(unpackedScript);
                java.lang.String links3 = '{' + kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(unpackedScript3, "var links={", (java.lang.String) null, i, (java.lang.Object) null), "};", (java.lang.String) null, i, (java.lang.Object) null) + '}';
                org.json.JSONObject obj7 = new org.json.JSONObject(links3);
                unpackedScript2 = unpackedScript3;
                itKeys = obj7.keys();
                anonymousClass13 = anonymousClass12;
                obj3 = $result2;
                function15 = function14;
                links2 = links3;
                obj4 = obj7;
                $i$f$forEach = 0;
                $result3 = $result;
                gXtapes74k2 = this;
                continuation2 = continuation;
                it2 = itKeys;
                if (it2.hasNext()) {
                    java.lang.Object element$iv = it2.next();
                    java.lang.String it4 = (java.lang.String) element$iv;
                    java.lang.String finalUrl = obj4.getString(it4);
                    kotlin.coroutines.Continuation<? super kotlin.Unit> continuation3 = continuation2;
                    java.lang.Object $result6 = $result3;
                    org.jsoup.nodes.Document response2 = response;
                    if (!kotlin.text.StringsKt.startsWith$default(finalUrl, "http", false, 2, (java.lang.Object) null)) {
                        finalUrl = com.lagradost.cloudstream3.utils.ExtractorApiKt.fixUrl(gXtapes74k2, finalUrl);
                    }
                    java.lang.Object obj8 = obj3;
                    java.lang.String name = gXtapes74k2.getName();
                    java.lang.String it5 = gXtapes74k2.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType extractorLinkType = com.lagradost.cloudstream3.utils.ExtractorLinkType.M3U8;
                    anonymousClass13.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(links);
                    anonymousClass13.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass13.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                    anonymousClass13.L$3 = function15;
                    anonymousClass13.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response2);
                    anonymousClass13.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript);
                    anonymousClass13.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript2);
                    anonymousClass13.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(links2);
                    anonymousClass13.L$8 = obj4;
                    anonymousClass13.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(itKeys);
                    anonymousClass13.L$10 = it2;
                    anonymousClass13.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv);
                    anonymousClass13.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(it4);
                    anonymousClass13.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(finalUrl);
                    anonymousClass13.L$14 = function15;
                    anonymousClass13.I$0 = $i$f$forEach;
                    anonymousClass13.I$1 = 0;
                    anonymousClass13.label = 2;
                    it3 = it2;
                    function16 = function15;
                    int $i$f$forEach3 = $i$f$forEach;
                    java.lang.String finalUrl2 = finalUrl;
                    org.json.JSONObject obj9 = obj4;
                    java.lang.Object objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name, it5, finalUrl2, extractorLinkType, (kotlin.jvm.functions.Function2) null, anonymousClass13, 16, (java.lang.Object) null);
                    if (objNewExtractorLink$default == obj8) {
                        return obj8;
                    }
                    $i$f$forEach2 = $i$f$forEach3;
                    anonymousClass14 = anonymousClass13;
                    function17 = function16;
                    continuation2 = continuation3;
                    obj5 = obj9;
                    function18 = function13;
                    $result5 = objNewExtractorLink$default;
                    obj3 = obj8;
                    $result4 = $result6;
                    response = response2;
                    function17.invoke($result5);
                    $result3 = $result4;
                    function13 = function18;
                    obj4 = obj5;
                    $i$f$forEach = $i$f$forEach2;
                    anonymousClass13 = anonymousClass14;
                    it2 = it3;
                    function15 = function16;
                    if (it2.hasNext()) {
                        return kotlin.Unit.INSTANCE;
                    }
                }
                break;
            case 1:
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19 = (kotlin.jvm.functions.Function1) anonymousClass1.L$3;
                function13 = (kotlin.jvm.functions.Function1) anonymousClass1.L$2;
                referer2 = (java.lang.String) anonymousClass1.L$1;
                links = (java.lang.String) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result5);
                anonymousClass12 = anonymousClass1;
                $result = $result5;
                z = false;
                i = 2;
                function14 = function19;
                $result2 = coroutine_suspended;
                obj = $result;
                response = ((com.lagradost.nicehttp.NiceResponse) obj).getDocument();
                it = response.select("script").iterator();
                while (true) {
                    if (it.hasNext()) {
                    }
                }
                element = (org.jsoup.nodes.Element) obj2;
                if (element != null) {
                    break;
                }
                return kotlin.Unit.INSTANCE;
            case 2:
                int i2 = anonymousClass1.I$1;
                int $i$f$forEach4 = anonymousClass1.I$0;
                function17 = (kotlin.jvm.functions.Function1) anonymousClass1.L$14;
                java.lang.Object obj10 = anonymousClass1.L$11;
                java.util.Iterator<java.lang.String> it6 = (java.util.Iterator) anonymousClass1.L$10;
                java.util.Iterator<java.lang.String> it7 = (java.util.Iterator) anonymousClass1.L$9;
                org.json.JSONObject obj11 = (org.json.JSONObject) anonymousClass1.L$8;
                java.lang.String links4 = (java.lang.String) anonymousClass1.L$7;
                java.lang.String unpackedScript4 = (java.lang.String) anonymousClass1.L$6;
                java.lang.String script = (java.lang.String) anonymousClass1.L$5;
                org.jsoup.nodes.Document response3 = (org.jsoup.nodes.Document) anonymousClass1.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function110 = (kotlin.jvm.functions.Function1) anonymousClass1.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) anonymousClass1.L$2;
                java.lang.String referer3 = (java.lang.String) anonymousClass1.L$1;
                java.lang.String url2 = (java.lang.String) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result5);
                function16 = function110;
                gXtapes74k2 = gXtapes74k;
                links2 = links4;
                unpackedScript2 = unpackedScript4;
                it3 = it6;
                unpackedScript = script;
                function18 = function111;
                links = url2;
                $i$f$forEach2 = $i$f$forEach4;
                itKeys = it7;
                continuation2 = continuation;
                anonymousClass14 = anonymousClass1;
                $result4 = $result5;
                obj3 = coroutine_suspended;
                response = response3;
                obj5 = obj11;
                referer2 = referer3;
                function17.invoke($result5);
                $result3 = $result4;
                function13 = function18;
                obj4 = obj5;
                $i$f$forEach = $i$f$forEach2;
                anonymousClass13 = anonymousClass14;
                it2 = it3;
                function15 = function16;
                if (it2.hasNext()) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
