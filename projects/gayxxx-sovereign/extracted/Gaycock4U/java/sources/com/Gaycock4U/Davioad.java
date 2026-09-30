package com.Gaycock4U;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00004\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0010\u000b\n\u0002\b\b\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B%\u0012\b\b\u0002\u0010\u0002\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0004\u001a\u00020\u0003\u0012\b\b\u0002\u0010\u0005\u001a\u00020\u0006¢\u0006\u0004\b\u0007\u0010\bJH\u0010\u000e\u001a\u00020\u000f2\u0006\u0010\u0010\u001a\u00020\u00032\b\u0010\u0011\u001a\u0004\u0018\u00010\u00032\u0012\u0010\u0012\u001a\u000e\u0012\u0004\u0012\u00020\u0014\u0012\u0004\u0012\u00020\u000f0\u00132\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0016\u0012\u0004\u0012\u00020\u000f0\u0013H\u0096@¢\u0006\u0002\u0010\u0017R\u0014\u0010\u0002\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\nR\u0014\u0010\u0004\u001a\u00020\u0003X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\nR\u0014\u0010\u0005\u001a\u00020\u0006X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"Lcom/Gaycock4U/Davioad;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "name", "", "mainUrl", "requiresReferer", "", "<init>", "(Ljava/lang/String;Ljava/lang/String;Z)V", "getName", "()Ljava/lang/String;", "getMainUrl", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gaycock4U"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gaycock4U/Davioad\n+ 2 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 3 Iterators.kt\nkotlin/collections/CollectionsKt__IteratorsKt\n*L\n1#1,131:1\n1#2:132\n32#3,2:133\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gaycock4U/Davioad\n*L\n107#1:133,2\n*E\n"})
public final class Davioad extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name;
    private final boolean requiresReferer;

    /* JADX INFO: renamed from: com.Gaycock4U.Davioad$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Davioad", f = "Extractor.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {92, 114}, m = "getUrl", n = {"url", "referer", "subtitleCallback", "callback", "url", "referer", "subtitleCallback", "callback", "response", "script", "unpackedScript", "rawLinks", "links", "obj", "$this$forEach$iv", "element$iv", "key", "finalUrl", "$i$f$forEach", "$i$a$-forEach-Davioad$getUrl$2"}, nl = {93, 113}, s = {"L$0", "L$1", "L$2", "L$3", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$12", "L$13", "L$14", "I$0", "I$1"}, v = 2)
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gaycock4U.Davioad.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaycock4U.Davioad.this.getUrl(null, null, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    public Davioad() {
        this(null, null, false, 7, null);
    }

    public Davioad(@org.jetbrains.annotations.NotNull java.lang.String name, @org.jetbrains.annotations.NotNull java.lang.String mainUrl, boolean requiresReferer) {
        this.name = name;
        this.mainUrl = mainUrl;
        this.requiresReferer = requiresReferer;
    }

    public /* synthetic */ Davioad(java.lang.String str, java.lang.String str2, boolean z, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? "Davioad" : str, (i & 2) != 0 ? "https://davioad.com" : str2, (i & 4) != 0 ? false : z);
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

    /* JADX WARN: Path cross not found for [B:109:0x020c, B:62:0x0220], limit reached: 111 */
    /* JADX WARN: Removed duplicated region for block: B:112:0x0178 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:53:0x01e2 A[Catch: Exception -> 0x02ff, TRY_LEAVE, TryCatch #1 {Exception -> 0x02ff, blocks: (B:51:0x01dc, B:53:0x01e2), top: B:92:0x01dc }] */
    /* JADX WARN: Removed duplicated region for block: B:76:0x02f3  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /* JADX WARN: Removed duplicated region for block: B:95:0x0154 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:67:0x02a2 -> B:107:0x02ba). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) throws org.json.JSONException {
        com.Gaycock4U.Davioad.AnonymousClass1 anonymousClass1;
        com.Gaycock4U.Davioad davioad;
        com.lagradost.nicehttp.Requests app;
        boolean z;
        java.lang.Object $result;
        com.Gaycock4U.Davioad.AnonymousClass1 anonymousClass12;
        java.lang.Object obj;
        java.lang.Object obj2;
        int i;
        java.lang.String str;
        boolean z2;
        java.lang.String rawLinks;
        java.lang.String links;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        org.jsoup.nodes.Document response;
        java.util.Iterator it;
        java.lang.Object next;
        org.jsoup.nodes.Element element;
        java.lang.String script;
        java.lang.String unpackedScript;
        com.Gaycock4U.Davioad davioad2;
        java.lang.String unpackedScript2;
        java.lang.String links2;
        java.util.Iterator<java.lang.String> itKeys;
        com.Gaycock4U.Davioad.AnonymousClass1 anonymousClass13;
        java.lang.Object obj3;
        org.json.JSONObject obj4;
        int $i$f$forEach;
        kotlin.coroutines.Continuation<? super kotlin.Unit> continuation2;
        java.util.Iterator<java.lang.String> it2;
        java.lang.String key;
        org.jsoup.nodes.Document response2;
        java.lang.String script2;
        java.lang.String finalUrl;
        kotlin.coroutines.Continuation<? super kotlin.Unit> continuation3;
        java.lang.Object obj5;
        java.util.Iterator<java.lang.String> it3;
        int $i$f$forEach2;
        org.json.JSONObject obj6;
        com.Gaycock4U.Davioad.AnonymousClass1 anonymousClass14;
        java.lang.Object objNewExtractorLink$default;
        int $i$f$forEach3;
        org.json.JSONObject obj7;
        java.lang.Object obj8;
        java.lang.String rawLinks2;
        java.util.Iterator<java.lang.String> it4;
        java.lang.String script3;
        java.lang.String rawLinks3;
        com.Gaycock4U.Davioad davioad3;
        org.jsoup.nodes.Document response3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        kotlin.coroutines.Continuation<? super kotlin.Unit> continuation4 = continuation;
        if (continuation4 instanceof com.Gaycock4U.Davioad.AnonymousClass1) {
            anonymousClass1 = (com.Gaycock4U.Davioad.AnonymousClass1) continuation4;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                davioad = this;
            } else {
                davioad = this;
                anonymousClass1 = davioad.new AnonymousClass1(continuation4);
            }
        }
        java.lang.Object $result2 = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result2);
                try {
                    app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    anonymousClass1.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                    anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                    anonymousClass1.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                    anonymousClass1.L$3 = function12;
                    anonymousClass1.label = 1;
                    z = true;
                    $result = $result2;
                    anonymousClass12 = anonymousClass1;
                    obj = coroutine_suspended;
                    obj2 = null;
                    i = 2;
                    str = "";
                    z2 = false;
                } catch (java.lang.Exception e) {
                    e = e;
                    continuation4 = continuation;
                    $result2 = $result2;
                }
                try {
                    $result2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                } catch (java.lang.Exception e2) {
                    e = e2;
                    continuation4 = continuation;
                    anonymousClass1 = anonymousClass12;
                    $result2 = $result;
                    java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                    return kotlin.Unit.INSTANCE;
                }
                if ($result2 == obj) {
                    return obj;
                }
                rawLinks = url;
                links = referer;
                function13 = function1;
                function14 = function12;
                try {
                    response = ((com.lagradost.nicehttp.NiceResponse) $result2).getDocument();
                    it = response.select("script").iterator();
                    while (true) {
                        if (it.hasNext()) {
                            next = obj2;
                        } else {
                            try {
                                next = it.next();
                                org.jsoup.nodes.Element it5 = (org.jsoup.nodes.Element) next;
                                if (kotlin.text.StringsKt.contains$default(it5.data(), "eval", z2, i, obj2)) {
                                }
                            } catch (java.lang.Exception e3) {
                                e = e3;
                                continuation4 = continuation;
                                anonymousClass1 = anonymousClass12;
                                $result2 = $result;
                                java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                                return kotlin.Unit.INSTANCE;
                            }
                        }
                    }
                    element = (org.jsoup.nodes.Element) next;
                } catch (java.lang.Exception e4) {
                    e = e4;
                    continuation4 = continuation;
                    anonymousClass1 = anonymousClass12;
                    $result2 = $result;
                }
                if (element != null || (script = element.data()) == null) {
                    return kotlin.Unit.INSTANCE;
                }
                unpackedScript = com.lagradost.cloudstream3.utils.ExtractorApiKt.getAndUnpack(script);
                java.lang.String str2 = str;
                java.lang.String rawLinks4 = kotlin.text.StringsKt.substringBefore(kotlin.text.StringsKt.substringAfter(unpackedScript, "var links={", str2), "};", str2);
                if (rawLinks4.length() != 0) {
                    z = false;
                }
                if (z) {
                    return kotlin.Unit.INSTANCE;
                }
                java.lang.String links3 = '{' + rawLinks4 + '}';
                org.json.JSONObject obj9 = new org.json.JSONObject(links3);
                davioad2 = this;
                unpackedScript2 = rawLinks4;
                links2 = links3;
                itKeys = obj9.keys();
                anonymousClass13 = anonymousClass12;
                obj3 = obj;
                obj4 = obj9;
                $i$f$forEach = 0;
                continuation2 = continuation;
                it2 = itKeys;
                try {
                } catch (java.lang.Exception e5) {
                    e = e5;
                    continuation4 = continuation2;
                    anonymousClass1 = anonymousClass13;
                    $result2 = $result;
                }
                if (it2.hasNext()) {
                    try {
                        try {
                            java.lang.Object element$iv = it2.next();
                            key = (java.lang.String) element$iv;
                            if (!kotlin.text.StringsKt.startsWith$default(finalUrl, "http", false, 2, (java.lang.Object) null)) {
                                try {
                                    finalUrl = com.lagradost.cloudstream3.utils.ExtractorApiKt.fixUrl(davioad2, finalUrl);
                                } catch (java.lang.Exception e6) {
                                    e = e6;
                                    continuation4 = continuation3;
                                    anonymousClass1 = anonymousClass13;
                                    $result2 = $result;
                                    java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                                    return kotlin.Unit.INSTANCE;
                                }
                            }
                            java.lang.String name = davioad2.getName();
                            obj5 = obj3;
                            java.lang.String name2 = davioad2.getName();
                            com.lagradost.cloudstream3.utils.ExtractorLinkType extractorLinkType = com.lagradost.cloudstream3.utils.ExtractorLinkType.M3U8;
                            anonymousClass13.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(rawLinks);
                            anonymousClass13.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(links);
                            anonymousClass13.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                            anonymousClass13.L$3 = function14;
                            anonymousClass13.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response2);
                            anonymousClass13.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(script2);
                            anonymousClass13.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript);
                            anonymousClass13.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript2);
                            anonymousClass13.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(links2);
                            anonymousClass13.L$9 = obj4;
                            anonymousClass13.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(itKeys);
                            anonymousClass13.L$11 = it2;
                            anonymousClass13.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv);
                            anonymousClass13.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(key);
                            anonymousClass13.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(finalUrl);
                            anonymousClass13.L$15 = function14;
                            anonymousClass13.I$0 = $i$f$forEach;
                            anonymousClass13.I$1 = 0;
                            anonymousClass13.label = 2;
                            objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name, name2, finalUrl, extractorLinkType, (kotlin.jvm.functions.Function2) null, anonymousClass14, 16, (java.lang.Object) null);
                        } catch (java.lang.Exception e7) {
                            e = e7;
                            continuation4 = continuation3;
                            anonymousClass1 = anonymousClass14;
                            $result2 = $result;
                            java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                            return kotlin.Unit.INSTANCE;
                        }
                        it3 = it2;
                        $i$f$forEach2 = $i$f$forEach;
                        obj6 = obj4;
                        anonymousClass14 = anonymousClass13;
                    } catch (java.lang.Exception e8) {
                        e = e8;
                        continuation4 = continuation3;
                        anonymousClass1 = anonymousClass13;
                        $result2 = $result;
                    }
                    response2 = response;
                    script2 = script;
                    finalUrl = obj4.getString(key);
                    continuation3 = continuation2;
                    if (objNewExtractorLink$default == obj5) {
                        return obj5;
                    }
                    $i$f$forEach3 = $i$f$forEach2;
                    obj7 = obj6;
                    obj8 = obj5;
                    $result2 = objNewExtractorLink$default;
                    rawLinks2 = unpackedScript2;
                    it4 = itKeys;
                    continuation4 = continuation3;
                    script3 = script2;
                    rawLinks3 = unpackedScript;
                    davioad3 = davioad2;
                    response3 = response2;
                    function15 = function14;
                    try {
                        function15.invoke($result2);
                        continuation2 = continuation4;
                        obj3 = obj8;
                        $i$f$forEach = $i$f$forEach3;
                        obj4 = obj7;
                        anonymousClass13 = anonymousClass14;
                        unpackedScript = rawLinks3;
                        script = script3;
                        response = response3;
                        davioad2 = davioad3;
                        it2 = it3;
                        unpackedScript2 = rawLinks2;
                        itKeys = it4;
                    } catch (java.lang.Exception e9) {
                        e = e9;
                        anonymousClass1 = anonymousClass14;
                        $result2 = $result;
                        java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                        return kotlin.Unit.INSTANCE;
                    }
                    if (it2.hasNext()) {
                        return kotlin.Unit.INSTANCE;
                    }
                    break;
                }
                break;
                break;
            case 1:
                function14 = (kotlin.jvm.functions.Function1) anonymousClass1.L$3;
                function13 = (kotlin.jvm.functions.Function1) anonymousClass1.L$2;
                links = (java.lang.String) anonymousClass1.L$1;
                rawLinks = (java.lang.String) anonymousClass1.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result2);
                    str = "";
                    anonymousClass12 = anonymousClass1;
                    $result = $result2;
                    obj = coroutine_suspended;
                    z2 = false;
                    obj2 = null;
                    i = 2;
                    z = true;
                    response = ((com.lagradost.nicehttp.NiceResponse) $result2).getDocument();
                    it = response.select("script").iterator();
                    while (true) {
                        if (it.hasNext()) {
                        }
                    }
                    element = (org.jsoup.nodes.Element) next;
                    if (element != null) {
                        break;
                    }
                    return kotlin.Unit.INSTANCE;
                } catch (java.lang.Exception e10) {
                    e = e10;
                    java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                    return kotlin.Unit.INSTANCE;
                }
            case 2:
                int i2 = anonymousClass1.I$1;
                int $i$f$forEach4 = anonymousClass1.I$0;
                function15 = (kotlin.jvm.functions.Function1) anonymousClass1.L$15;
                java.lang.Object obj10 = anonymousClass1.L$12;
                java.util.Iterator<java.lang.String> it6 = (java.util.Iterator) anonymousClass1.L$11;
                java.util.Iterator<java.lang.String> it7 = (java.util.Iterator) anonymousClass1.L$10;
                org.json.JSONObject obj11 = (org.json.JSONObject) anonymousClass1.L$9;
                java.lang.String links4 = (java.lang.String) anonymousClass1.L$8;
                java.lang.String rawLinks5 = (java.lang.String) anonymousClass1.L$7;
                rawLinks3 = (java.lang.String) anonymousClass1.L$6;
                script3 = (java.lang.String) anonymousClass1.L$5;
                response3 = (org.jsoup.nodes.Document) anonymousClass1.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = (kotlin.jvm.functions.Function1) anonymousClass1.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) anonymousClass1.L$2;
                java.lang.String referer2 = (java.lang.String) anonymousClass1.L$1;
                java.lang.String url2 = (java.lang.String) anonymousClass1.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result2);
                    anonymousClass14 = anonymousClass1;
                    rawLinks2 = rawLinks5;
                    it4 = it7;
                    rawLinks = url2;
                    obj7 = obj11;
                    links2 = links4;
                    function13 = function17;
                    links = referer2;
                    $result = $result2;
                    it3 = it6;
                    $i$f$forEach3 = $i$f$forEach4;
                    function14 = function16;
                    davioad3 = davioad;
                    obj8 = coroutine_suspended;
                    function15.invoke($result2);
                    continuation2 = continuation4;
                    obj3 = obj8;
                    $i$f$forEach = $i$f$forEach3;
                    obj4 = obj7;
                    anonymousClass13 = anonymousClass14;
                    unpackedScript = rawLinks3;
                    script = script3;
                    response = response3;
                    davioad2 = davioad3;
                    it2 = it3;
                    unpackedScript2 = rawLinks2;
                    itKeys = it4;
                    if (it2.hasNext()) {
                    }
                } catch (java.lang.Exception e11) {
                    e = e11;
                    java.lang.System.out.println((java.lang.Object) ("❌ Lỗi khi parse Davioad: " + e.getMessage()));
                    return kotlin.Unit.INSTANCE;
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
