package com.Jayboys;

/* JADX INFO: compiled from: Javboys3.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\u0088\u0001\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\f\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010$\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001a\u0010-\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\u00050$H\u0082@¢\u0006\u0002\u0010.J\u001e\u0010+\u001a\u00020/2\u0006\u00100\u001a\u0002012\u0006\u00102\u001a\u000203H\u0096@¢\u0006\u0002\u00104J\f\u00105\u001a\u000206*\u000207H\u0002J\u000e\u00108\u001a\u0004\u0018\u000106*\u000207H\u0002J\u001c\u00109\u001a\b\u0012\u0004\u0012\u0002060)2\u0006\u0010:\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010;J\u0016\u0010<\u001a\u00020=2\u0006\u0010>\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010;JF\u0010?\u001a\u00020\u000e2\u0006\u0010@\u001a\u00020\u00052\u0006\u0010A\u001a\u00020\u000e2\u0012\u0010B\u001a\u000e\u0012\u0004\u0012\u00020D\u0012\u0004\u0012\u00020E0C2\u0012\u0010F\u001a\u000e\u0012\u0004\u0012\u00020G\u0012\u0004\u0012\u00020E0CH\u0096@¢\u0006\u0002\u0010HR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u0014\u0010\u0014\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0014\u0010\u0016\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0010R\u0014\u0010\u0018\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0010R\u001a\u0010\u001a\u001a\b\u0012\u0004\u0012\u00020\u001c0\u001bX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001d\u0010\u001eR\u0014\u0010\u001f\u001a\u00020 X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b!\u0010\"R\u001a\u0010#\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\u00050$X\u0082\u0004¢\u0006\u0002\n\u0000R\u000e\u0010%\u001a\u00020&X\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010'\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\u00050$X\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010(\u001a\b\u0012\u0004\u0012\u00020*0)X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b+\u0010,¨\u0006I"}, d2 = {"Lcom/Jayboys/Jayboys3;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "hasDownloadSupport", "getHasDownloadSupport", "hasChromecastSupport", "getHasChromecastSupport", "hasQuickSearch", "getHasQuickSearch", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "formData", "", "cfKiller", "Lcom/lagradost/cloudstream3/network/CloudflareKiller;", "headers", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "getCookiesAfterAgeGate", "(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nJavboys3.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Javboys3.kt\ncom/Jayboys/Jayboys3\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 4 _Sequences.kt\nkotlin/sequences/SequencesKt___SequencesKt\n*L\n1#1,241:1\n1642#2,10:242\n1915#2:252\n1916#2:254\n1652#2:255\n1642#2,10:256\n1915#2:266\n1916#2:268\n1652#2:269\n1642#2,10:270\n1915#2:280\n1916#2:282\n1652#2:283\n1915#2:284\n1916#2:286\n1915#2,2:287\n1915#2,2:289\n1915#2,2:291\n1915#2,2:295\n1586#2:297\n1661#2,3:298\n777#2:301\n873#2,2:302\n1#3:253\n1#3:267\n1#3:281\n1#3:285\n1342#4,2:293\n*S KotlinDebug\n*F\n+ 1 Javboys3.kt\ncom/Jayboys/Jayboys3\n*L\n82#1:242,10\n82#1:252\n82#1:254\n82#1:255\n124#1:256,10\n124#1:266\n124#1:268\n124#1:269\n146#1:270,10\n146#1:280\n146#1:282\n146#1:283\n174#1:284\n174#1:286\n187#1:287,2\n192#1:289,2\n197#1:291,2\n208#1:295,2\n217#1:297\n217#1:298,3\n218#1:301\n218#1:302,2\n82#1:253\n124#1:267\n146#1:281\n203#1:293,2\n*E\n"})
public final class Jayboys3 extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://www.javboys.tv";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Javboys🍑🍑";
    private final boolean hasMainPage = true;

    @org.jetbrains.annotations.NotNull
    private java.lang.String lang = "en";
    private final boolean hasDownloadSupport = true;
    private final boolean hasChromecastSupport = true;
    private final boolean hasQuickSearch = true;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.util.Map<java.lang.String, java.lang.String> formData = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("age_gate[age]", "9MRd26N84fSy3NwprhoXtg=="), kotlin.TuplesKt.to("age_gate[lang]", "en"), kotlin.TuplesKt.to("age_gate[confirm]", "1"), kotlin.TuplesKt.to("age_gate[remember]", "1")});

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.network.CloudflareKiller cfKiller = new com.lagradost.cloudstream3.network.CloudflareKiller();

    @org.jetbrains.annotations.NotNull
    private final java.util.Map<java.lang.String, java.lang.String> headers = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"), kotlin.TuplesKt.to("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"), kotlin.TuplesKt.to("Accept-Language", "en-US,en;q=0.5"), kotlin.TuplesKt.to("Connection", "keep-alive"), kotlin.TuplesKt.to("Referer", "url")});

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("/2026/06/", "Latest Updates"), kotlin.TuplesKt.to("/2026/05/", "26May"), kotlin.TuplesKt.to("/2026/04/", "26April"), kotlin.TuplesKt.to("/category/onlyfans/fansone-co/", "Fansone")});

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$getCookiesAfterAgeGate$1, reason: invalid class name */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3", f = "Javboys3.kt", i = {0}, l = {55}, m = "getCookiesAfterAgeGate", n = {"ua"}, nl = {63}, s = {"L$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.Jayboys3.this.getCookiesAfterAgeGate((kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$getMainPage$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3", f = "Javboys3.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1}, l = {78, 80}, m = "getMainPage", n = {"request", "url", "ua", "page", "request", "url", "ua", "cookies", "page"}, nl = {80, 82}, s = {"L$0", "L$1", "L$2", "I$0", "L$0", "L$1", "L$2", "L$3", "I$0"}, v = 2)
    static final class C00101 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        int label;
        /* synthetic */ java.lang.Object result;

        C00101(kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.C00101> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.Jayboys3.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3", f = "Javboys3.kt", i = {0, 1, 1, 1, 1, 1, 1}, l = {140, 150}, m = "load", n = {"url", "url", "document", "title", "poster", "description", "recommendations"}, nl = {142, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5"}, v = 2)
    static final class C00111 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        int label;
        /* synthetic */ java.lang.Object result;

        C00111(kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.C00111> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.Jayboys3.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3", f = "Javboys3.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {164, 222}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "response", "document", "pageText", "found", "videoUrls", "iframeSrc", "dataVideoRegex", "filteredUrls", "isCasting"}, nl = {165, 238}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "Z$0"}, v = 2)
    static final class C00121 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
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
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00121(kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.C00121> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.Jayboys3.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3", f = "Javboys3.kt", i = {0, 0, 0}, l = {122}, m = "search", n = {"query", "searchResponse", "i"}, nl = {124}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class C00131 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00131(kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.C00131> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.Jayboys3.this.search(null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public void setMainUrl(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.mainUrl = str;
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getName() {
        return this.name;
    }

    public void setName(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.name = str;
    }

    public boolean getHasMainPage() {
        return this.hasMainPage;
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getLang() {
        return this.lang;
    }

    public void setLang(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.lang = str;
    }

    public boolean getHasDownloadSupport() {
        return this.hasDownloadSupport;
    }

    public boolean getHasChromecastSupport() {
        return this.hasChromecastSupport;
    }

    public boolean getHasQuickSearch() {
        return this.hasQuickSearch;
    }

    @org.jetbrains.annotations.NotNull
    public java.util.Set<com.lagradost.cloudstream3.TvType> getSupportedTypes() {
        return this.supportedTypes;
    }

    @org.jetbrains.annotations.NotNull
    public com.lagradost.cloudstream3.VPNStatus getVpnStatus() {
        return this.vpnStatus;
    }

    @org.jetbrains.annotations.NotNull
    public java.util.List<com.lagradost.cloudstream3.MainPageData> getMainPage() {
        return this.mainPage;
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public final java.lang.Object getCookiesAfterAgeGate(kotlin.coroutines.Continuation<? super java.util.Map<java.lang.String, java.lang.String>> continuation) {
        com.Jayboys.Jayboys3.AnonymousClass1 anonymousClass1;
        if (continuation instanceof com.Jayboys.Jayboys3.AnonymousClass1) {
            anonymousClass1 = (com.Jayboys.Jayboys3.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Jayboys.Jayboys3.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.Map ua = kotlin.collections.MapsKt.mapOf(kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"));
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.lang.String mainUrl = getMainUrl();
                java.util.Map<java.lang.String, java.lang.String> map = this.formData;
                okhttp3.Interceptor interceptor = this.cfKiller;
                anonymousClass1.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua);
                anonymousClass1.label = 1;
                $result = com.lagradost.nicehttp.Requests.post$default(app, mainUrl, ua, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, map, (java.util.List) null, (java.lang.Object) null, (okhttp3.RequestBody) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, interceptor, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 57308, (java.lang.Object) null);
                if ($result == coroutine_suspended) {
                    return coroutine_suspended;
                }
                break;
            case 1:
                kotlin.ResultKt.throwOnFailure($result);
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) $result;
        return response.getCookies();
    }

    /* JADX WARN: Removed duplicated region for block: B:27:0x018d A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:28:0x018e  */
    /* JADX WARN: Removed duplicated region for block: B:32:0x01b6  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x01e0  */
    /* JADX WARN: Removed duplicated region for block: B:39:0x01e2  */
    /* JADX WARN: Removed duplicated region for block: B:42:0x01f1  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getMainPage(int page, @org.jetbrains.annotations.NotNull com.lagradost.cloudstream3.MainPageRequest request, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.HomePageResponse> continuation) {
        com.Jayboys.Jayboys3.C00101 c00101;
        java.lang.Object cookiesAfterAgeGate;
        java.lang.Object obj;
        java.lang.String url;
        java.util.Map ua;
        com.lagradost.cloudstream3.MainPageRequest request2;
        java.lang.Object obj2;
        boolean z;
        com.lagradost.cloudstream3.MainPageRequest request3;
        boolean hasNext;
        int page2 = page;
        if (continuation instanceof com.Jayboys.Jayboys3.C00101) {
            c00101 = (com.Jayboys.Jayboys3.C00101) continuation;
            if ((c00101.label & Integer.MIN_VALUE) != 0) {
                c00101.label -= Integer.MIN_VALUE;
            } else {
                c00101 = new com.Jayboys.Jayboys3.C00101(continuation);
            }
        }
        java.lang.Object $result = c00101.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00101.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String str = ((!kotlin.text.StringsKt.startsWith$default(request.getData(), "/category/", false, 2, (java.lang.Object) null) || page2 <= 1) && page2 <= 1) ? getMainUrl() + request.getData() : getMainUrl() + request.getData() + "page/" + page2 + '/';
                java.lang.String url2 = str;
                java.util.Map ua2 = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"), kotlin.TuplesKt.to("Referer", getMainUrl() + '/')});
                c00101.L$0 = request;
                c00101.L$1 = url2;
                c00101.L$2 = ua2;
                c00101.I$0 = page2;
                c00101.label = 1;
                cookiesAfterAgeGate = getCookiesAfterAgeGate(c00101);
                if (cookiesAfterAgeGate == coroutine_suspended) {
                    return coroutine_suspended;
                }
                obj = coroutine_suspended;
                url = url2;
                ua = ua2;
                request2 = request;
                java.util.Map cookies = (java.util.Map) cookiesAfterAgeGate;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                okhttp3.Interceptor interceptor = this.cfKiller;
                c00101.L$0 = request2;
                c00101.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                c00101.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua);
                c00101.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(cookies);
                c00101.I$0 = page2;
                c00101.label = 2;
                com.lagradost.cloudstream3.MainPageRequest request4 = request2;
                obj2 = obj;
                z = false;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, ua, (java.lang.String) null, (java.util.Map) null, cookies, false, 0, (java.util.concurrent.TimeUnit) null, 0L, interceptor, false, (com.lagradost.nicehttp.ResponseParser) null, c00101, 3564, (java.lang.Object) null);
                if ($result != obj2) {
                    return obj2;
                }
                request3 = request4;
                org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv = document.select("div.list-item div.video.col-2");
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                    org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
                    if (searchResult != null) {
                        destination$iv$iv.add(searchResult);
                    }
                }
                java.util.List home = (java.util.List) destination$iv$iv;
                hasNext = document.selectFirst("a.next.page-numbers") == null;
                com.lagradost.cloudstream3.HomePageList homePageList = new com.lagradost.cloudstream3.HomePageList(request3.getName(), home, true);
                if (hasNext) {
                    z = true;
                }
                return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(homePageList, kotlin.coroutines.jvm.internal.Boxing.boxBoolean(z));
            case 1:
                page2 = c00101.I$0;
                java.util.Map ua3 = (java.util.Map) c00101.L$2;
                java.lang.String url3 = (java.lang.String) c00101.L$1;
                com.lagradost.cloudstream3.MainPageRequest request5 = (com.lagradost.cloudstream3.MainPageRequest) c00101.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                url = url3;
                ua = ua3;
                request2 = request5;
                cookiesAfterAgeGate = $result;
                java.util.Map cookies2 = (java.util.Map) cookiesAfterAgeGate;
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                okhttp3.Interceptor interceptor2 = this.cfKiller;
                c00101.L$0 = request2;
                c00101.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                c00101.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua);
                c00101.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(cookies2);
                c00101.I$0 = page2;
                c00101.label = 2;
                com.lagradost.cloudstream3.MainPageRequest request42 = request2;
                obj2 = obj;
                z = false;
                $result = com.lagradost.nicehttp.Requests.get$default(app2, url, ua, (java.lang.String) null, (java.util.Map) null, cookies2, false, 0, (java.util.concurrent.TimeUnit) null, 0L, interceptor2, false, (com.lagradost.nicehttp.ResponseParser) null, c00101, 3564, (java.lang.Object) null);
                if ($result != obj2) {
                }
                break;
            case 2:
                int i = c00101.I$0;
                request3 = (com.lagradost.cloudstream3.MainPageRequest) c00101.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                z = false;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("div.list-item div.video.col-2");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                while (r15.hasNext()) {
                }
                java.util.List home2 = (java.util.List) destination$iv$iv2;
                if (document2.selectFirst("a.next.page-numbers") == null) {
                }
                com.lagradost.cloudstream3.HomePageList homePageList2 = new com.lagradost.cloudstream3.HomePageList(request3.getName(), home2, true);
                if (hasNext) {
                }
                return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(homePageList2, kotlin.coroutines.jvm.internal.Boxing.boxBoolean(z));
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String string;
        java.lang.String strAttr;
        java.lang.String string2;
        java.lang.String strAttr2;
        java.lang.String string3;
        java.lang.String strText;
        org.jsoup.nodes.Element elementSelectFirst = $this$toSearchResult.selectFirst("a.denomination span.title");
        final java.lang.String posterUrl = "";
        if (elementSelectFirst == null || (strText = elementSelectFirst.text()) == null || (string = kotlin.text.StringsKt.trim(strText).toString()) == null) {
            string = "";
        }
        java.lang.String title = string;
        org.jsoup.nodes.Element elementSelectFirst2 = $this$toSearchResult.selectFirst("a.thumb-video");
        java.lang.String href = (elementSelectFirst2 == null || (strAttr2 = elementSelectFirst2.attr("href")) == null || (string3 = kotlin.text.StringsKt.trim(strAttr2).toString()) == null) ? "" : string3;
        org.jsoup.nodes.Element elementSelectFirst3 = $this$toSearchResult.selectFirst("a.thumb-video img");
        if (elementSelectFirst3 != null && (strAttr = elementSelectFirst3.attr("src")) != null && (string2 = kotlin.text.StringsKt.trim(strAttr).toString()) != null) {
            posterUrl = string2;
        }
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.Jayboys.Jayboys3$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.Jayboys.Jayboys3.toSearchResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        java.lang.String string;
        java.lang.String strAttr;
        java.lang.String string2;
        java.lang.String strAttr2;
        java.lang.String string3;
        java.lang.String strText;
        org.jsoup.nodes.Element elementSelectFirst = $this$toRecommendResult.selectFirst("a.denomination span.title");
        final java.lang.String posterUrl = "";
        if (elementSelectFirst == null || (strText = elementSelectFirst.text()) == null || (string = kotlin.text.StringsKt.trim(strText).toString()) == null) {
            string = "";
        }
        java.lang.String title = string;
        org.jsoup.nodes.Element elementSelectFirst2 = $this$toRecommendResult.selectFirst("a.thumb-video");
        java.lang.String href = (elementSelectFirst2 == null || (strAttr2 = elementSelectFirst2.attr("href")) == null || (string3 = kotlin.text.StringsKt.trim(strAttr2).toString()) == null) ? "" : string3;
        org.jsoup.nodes.Element elementSelectFirst3 = $this$toRecommendResult.selectFirst("a.thumb-video img");
        if (elementSelectFirst3 != null && (strAttr = elementSelectFirst3.attr("src")) != null && (string2 = kotlin.text.StringsKt.trim(strAttr).toString()) != null) {
            posterUrl = string2;
        }
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.Jayboys.Jayboys3$$ExternalSyntheticLambda1
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.Jayboys.Jayboys3.toRecommendResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toRecommendResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:16:0x0063  */
    /* JADX WARN: Removed duplicated region for block: B:23:0x00f7  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0126  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x0144  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:19:0x00ca -> B:20:0x00d3). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        com.Jayboys.Jayboys3.C00131 c00131;
        com.Jayboys.Jayboys3 jayboys3;
        java.util.List searchResponse;
        com.Jayboys.Jayboys3.C00131 c001312;
        com.Jayboys.Jayboys3 jayboys32;
        java.lang.String query2;
        int i;
        java.util.List results;
        if (continuation instanceof com.Jayboys.Jayboys3.C00131) {
            c00131 = (com.Jayboys.Jayboys3.C00131) continuation;
            if ((c00131.label & Integer.MIN_VALUE) != 0) {
                c00131.label -= Integer.MIN_VALUE;
                jayboys3 = this;
            } else {
                jayboys3 = this;
                c00131 = jayboys3.new C00131(continuation);
            }
        }
        java.lang.Object $result = c00131.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00131.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.List searchResponse2 = new java.util.ArrayList();
                searchResponse = searchResponse2;
                int i2 = 1;
                com.Jayboys.Jayboys3 jayboys33 = jayboys3;
                com.Jayboys.Jayboys3.C00131 c001313 = c00131;
                java.lang.String query3 = query;
                if (i2 >= 6) {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = jayboys33.getMainUrl() + "/page/" + i2 + "/?s=" + query3;
                    c001313.L$0 = query3;
                    c001313.L$1 = searchResponse;
                    c001313.I$0 = i2;
                    c001313.label = 1;
                    int i3 = i2;
                    java.util.List searchResponse3 = searchResponse;
                    c001312 = c001313;
                    java.lang.Object obj = coroutine_suspended;
                    java.lang.String query4 = query3;
                    $result = com.lagradost.nicehttp.Requests.get$default(app, str, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c001312, 4094, (java.lang.Object) null);
                    if ($result == obj) {
                        return obj;
                    }
                    coroutine_suspended = obj;
                    jayboys32 = jayboys33;
                    searchResponse = searchResponse3;
                    query2 = query4;
                    i = i3;
                    org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.Iterable $this$mapNotNull$iv = document.select("div.list-item div.video.col-2");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                        java.lang.String query5 = query2;
                        org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                        com.lagradost.cloudstream3.SearchResponse searchResult = jayboys32.toSearchResult(it);
                        if (searchResult != null) {
                            destination$iv$iv.add(searchResult);
                        }
                        query2 = query5;
                    }
                    java.lang.String query6 = query2;
                    results = (java.util.List) destination$iv$iv;
                    if (!searchResponse.containsAll(results)) {
                        searchResponse.addAll(results);
                        if (!results.isEmpty()) {
                            i2 = i + 1;
                            jayboys33 = jayboys32;
                            c001313 = c001312;
                            query3 = query6;
                            if (i2 >= 6) {
                                return searchResponse;
                            }
                        }
                    }
                    return searchResponse;
                }
                break;
            case 1:
                i = c00131.I$0;
                searchResponse = (java.util.List) c00131.L$1;
                java.lang.String query7 = (java.lang.String) c00131.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c001312 = c00131;
                query2 = query7;
                jayboys32 = jayboys3;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("div.list-item div.video.col-2");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                while (r15.hasNext()) {
                }
                java.lang.String query62 = query2;
                results = (java.util.List) destination$iv$iv2;
                if (!searchResponse.containsAll(results)) {
                }
                return searchResponse;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object load(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.LoadResponse> continuation) {
        com.Jayboys.Jayboys3.C00111 c00111;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        if (continuation instanceof com.Jayboys.Jayboys3.C00111) {
            c00111 = (com.Jayboys.Jayboys3.C00111) continuation;
            if ((c00111.label & Integer.MIN_VALUE) != 0) {
                c00111.label -= Integer.MIN_VALUE;
            } else {
                c00111 = new com.Jayboys.Jayboys3.C00111(continuation);
            }
        }
        com.Jayboys.Jayboys3.C00111 c001112 = c00111;
        java.lang.Object $result = c001112.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c001112.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.util.Map<java.lang.String, java.lang.String> map = this.headers;
                okhttp3.Interceptor interceptor = this.cfKiller;
                c001112.L$0 = url;
                c001112.label = 1;
                obj = coroutine_suspended;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, map, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, interceptor, false, (com.lagradost.nicehttp.ResponseParser) null, c001112, 3580, (java.lang.Object) null);
                c001112 = c001112;
                if (obj2 == obj) {
                    return obj;
                }
                url2 = url;
                break;
                break;
            case 1:
                java.lang.String url3 = (java.lang.String) c001112.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                url2 = url3;
                obj2 = $result;
                break;
            case 2:
                kotlin.ResultKt.throwOnFailure($result);
                return $result;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
        org.jsoup.nodes.Element elementSelectFirst = document.selectFirst("meta[property=og:title]");
        java.lang.String title = java.lang.String.valueOf((elementSelectFirst == null || (strAttr2 = elementSelectFirst.attr("content")) == null) ? null : kotlin.text.StringsKt.trim(strAttr2).toString());
        com.Jayboys.Jayboys3 jayboys3 = this;
        org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("[property='og:image']");
        java.lang.String poster = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(jayboys3, elementSelectFirst2 != null ? elementSelectFirst2.attr("content") : null);
        org.jsoup.nodes.Element elementSelectFirst3 = document.selectFirst("meta[property=og:description]");
        java.lang.String description = (elementSelectFirst3 == null || (strAttr = elementSelectFirst3.attr("content")) == null) ? null : kotlin.text.StringsKt.trim(strAttr).toString();
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.list-item div.video.col-2");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse recommendResult = toRecommendResult(it);
            if (recommendResult != null) {
                destination$iv$iv.add(recommendResult);
            }
        }
        java.util.List recommendations = (java.util.List) destination$iv$iv;
        com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.NSFW;
        com.Jayboys.Jayboys3.AnonymousClass2 anonymousClass2 = new com.Jayboys.Jayboys3.AnonymousClass2(poster, description, recommendations, null);
        c001112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        c001112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
        c001112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
        c001112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
        c001112.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
        c001112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
        c001112.label = 2;
        java.lang.Object objNewMovieLoadResponse = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType, url2, anonymousClass2, c001112);
        return objNewMovieLoadResponse == obj ? obj : objNewMovieLoadResponse;
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3$load$2", f = "Javboys3.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list, kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$recommendations = list;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Jayboys.Jayboys3.AnonymousClass2(this.$poster, this.$description, this.$recommendations, continuation);
            anonymousClass2.L$0 = obj;
            return anonymousClass2;
        }

        public final java.lang.Object invoke(com.lagradost.cloudstream3.MovieLoadResponse movieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
            return create(movieLoadResponse, continuation).invokeSuspend(kotlin.Unit.INSTANCE);
        }

        public final java.lang.Object invokeSuspend(java.lang.Object $result) {
            com.lagradost.cloudstream3.MovieLoadResponse $this$newMovieLoadResponse = (com.lagradost.cloudstream3.MovieLoadResponse) this.L$0;
            kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
            switch (this.label) {
                case 0:
                    kotlin.ResultKt.throwOnFailure($result);
                    $this$newMovieLoadResponse.setPosterUrl(this.$poster);
                    $this$newMovieLoadResponse.setPlot(this.$description);
                    $this$newMovieLoadResponse.setRecommendations(this.$recommendations);
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:154:0x0159 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:156:0x0151 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:159:0x01ee A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:21:0x010d  */
    /* JADX WARN: Removed duplicated region for block: B:36:0x0147  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x014b  */
    /* JADX WARN: Removed duplicated region for block: B:71:0x01e3  */
    /* JADX WARN: Removed duplicated region for block: B:73:0x01e7  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.Jayboys.Jayboys3.C00121 c00121;
        java.lang.Object obj;
        com.Jayboys.Jayboys3.C00121 c001212;
        java.lang.String data2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        boolean isCasting2;
        java.lang.Iterable $this$forEach$iv;
        java.util.Iterator it;
        java.lang.String data3;
        kotlin.jvm.internal.Ref.BooleanRef found;
        java.lang.String str;
        boolean z;
        java.lang.String it2;
        boolean z2;
        if (continuation instanceof com.Jayboys.Jayboys3.C00121) {
            c00121 = (com.Jayboys.Jayboys3.C00121) continuation;
            if ((c00121.label & Integer.MIN_VALUE) != 0) {
                c00121.label -= Integer.MIN_VALUE;
            } else {
                c00121 = new com.Jayboys.Jayboys3.C00121(continuation);
            }
        }
        java.lang.Object $result = c00121.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00121.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.util.Map<java.lang.String, java.lang.String> map = this.headers;
                okhttp3.Interceptor interceptor = this.cfKiller;
                c00121.L$0 = data;
                c00121.L$1 = function1;
                c00121.L$2 = function12;
                c00121.Z$0 = isCasting;
                c00121.label = 1;
                com.Jayboys.Jayboys3.C00121 c001213 = c00121;
                obj = coroutine_suspended;
                java.lang.Object obj3 = com.lagradost.nicehttp.Requests.get$default(app, data, map, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, interceptor, false, (com.lagradost.nicehttp.ResponseParser) null, c001213, 3580, (java.lang.Object) null);
                c001212 = c001213;
                if (obj3 == obj) {
                    return obj;
                }
                data2 = data;
                function13 = function1;
                function14 = function12;
                obj2 = obj3;
                isCasting2 = isCasting;
                com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Document document = response.getDocument();
                java.lang.String pageText = response.getText();
                kotlin.jvm.internal.Ref.BooleanRef found2 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.util.Set videoUrls = new java.util.LinkedHashSet();
                $this$forEach$iv = document.select("div#player, div.video-player");
                it = $this$forEach$iv.iterator();
                while (true) {
                    java.lang.String u = "data-src";
                    java.lang.Iterable $this$forEach$iv2 = $this$forEach$iv;
                    if (it.hasNext()) {
                        org.jsoup.nodes.Element elementSelectFirst = document.selectFirst("iframe[src]");
                        java.lang.String iframeSrc = elementSelectFirst != null ? elementSelectFirst.attr("src") : null;
                        if (iframeSrc != null) {
                            kotlin.coroutines.jvm.internal.Boxing.boxBoolean(videoUrls.add(iframeSrc));
                        }
                        org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("div.download-button-wrapper a[href]");
                        if (elementSelectFirst2 != null) {
                            data3 = data2;
                            java.lang.String it3 = elementSelectFirst2.attr("href");
                            if (it3 != null) {
                                kotlin.coroutines.jvm.internal.Boxing.boxBoolean(videoUrls.add(it3));
                            }
                        } else {
                            data3 = data2;
                        }
                        java.lang.Iterable $this$forEach$iv3 = document.select("[data-src]");
                        for (java.lang.Object element$iv : $this$forEach$iv3) {
                            java.lang.Iterable $this$forEach$iv4 = $this$forEach$iv3;
                            org.jsoup.nodes.Element el = (org.jsoup.nodes.Element) element$iv;
                            java.lang.String u2 = el.attr(u);
                            java.lang.String str2 = u2;
                            if (str2 == null || kotlin.text.StringsKt.isBlank(str2)) {
                                str = u;
                            } else {
                                str = u;
                                z = kotlin.jvm.internal.Intrinsics.areEqual(u2, "#") ? false : true;
                                if (!z) {
                                    u2 = null;
                                }
                                if (u2 == null) {
                                    videoUrls.add(u2);
                                }
                                $this$forEach$iv3 = $this$forEach$iv4;
                                u = str;
                            }
                            if (!z) {
                            }
                            if (u2 == null) {
                            }
                            $this$forEach$iv3 = $this$forEach$iv4;
                            u = str;
                        }
                        java.lang.Iterable $this$forEach$iv5 = document.select("[src]");
                        for (java.lang.Object element$iv2 : $this$forEach$iv5) {
                            java.lang.Iterable $this$forEach$iv6 = $this$forEach$iv5;
                            org.jsoup.nodes.Element el2 = (org.jsoup.nodes.Element) element$iv2;
                            java.lang.String u3 = el2.attr("src");
                            java.lang.String str3 = u3;
                            if (str3 == null || kotlin.text.StringsKt.isBlank(str3)) {
                                u3 = null;
                            }
                            if (u3 != null) {
                                java.lang.String it4 = u3;
                                if (!kotlin.jvm.internal.Intrinsics.areEqual(it4, "#")) {
                                    videoUrls.add(it4);
                                }
                            }
                            $this$forEach$iv5 = $this$forEach$iv6;
                        }
                        java.lang.Iterable $this$forEach$iv7 = document.select("video source[src], source[src]");
                        for (java.lang.Object element$iv3 : $this$forEach$iv7) {
                            java.lang.Iterable $this$forEach$iv8 = $this$forEach$iv7;
                            java.lang.String u4 = ((org.jsoup.nodes.Element) element$iv3).attr("src");
                            java.lang.String str4 = u4;
                            if (str4 == null || kotlin.text.StringsKt.isBlank(str4)) {
                                u4 = null;
                            }
                            if (u4 != null) {
                                videoUrls.add(u4);
                            }
                            $this$forEach$iv7 = $this$forEach$iv8;
                        }
                        kotlin.text.Regex dataVideoRegex = new kotlin.text.Regex("data:video\\/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/=]+");
                        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function15 = function13;
                        for (java.lang.Object element$iv4 : kotlin.text.Regex.findAll$default(dataVideoRegex, pageText, 0, 2, (java.lang.Object) null)) {
                            kotlin.text.MatchResult match = (kotlin.text.MatchResult) element$iv4;
                            videoUrls.add(match.getValue());
                        }
                        for (java.lang.Object element$iv5 : document.select("video[src^=data:], source[src^=data:], div[src^=data:], iframe[src^=data:]")) {
                            java.lang.String u5 = ((org.jsoup.nodes.Element) element$iv5).attr("src");
                            java.lang.String str5 = u5;
                            if (str5 == null || kotlin.text.StringsKt.isBlank(str5)) {
                                u5 = null;
                            }
                            if (u5 != null) {
                                videoUrls.add(u5);
                            }
                        }
                        java.util.Set $this$map$iv = videoUrls;
                        java.util.Collection destination$iv$iv = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv, 10));
                        for (java.lang.Object item$iv$iv : $this$map$iv) {
                            destination$iv$iv.add(kotlin.text.StringsKt.trim((java.lang.String) item$iv$iv).toString());
                            dataVideoRegex = dataVideoRegex;
                        }
                        kotlin.text.Regex dataVideoRegex2 = dataVideoRegex;
                        java.lang.Iterable $this$filter$iv = (java.util.List) destination$iv$iv;
                        int $i$f$filter = 0;
                        java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                        java.lang.Iterable $this$filterTo$iv$iv = $this$filter$iv;
                        int $i$f$filterTo = 0;
                        for (java.lang.Object element$iv$iv : $this$filterTo$iv$iv) {
                            java.lang.Iterable $this$filter$iv2 = $this$filter$iv;
                            int $i$f$filter2 = $i$f$filter;
                            java.lang.String it5 = (java.lang.String) element$iv$iv;
                            java.lang.Iterable $this$filterTo$iv$iv2 = $this$filterTo$iv$iv;
                            int $i$f$filterTo2 = $i$f$filterTo;
                            if (!kotlin.text.StringsKt.startsWith(it5, "data:", true) || kotlin.text.StringsKt.startsWith(it5, "data:video/", true)) {
                                destination$iv$iv2.add(element$iv$iv);
                            }
                            $this$filter$iv = $this$filter$iv2;
                            $i$f$filter = $i$f$filter2;
                            $this$filterTo$iv$iv = $this$filterTo$iv$iv2;
                            $i$f$filterTo = $i$f$filterTo2;
                        }
                        java.util.List filteredUrls = kotlin.collections.CollectionsKt.toList((java.util.List) destination$iv$iv2);
                        java.lang.String data4 = data3;
                        com.Jayboys.Jayboys3.AnonymousClass10 anonymousClass10 = new com.Jayboys.Jayboys3.AnonymousClass10(data4, function15, found2, function14, null);
                        c001212.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data4);
                        c001212.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                        c001212.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                        c001212.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                        c001212.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        c001212.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pageText);
                        c001212.L$6 = found2;
                        c001212.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrls);
                        c001212.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeSrc);
                        c001212.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(dataVideoRegex2);
                        c001212.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(filteredUrls);
                        c001212.Z$0 = isCasting2;
                        c001212.label = 2;
                        if (com.lagradost.cloudstream3.ParCollectionsKt.amap(filteredUrls, anonymousClass10, c001212) == obj) {
                            return obj;
                        }
                        found = found2;
                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
                    }
                    java.lang.Object element$iv6 = it.next();
                    java.lang.String u6 = ((org.jsoup.nodes.Element) element$iv6).attr("data-src");
                    java.lang.String str6 = u6;
                    if (str6 == null || kotlin.text.StringsKt.isBlank(str6)) {
                        it2 = u6;
                    } else {
                        it2 = u6;
                        z2 = kotlin.jvm.internal.Intrinsics.areEqual(u6, "#") ? false : true;
                        if (!z2) {
                            it2 = null;
                        }
                        if (it2 == null) {
                            videoUrls.add(it2);
                        }
                        $this$forEach$iv = $this$forEach$iv2;
                    }
                    if (!z2) {
                    }
                    if (it2 == null) {
                    }
                    $this$forEach$iv = $this$forEach$iv2;
                }
                break;
            case 1:
                boolean isCasting3 = c00121.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = (kotlin.jvm.functions.Function1) c00121.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) c00121.L$1;
                java.lang.String data5 = (java.lang.String) c00121.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c001212 = c00121;
                obj = coroutine_suspended;
                data2 = data5;
                isCasting2 = isCasting3;
                function14 = function16;
                function13 = function17;
                obj2 = $result;
                com.lagradost.nicehttp.NiceResponse response2 = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Document document2 = response2.getDocument();
                java.lang.String pageText2 = response2.getText();
                kotlin.jvm.internal.Ref.BooleanRef found22 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.util.Set videoUrls2 = new java.util.LinkedHashSet();
                $this$forEach$iv = document2.select("div#player, div.video-player");
                it = $this$forEach$iv.iterator();
                while (true) {
                    java.lang.String u7 = "data-src";
                    java.lang.Iterable $this$forEach$iv22 = $this$forEach$iv;
                    if (it.hasNext()) {
                    }
                    $this$forEach$iv = $this$forEach$iv22;
                }
                break;
            case 2:
                boolean z3 = c00121.Z$0;
                found = (kotlin.jvm.internal.Ref.BooleanRef) c00121.L$6;
                kotlin.ResultKt.throwOnFailure($result);
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.Jayboys3$loadLinks$10, reason: invalid class name */
    /* JADX INFO: compiled from: Javboys3.kt */
    @kotlin.Metadata(d1 = {"\u0000\f\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\u0010\u0000\u001a\u00020\u00012\u0006\u0010\u0002\u001a\u00020\u0003H\n"}, d2 = {"<anonymous>", "", "url", ""}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.Jayboys3$loadLinks$10", f = "Javboys3.kt", i = {0}, l = {224}, m = "invokeSuspend", n = {"url"}, nl = {231}, s = {"L$0"}, v = 2)
    static final class AnonymousClass10 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<java.lang.String, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> $callback;
        final /* synthetic */ java.lang.String $data;
        final /* synthetic */ kotlin.jvm.internal.Ref.BooleanRef $found;
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> $subtitleCallback;
        /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass10(java.lang.String str, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.internal.Ref.BooleanRef booleanRef, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super com.Jayboys.Jayboys3.AnonymousClass10> continuation) {
            super(2, continuation);
            this.$data = str;
            this.$subtitleCallback = function1;
            this.$found = booleanRef;
            this.$callback = function12;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass10 = new com.Jayboys.Jayboys3.AnonymousClass10(this.$data, this.$subtitleCallback, this.$found, this.$callback, continuation);
            anonymousClass10.L$0 = obj;
            return anonymousClass10;
        }

        public final java.lang.Object invoke(java.lang.String str, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
            return create(str, continuation).invokeSuspend(kotlin.Unit.INSTANCE);
        }

        public final java.lang.Object invokeSuspend(java.lang.Object $result) {
            java.lang.Object objLoadExtractor;
            java.lang.String url = (java.lang.String) this.L$0;
            java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
            try {
                switch (this.label) {
                    case 0:
                        kotlin.ResultKt.throwOnFailure($result);
                        java.lang.String str = this.$data;
                        kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1 = this.$subtitleCallback;
                        final kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12 = this.$callback;
                        this.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                        this.label = 1;
                        objLoadExtractor = com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(url, str, function1, new kotlin.jvm.functions.Function1() { // from class: com.Jayboys.Jayboys3$loadLinks$10$$ExternalSyntheticLambda0
                            public final java.lang.Object invoke(java.lang.Object obj) {
                                return com.Jayboys.Jayboys3.AnonymousClass10.invokeSuspend$lambda$0(function12, (com.lagradost.cloudstream3.utils.ExtractorLink) obj);
                            }
                        }, (kotlin.coroutines.Continuation) this);
                        if (objLoadExtractor == coroutine_suspended) {
                            return coroutine_suspended;
                        }
                        break;
                    case 1:
                        kotlin.ResultKt.throwOnFailure($result);
                        objLoadExtractor = $result;
                        break;
                    default:
                        throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
                }
                boolean ok = ((java.lang.Boolean) objLoadExtractor).booleanValue();
                if (ok) {
                    this.$found.element = true;
                }
            } catch (java.lang.Exception e) {
            }
            return kotlin.Unit.INSTANCE;
        }

        static final kotlin.Unit invokeSuspend$lambda$0(kotlin.jvm.functions.Function1 $callback, com.lagradost.cloudstream3.utils.ExtractorLink link) {
            $callback.invoke(link);
            return kotlin.Unit.INSTANCE;
        }
    }
}
