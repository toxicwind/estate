package com.Gaycock4U;

/* JADX INFO: compiled from: Gaycock4U.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\u0086\u0001\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\n\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0010$\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010)\u001a\u00020+2\u0006\u0010,\u001a\u00020-2\u0006\u0010.\u001a\u00020/H\u0096@¢\u0006\u0002\u00100J\u000e\u00101\u001a\u0004\u0018\u000102*\u000203H\u0002J\u000e\u00104\u001a\u0004\u0018\u000102*\u000203H\u0002J\u001c\u00105\u001a\b\u0012\u0004\u0012\u0002020'2\u0006\u00106\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00107J\u0016\u00108\u001a\u0002092\u0006\u0010:\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00107JF\u0010;\u001a\u00020\u000e2\u0006\u0010<\u001a\u00020\u00052\u0006\u0010=\u001a\u00020\u000e2\u0012\u0010>\u001a\u000e\u0012\u0004\u0012\u00020@\u0012\u0004\u0012\u00020A0?2\u0012\u0010B\u001a\u000e\u0012\u0004\u0012\u00020C\u0012\u0004\u0012\u00020A0?H\u0096@¢\u0006\u0002\u0010DR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u0014\u0010\u0014\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0014\u0010\u0016\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0010R\u001a\u0010\u0018\u001a\b\u0012\u0004\u0012\u00020\u001a0\u0019X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001b\u0010\u001cR\u0014\u0010\u001d\u001a\u00020\u001eX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001f\u0010 R\u000e\u0010!\u001a\u00020\u0005X\u0082D¢\u0006\u0002\n\u0000R\u001a\u0010\"\u001a\u000e\u0012\u0004\u0012\u00020\u0005\u0012\u0004\u0012\u00020\u00050#X\u0082\u0004¢\u0006\u0002\n\u0000R\u000e\u0010$\u001a\u00020%X\u0082\u0004¢\u0006\u0002\n\u0000R\u001a\u0010&\u001a\b\u0012\u0004\u0012\u00020(0'X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b)\u0010*¨\u0006E"}, d2 = {"Lcom/Gaycock4U/Gaycock4U;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "hasDownloadSupport", "getHasDownloadSupport", "hasChromecastSupport", "getHasChromecastSupport", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "userAgent", "headers", "", "cfKiller", "Lcom/lagradost/cloudstream3/network/CloudflareKiller;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gaycock4U"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nGaycock4U.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Gaycock4U.kt\ncom/Gaycock4U/Gaycock4U\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,186:1\n1642#2,10:187\n1915#2:197\n1916#2:199\n1652#2:200\n1642#2,10:201\n1915#2:211\n1916#2:213\n1652#2:214\n1642#2,10:215\n1915#2:225\n1916#2:227\n1652#2:228\n1915#2:229\n1916#2:231\n1#3:198\n1#3:212\n1#3:226\n1#3:230\n*S KotlinDebug\n*F\n+ 1 Gaycock4U.kt\ncom/Gaycock4U/Gaycock4U\n*L\n77#1:187,10\n77#1:197\n77#1:199\n77#1:200\n122#1:201,10\n122#1:211\n122#1:213\n122#1:214\n144#1:215,10\n144#1:225\n144#1:227\n144#1:228\n173#1:229\n173#1:231\n77#1:198\n122#1:212\n144#1:226\n*E\n"})
public final class Gaycock4U extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://gaycock4u.com";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Gaycock4U";
    private final boolean hasMainPage = true;

    @org.jetbrains.annotations.NotNull
    private java.lang.String lang = "en";
    private final boolean hasDownloadSupport = true;
    private final boolean hasChromecastSupport = true;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

    @org.jetbrains.annotations.NotNull
    private final java.util.Map<java.lang.String, java.lang.String> headers = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", this.userAgent), kotlin.TuplesKt.to("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"), kotlin.TuplesKt.to("Referer", getMainUrl() + '/'), kotlin.TuplesKt.to("Connection", "keep-alive"), kotlin.TuplesKt.to("Accept-Language", "en-US,en;q=0.5"), kotlin.TuplesKt.to("Upgrade-Insecure-Requests", "1")});

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.network.CloudflareKiller cfKiller = new com.lagradost.cloudstream3.network.CloudflareKiller();

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("/#content", "Latest Updates"), kotlin.TuplesKt.to("/category/amateur/", "Amateur"), kotlin.TuplesKt.to("/category/bareback/", "Bareback"), kotlin.TuplesKt.to("/category/bigcock/", "Big Cock"), kotlin.TuplesKt.to("/category/group/", "Group"), kotlin.TuplesKt.to("/category/hardcore/", "Hardcore"), kotlin.TuplesKt.to("/category/latino/", "Latino"), kotlin.TuplesKt.to("/category/interracial/", "Interracial"), kotlin.TuplesKt.to("/category/twink/", "Twink"), kotlin.TuplesKt.to("/studio/asianetwork/", "Asianetwork"), kotlin.TuplesKt.to("/studio/bromo/", "Bromo"), kotlin.TuplesKt.to("/studio/chaosmen/", "Chaos Men"), kotlin.TuplesKt.to("/studio/euronetwork/", "Euro Network"), kotlin.TuplesKt.to("/studio/gayhoopla/", "Gay Hoopla"), kotlin.TuplesKt.to("/studio/latinleche/", "Latino Leche"), kotlin.TuplesKt.to("/studio/latinonetwork/", "Latino Network"), kotlin.TuplesKt.to("/studio/lucasentertainment/", "Lucas Entertainment"), kotlin.TuplesKt.to("/studio/onlyfans/", "Onlyfans"), kotlin.TuplesKt.to("/studio/rawfuckclub/", "Raw Fuck Club"), kotlin.TuplesKt.to("/studio/ragingstallion/", "Ragingstallion"), kotlin.TuplesKt.to("/studio/seancody/", "Sean Cody")});

    /* JADX INFO: renamed from: com.Gaycock4U.Gaycock4U$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: Gaycock4U.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Gaycock4U", f = "Gaycock4U.kt", i = {0, 0, 0, 1, 1, 1, 1}, l = {70, 72}, m = "getMainPage", n = {"request", "url", "page", "request", "url", "document", "page"}, nl = {71, 76}, s = {"L$0", "L$1", "I$0", "L$0", "L$1", "L$2", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gaycock4U.Gaycock4U.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaycock4U.Gaycock4U.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Gaycock4U.Gaycock4U$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Gaycock4U.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Gaycock4U", f = "Gaycock4U.kt", i = {0, 1, 1, 1, 1, 1, 1}, l = {138, 148}, m = "load", n = {"url", "url", "document", "title", "poster", "description", "recommendations"}, nl = {140, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.Gaycock4U.Gaycock4U.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaycock4U.Gaycock4U.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Gaycock4U.Gaycock4U$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Gaycock4U.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Gaycock4U", f = "Gaycock4U.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {161, 179}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "document", "found", "$this$forEach$iv", "element$iv", "f", "url", "isCasting", "$i$f$forEach", "$i$a$-forEach-Gaycock4U$loadLinks$2"}, nl = {162, 181}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$7", "L$8", "L$9", "Z$0", "I$0", "I$1"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        java.lang.Object L$0;
        java.lang.Object L$1;
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

        C00011(kotlin.coroutines.Continuation<? super com.Gaycock4U.Gaycock4U.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaycock4U.Gaycock4U.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Gaycock4U.Gaycock4U$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Gaycock4U.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Gaycock4U", f = "Gaycock4U.kt", i = {0, 0, 0}, l = {120}, m = "search", n = {"query", "searchResponse", "i"}, nl = {122}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super com.Gaycock4U.Gaycock4U.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaycock4U.Gaycock4U.this.search(null, (kotlin.coroutines.Continuation) this);
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

    /* JADX WARN: Removed duplicated region for block: B:24:0x0109  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0166  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x0190  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getMainPage(int page, @org.jetbrains.annotations.NotNull com.lagradost.cloudstream3.MainPageRequest request, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.HomePageResponse> continuation) {
        com.Gaycock4U.Gaycock4U.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        com.Gaycock4U.Gaycock4U.AnonymousClass1 anonymousClass12;
        java.lang.Object obj2;
        java.lang.String url;
        int page2;
        com.lagradost.cloudstream3.MainPageRequest request2;
        org.jsoup.nodes.Document document;
        com.lagradost.cloudstream3.MainPageRequest request3;
        java.lang.String url2;
        int page3;
        com.lagradost.cloudstream3.MainPageRequest request4;
        if (continuation instanceof com.Gaycock4U.Gaycock4U.AnonymousClass1) {
            anonymousClass1 = (com.Gaycock4U.Gaycock4U.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Gaycock4U.Gaycock4U.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String url3 = page > 1 ? getMainUrl() + request.getData() + "page/" + page : getMainUrl() + request.getData();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = url3;
                anonymousClass1.I$0 = page;
                anonymousClass1.label = 1;
                java.lang.String url4 = url3;
                com.Gaycock4U.Gaycock4U.AnonymousClass1 anonymousClass13 = anonymousClass1;
                obj = coroutine_suspended;
                java.lang.Object obj3 = com.lagradost.nicehttp.Requests.get$default(app, url4, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass13;
                if (obj3 == obj) {
                    return obj;
                }
                obj2 = obj3;
                url = url4;
                page2 = page;
                request2 = request;
                document = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                if (kotlin.jvm.internal.Intrinsics.areEqual(document.select("title").text(), "Just a moment...")) {
                    request3 = request2;
                    java.lang.Iterable $this$mapNotNull$iv = document.select("article.dce-post");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    while (r14.hasNext()) {
                    }
                    java.util.List list = (java.util.List) destination$iv$iv;
                    return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request3.getName(), list, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(true));
                }
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.util.Map<java.lang.String, java.lang.String> map = this.headers;
                okhttp3.Interceptor interceptor = this.cfKiller;
                anonymousClass12.L$0 = request2;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                anonymousClass12.I$0 = page2;
                anonymousClass12.label = 2;
                com.lagradost.cloudstream3.MainPageRequest request5 = request2;
                java.lang.String url5 = url;
                int page4 = page2;
                $result = com.lagradost.nicehttp.Requests.get$default(app2, url5, map, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, true, 0, (java.util.concurrent.TimeUnit) null, 120L, interceptor, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 3292, (java.lang.Object) null);
                if ($result == obj) {
                    return obj;
                }
                url2 = url5;
                page3 = page4;
                request4 = request5;
                document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                request3 = request4;
                java.lang.Iterable $this$mapNotNull$iv2 = document.select("article.dce-post");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv2) {
                    org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
                    if (searchResult != null) {
                        destination$iv$iv2.add(searchResult);
                    }
                }
                java.util.List list2 = (java.util.List) destination$iv$iv2;
                return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request3.getName(), list2, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(true));
            case 1:
                int page5 = anonymousClass1.I$0;
                java.lang.String url6 = (java.lang.String) anonymousClass1.L$1;
                com.lagradost.cloudstream3.MainPageRequest request6 = (com.lagradost.cloudstream3.MainPageRequest) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj2 = $result;
                page2 = page5;
                obj = coroutine_suspended;
                request2 = request6;
                url = url6;
                anonymousClass12 = anonymousClass1;
                document = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                if (kotlin.jvm.internal.Intrinsics.areEqual(document.select("title").text(), "Just a moment...")) {
                }
                break;
            case 2:
                page3 = anonymousClass1.I$0;
                url2 = (java.lang.String) anonymousClass1.L$1;
                request4 = (com.lagradost.cloudstream3.MainPageRequest) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                request3 = request4;
                java.lang.Iterable $this$mapNotNull$iv22 = document.select("article.dce-post");
                java.util.Collection destination$iv$iv22 = new java.util.ArrayList();
                while (r14.hasNext()) {
                }
                java.util.List list22 = (java.util.List) destination$iv$iv22;
                return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request3.getName(), list22, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(true));
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String string;
        java.lang.String href;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        java.lang.String strAttr3;
        java.lang.String string2;
        java.lang.String strAttr4;
        java.lang.String string3;
        java.lang.String strText;
        org.jsoup.nodes.Element titleElement = $this$toSearchResult.selectFirst("p.elementor-heading-title a, h1.elementor-heading-title a, h2.elementor-heading-title a");
        final java.lang.String posterUrl = "";
        if (titleElement == null || (strText = titleElement.text()) == null || (string = kotlin.text.StringsKt.trim(strText).toString()) == null) {
            string = "";
        }
        java.lang.String title = string;
        if (titleElement == null || (strAttr4 = titleElement.attr("href")) == null || (string3 = kotlin.text.StringsKt.trim(strAttr4).toString()) == null) {
            org.jsoup.nodes.Element elementSelectFirst = $this$toSearchResult.selectFirst("a[href]");
            href = (elementSelectFirst == null || (strAttr = elementSelectFirst.attr("href")) == null) ? "" : kotlin.text.StringsKt.trim(strAttr).toString();
        } else {
            href = string3;
        }
        org.jsoup.nodes.Element elementSelectFirst2 = $this$toSearchResult.selectFirst("img[src]");
        if (elementSelectFirst2 == null || (strAttr3 = elementSelectFirst2.attr("src")) == null || (string2 = kotlin.text.StringsKt.trim(strAttr3).toString()) == null) {
            org.jsoup.nodes.Element elementSelectFirst3 = $this$toSearchResult.selectFirst("img[data-src]");
            if (elementSelectFirst3 != null && (strAttr2 = elementSelectFirst3.attr("data-src")) != null) {
                posterUrl = kotlin.text.StringsKt.trim(strAttr2).toString();
            }
        } else {
            posterUrl = string2;
        }
        if (kotlin.text.StringsKt.isBlank(title) || kotlin.text.StringsKt.isBlank(href)) {
            return null;
        }
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.Gaycock4U.Gaycock4U$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.Gaycock4U.Gaycock4U.toSearchResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        return toSearchResult($this$toRecommendResult);
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
        com.Gaycock4U.Gaycock4U.C00021 c00021;
        com.Gaycock4U.Gaycock4U gaycock4U;
        java.util.List searchResponse;
        com.Gaycock4U.Gaycock4U.C00021 c000212;
        com.Gaycock4U.Gaycock4U gaycock4U2;
        java.lang.String query2;
        int i;
        java.util.List results;
        if (continuation instanceof com.Gaycock4U.Gaycock4U.C00021) {
            c00021 = (com.Gaycock4U.Gaycock4U.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
                gaycock4U = this;
            } else {
                gaycock4U = this;
                c00021 = gaycock4U.new C00021(continuation);
            }
        }
        java.lang.Object $result = c00021.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00021.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.List searchResponse2 = new java.util.ArrayList();
                searchResponse = searchResponse2;
                int i2 = 1;
                com.Gaycock4U.Gaycock4U gaycock4U3 = gaycock4U;
                com.Gaycock4U.Gaycock4U.C00021 c000213 = c00021;
                java.lang.String query3 = query;
                if (i2 >= 6) {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = gaycock4U3.getMainUrl() + "/page/" + i2 + "/?s=" + query3;
                    c000213.L$0 = query3;
                    c000213.L$1 = searchResponse;
                    c000213.I$0 = i2;
                    c000213.label = 1;
                    int i3 = i2;
                    java.util.List searchResponse3 = searchResponse;
                    c000212 = c000213;
                    java.lang.Object obj = coroutine_suspended;
                    java.lang.String query4 = query3;
                    $result = com.lagradost.nicehttp.Requests.get$default(app, str, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000212, 4094, (java.lang.Object) null);
                    if ($result == obj) {
                        return obj;
                    }
                    coroutine_suspended = obj;
                    gaycock4U2 = gaycock4U3;
                    searchResponse = searchResponse3;
                    query2 = query4;
                    i = i3;
                    org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.Iterable $this$mapNotNull$iv = document.select("div.elementor-widget-container article.elementor-post");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                        java.lang.String query5 = query2;
                        org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                        com.lagradost.cloudstream3.SearchResponse searchResult = gaycock4U2.toSearchResult(it);
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
                            gaycock4U3 = gaycock4U2;
                            c000213 = c000212;
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
                i = c00021.I$0;
                searchResponse = (java.util.List) c00021.L$1;
                java.lang.String query7 = (java.lang.String) c00021.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c000212 = c00021;
                query2 = query7;
                gaycock4U2 = gaycock4U;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("div.elementor-widget-container article.elementor-post");
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
        com.Gaycock4U.Gaycock4U.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        if (continuation instanceof com.Gaycock4U.Gaycock4U.C00001) {
            c00001 = (com.Gaycock4U.Gaycock4U.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.Gaycock4U.Gaycock4U.C00001(continuation);
            }
        }
        com.Gaycock4U.Gaycock4U.C00001 c000012 = c00001;
        java.lang.Object $result = c000012.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000012.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c000012.L$0 = url;
                c000012.label = 1;
                obj = coroutine_suspended;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000012, 4094, (java.lang.Object) null);
                c000012 = c000012;
                if (obj2 == obj) {
                    return obj;
                }
                url2 = url;
                break;
                break;
            case 1:
                java.lang.String url3 = (java.lang.String) c000012.L$0;
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
        com.Gaycock4U.Gaycock4U gaycock4U = this;
        org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("[property='og:image']");
        java.lang.String poster = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(gaycock4U, elementSelectFirst2 != null ? elementSelectFirst2.attr("content") : null);
        org.jsoup.nodes.Element elementSelectFirst3 = document.selectFirst("meta[property=og:description]");
        java.lang.String description = (elementSelectFirst3 == null || (strAttr = elementSelectFirst3.attr("content")) == null) ? null : kotlin.text.StringsKt.trim(strAttr).toString();
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.elementor-widget-container article.elementor-post");
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
        com.Gaycock4U.Gaycock4U.AnonymousClass2 anonymousClass2 = new com.Gaycock4U.Gaycock4U.AnonymousClass2(poster, description, recommendations, null);
        c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
        c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
        c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
        c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
        c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
        c000012.label = 2;
        java.lang.Object objNewMovieLoadResponse = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType, url2, anonymousClass2, c000012);
        return objNewMovieLoadResponse == obj ? obj : objNewMovieLoadResponse;
    }

    /* JADX INFO: renamed from: com.Gaycock4U.Gaycock4U$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: Gaycock4U.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaycock4U.Gaycock4U$load$2", f = "Gaycock4U.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list, kotlin.coroutines.Continuation<? super com.Gaycock4U.Gaycock4U.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$recommendations = list;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Gaycock4U.Gaycock4U.AnonymousClass2(this.$poster, this.$description, this.$recommendations, continuation);
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

    /* JADX WARN: Removed duplicated region for block: B:21:0x0105  */
    /* JADX WARN: Removed duplicated region for block: B:39:0x01bf  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:35:0x0196 -> B:36:0x01a9). Please report as a decompilation issue!!! */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:37:0x01b6 -> B:38:0x01ba). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.Gaycock4U.Gaycock4U.C00011 c00011;
        com.Gaycock4U.Gaycock4U gaycock4U;
        java.lang.Object $result;
        com.Gaycock4U.Gaycock4U.C00011 c000112;
        java.lang.Object obj;
        java.lang.String data2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        boolean isCasting2;
        int $i$f$forEach;
        org.jsoup.nodes.Document document;
        kotlin.jvm.internal.Ref.BooleanRef found;
        java.lang.Iterable element$iv;
        java.util.Iterator it;
        java.lang.Object obj3;
        boolean isCasting3;
        com.Gaycock4U.Gaycock4U.C00011 c000113;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation2;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        org.jsoup.nodes.Document document2;
        java.lang.Iterable $this$forEach$iv;
        java.lang.Object element$iv2;
        kotlin.jvm.internal.Ref.BooleanRef found2;
        java.util.Iterator it2;
        if (continuation instanceof com.Gaycock4U.Gaycock4U.C00011) {
            c00011 = (com.Gaycock4U.Gaycock4U.C00011) continuation;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
                gaycock4U = this;
            } else {
                gaycock4U = this;
                c00011 = gaycock4U.new C00011(continuation);
            }
        }
        java.lang.Object $result2 = c00011.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00011.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result2);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c00011.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data);
                c00011.L$1 = function1;
                c00011.L$2 = function12;
                c00011.Z$0 = isCasting;
                c00011.label = 1;
                $result = $result2;
                c000112 = c00011;
                obj = coroutine_suspended;
                java.lang.Object obj4 = com.lagradost.nicehttp.Requests.get$default(app, data, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000112, 4094, (java.lang.Object) null);
                if (obj4 == obj) {
                    return obj;
                }
                data2 = data;
                function13 = function1;
                function14 = function12;
                obj2 = obj4;
                isCasting2 = isCasting;
                org.jsoup.nodes.Document document3 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                kotlin.jvm.internal.Ref.BooleanRef found3 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.lang.Iterable $this$forEach$iv2 = document3.select("iframe[src], iframe[data-src]");
                $i$f$forEach = 0;
                document = document3;
                found = found3;
                element$iv = $this$forEach$iv2;
                it = $this$forEach$iv2.iterator();
                coroutine_suspended = obj;
                obj3 = gaycock4U;
                isCasting3 = isCasting2;
                c000113 = c000112;
                continuation2 = continuation;
                if (it.hasNext()) {
                    java.lang.Object element$iv3 = it.next();
                    org.jsoup.nodes.Element f = (org.jsoup.nodes.Element) element$iv3;
                    kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation4 = continuation2;
                    java.lang.String strAbsUrl = f.absUrl("src");
                    if (kotlin.text.StringsKt.isBlank(strAbsUrl)) {
                        strAbsUrl = f.attr("src");
                    }
                    java.lang.String strAbsUrl2 = strAbsUrl;
                    if (kotlin.text.StringsKt.isBlank(strAbsUrl2)) {
                        strAbsUrl2 = f.absUrl("data-src");
                    }
                    java.lang.String strAttr = strAbsUrl2;
                    if (kotlin.text.StringsKt.isBlank(strAttr)) {
                        strAttr = f.attr("data-src");
                    }
                    java.lang.String url = strAttr;
                    if (kotlin.text.StringsKt.isBlank(url)) {
                        continuation2 = continuation4;
                        if (it.hasNext()) {
                        }
                    } else {
                        found.element = true;
                        java.lang.String strLoadLinks$normalize = loadLinks$normalize(url);
                        c000113.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data2);
                        c000113.L$1 = function13;
                        c000113.L$2 = function14;
                        c000113.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        c000113.L$4 = found;
                        c000113.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv);
                        c000113.L$6 = it;
                        c000113.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv3);
                        c000113.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(f);
                        c000113.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                        c000113.Z$0 = isCasting3;
                        c000113.I$0 = $i$f$forEach;
                        c000113.I$1 = 0;
                        c000113.label = 2;
                        if (com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(strLoadLinks$normalize, function13, function14, c000113) == coroutine_suspended) {
                            return coroutine_suspended;
                        }
                        continuation3 = continuation4;
                        function15 = function14;
                        document2 = document;
                        c00011 = c000113;
                        $this$forEach$iv = element$iv;
                        $result2 = $result;
                        element$iv2 = obj3;
                        found2 = found;
                        it2 = it;
                        function14 = function15;
                        $result = $result2;
                        obj3 = element$iv2;
                        it = it2;
                        element$iv = $this$forEach$iv;
                        found = found2;
                        document = document2;
                        c000113 = c00011;
                        continuation2 = continuation3;
                        if (it.hasNext()) {
                            return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
                        }
                    }
                }
                break;
            case 1:
                boolean isCasting4 = c00011.Z$0;
                function14 = (kotlin.jvm.functions.Function1) c00011.L$2;
                function13 = (kotlin.jvm.functions.Function1) c00011.L$1;
                data2 = (java.lang.String) c00011.L$0;
                kotlin.ResultKt.throwOnFailure($result2);
                c000112 = c00011;
                $result = $result2;
                obj = coroutine_suspended;
                isCasting2 = isCasting4;
                obj2 = $result;
                org.jsoup.nodes.Document document32 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                kotlin.jvm.internal.Ref.BooleanRef found32 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.lang.Iterable $this$forEach$iv22 = document32.select("iframe[src], iframe[data-src]");
                $i$f$forEach = 0;
                document = document32;
                found = found32;
                element$iv = $this$forEach$iv22;
                it = $this$forEach$iv22.iterator();
                coroutine_suspended = obj;
                obj3 = gaycock4U;
                isCasting3 = isCasting2;
                c000113 = c000112;
                continuation2 = continuation;
                if (it.hasNext()) {
                }
                break;
            case 2:
                int i = c00011.I$1;
                int $i$f$forEach2 = c00011.I$0;
                isCasting3 = c00011.Z$0;
                java.lang.Object obj5 = c00011.L$7;
                java.util.Iterator it3 = (java.util.Iterator) c00011.L$6;
                java.lang.Iterable $this$forEach$iv3 = (java.lang.Iterable) c00011.L$5;
                kotlin.jvm.internal.Ref.BooleanRef found4 = (kotlin.jvm.internal.Ref.BooleanRef) c00011.L$4;
                org.jsoup.nodes.Document document4 = (org.jsoup.nodes.Document) c00011.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = (kotlin.jvm.functions.Function1) c00011.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) c00011.L$1;
                java.lang.String data3 = (java.lang.String) c00011.L$0;
                kotlin.ResultKt.throwOnFailure($result2);
                found2 = found4;
                document2 = document4;
                it2 = it3;
                $this$forEach$iv = $this$forEach$iv3;
                element$iv2 = gaycock4U;
                function15 = function16;
                $i$f$forEach = $i$f$forEach2;
                function13 = function17;
                data2 = data3;
                continuation3 = continuation;
                function14 = function15;
                $result = $result2;
                obj3 = element$iv2;
                it = it2;
                element$iv = $this$forEach$iv;
                found = found2;
                document = document2;
                c000113 = c00011;
                continuation2 = continuation3;
                if (it.hasNext()) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private static final java.lang.String loadLinks$normalize(java.lang.String u) {
        java.lang.String url = kotlin.text.StringsKt.trim(u).toString();
        return url.length() == 0 ? "" : kotlin.text.StringsKt.startsWith$default(url, "//", false, 2, (java.lang.Object) null) ? "https:" + url : url;
    }
}
