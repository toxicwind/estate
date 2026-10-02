package com.Nurgay;

/* JADX INFO: compiled from: Nurgay.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000z\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\f\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010&\u001a\u00020(2\u0006\u0010)\u001a\u00020*2\u0006\u0010+\u001a\u00020,H\u0096@¢\u0006\u0002\u0010-J\f\u0010.\u001a\u00020/*\u000200H\u0002J\u001c\u00101\u001a\b\u0012\u0004\u0012\u00020/0$2\u0006\u00102\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00103J\u0016\u00104\u001a\u0002052\u0006\u00106\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00103JF\u00107\u001a\u00020\u000e2\u0006\u00108\u001a\u00020\u00052\u0006\u00109\u001a\u00020\u000e2\u0012\u0010:\u001a\u000e\u0012\u0004\u0012\u00020<\u0012\u0004\u0012\u00020=0;2\u0012\u0010>\u001a\u000e\u0012\u0004\u0012\u00020?\u0012\u0004\u0012\u00020=0;H\u0096@¢\u0006\u0002\u0010@R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u0014\u0010\u0014\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0014\u0010\u0016\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0010R\u0014\u0010\u0018\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0010R\u001a\u0010\u001a\u001a\b\u0012\u0004\u0012\u00020\u001c0\u001bX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001d\u0010\u001eR\u0014\u0010\u001f\u001a\u00020 X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b!\u0010\"R\u001a\u0010#\u001a\b\u0012\u0004\u0012\u00020%0$X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b&\u0010'¨\u0006A"}, d2 = {"Lcom/Nurgay/Nurgay;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "hasQuickSearch", "getHasQuickSearch", "hasChromecastSupport", "getHasChromecastSupport", "hasDownloadSupport", "getHasDownloadSupport", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Nurgay"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nNurgay.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Nurgay.kt\ncom/Nurgay/Nurgay\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,174:1\n1642#2,10:175\n1915#2:185\n1916#2:187\n1652#2:188\n1642#2,10:190\n1915#2:200\n1916#2:202\n1652#2:203\n1642#2,10:204\n1915#2:214\n1916#2:217\n1652#2:218\n1#3:186\n1#3:189\n1#3:201\n1#3:215\n1#3:216\n*S KotlinDebug\n*F\n+ 1 Nurgay.kt\ncom/Nurgay/Nurgay\n*L\n50#1:175,10\n50#1:185\n50#1:187\n50#1:188\n79#1:190,10\n79#1:200\n79#1:202\n79#1:203\n134#1:204,10\n134#1:214\n134#1:217\n134#1:218\n50#1:186\n79#1:201\n134#1:216\n*E\n"})
public final class Nurgay extends com.lagradost.cloudstream3.MainAPI {
    private final boolean hasQuickSearch;

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://nurgay.to";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Nurgay";
    private final boolean hasMainPage = true;

    @org.jetbrains.annotations.NotNull
    private java.lang.String lang = "en";
    private final boolean hasChromecastSupport = true;
    private final boolean hasDownloadSupport = true;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(new com.lagradost.cloudstream3.TvType[]{com.lagradost.cloudstream3.TvType.NSFW, com.lagradost.cloudstream3.TvType.Movie});

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("/?filter=latest", "Latest"), kotlin.TuplesKt.to("/?filter=most-viewed", "Most Viewed"), kotlin.TuplesKt.to("/asiaten", "Asian"), kotlin.TuplesKt.to("/asiaten/?filter=random", "Asian random"), kotlin.TuplesKt.to("/gruppensex", "Group Sex"), kotlin.TuplesKt.to("/bisex", "Bisexual"), kotlin.TuplesKt.to("/hunks", "Hunks"), kotlin.TuplesKt.to("/hunks/?filter=random", "Hunk random"), kotlin.TuplesKt.to("/latino", "Latino"), kotlin.TuplesKt.to("/muskeln", "Muscle"), kotlin.TuplesKt.to("/bareback", "Bareback")});

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay", f = "Nurgay.kt", i = {0, 0, 0}, l = {49}, m = "getMainPage", n = {"request", "pageUrl", "page"}, nl = {50}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.Nurgay.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay", f = "Nurgay.kt", i = {0, 1, 1, 1, 1, 1}, l = {90, 96}, m = "load", n = {"url", "url", "document", "title", "poster", "description"}, nl = {92, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.Nurgay.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay", f = "Nurgay.kt", i = {0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {114, 129, 148}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "found", "isCasting", "data", "subtitleCallback", "callback", "found", "mainDoc", "embedUrl", "isCasting", "data", "subtitleCallback", "callback", "found", "mainDoc", "embedUrl", "embedDoc", "mirrors", "isCasting"}, nl = {119, 132, 170}, s = {"L$0", "L$1", "L$2", "L$3", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "Z$0"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        java.lang.Object L$7;
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00011(kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.Nurgay.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay", f = "Nurgay.kt", i = {0, 0, 0}, l = {78}, m = "search", n = {"query", "searchResponse", "i"}, nl = {79}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class C00031 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00031(kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.C00031> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.Nurgay.this.search(null, (kotlin.coroutines.Continuation) this);
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

    public boolean getHasQuickSearch() {
        return this.hasQuickSearch;
    }

    public boolean getHasChromecastSupport() {
        return this.hasChromecastSupport;
    }

    public boolean getHasDownloadSupport() {
        return this.hasDownloadSupport;
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

    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getMainPage(int page, @org.jetbrains.annotations.NotNull com.lagradost.cloudstream3.MainPageRequest request, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.HomePageResponse> continuation) {
        com.Nurgay.Nurgay.AnonymousClass1 anonymousClass1;
        boolean z;
        int page2;
        com.lagradost.cloudstream3.MainPageRequest request2;
        if (continuation instanceof com.Nurgay.Nurgay.AnonymousClass1) {
            anonymousClass1 = (com.Nurgay.Nurgay.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Nurgay.Nurgay.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String pageUrl = page == 1 ? getMainUrl() + request.getData() : getMainUrl() + "/page/" + page + request.getData();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pageUrl);
                anonymousClass1.I$0 = page;
                anonymousClass1.label = 1;
                z = true;
                $result = com.lagradost.nicehttp.Requests.get$default(app, pageUrl, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 4094, (java.lang.Object) null);
                if ($result == coroutine_suspended) {
                    return coroutine_suspended;
                }
                page2 = page;
                request2 = request;
                break;
                break;
            case 1:
                page2 = anonymousClass1.I$0;
                request2 = (com.lagradost.cloudstream3.MainPageRequest) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                z = true;
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
        java.lang.Iterable $this$mapNotNull$iv = document.select("article.loop-video");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            int page3 = page2;
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
            if (searchResult != null) {
                destination$iv$iv.add(searchResult);
            }
            page2 = page3;
        }
        java.util.List home = (java.util.List) destination$iv$iv;
        return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request2.getName(), home, false), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(z));
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String title = $this$toSearchResult.select("header.entry-header span").text();
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, $this$toSearchResult.select("a").attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toSearchResult.select("img").attr("data-src"));
        java.lang.String str = posterUrl;
        if (str == null || kotlin.text.StringsKt.isBlank(str)) {
            posterUrl = null;
        }
        if (posterUrl == null) {
            posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toSearchResult.select("img").attr("src"));
        }
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.Nurgay.Nurgay$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.Nurgay.Nurgay.toSearchResult$lambda$1(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$1(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:16:0x0064  */
    /* JADX WARN: Removed duplicated region for block: B:23:0x00f8  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0124  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x0134  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x013b  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:19:0x00cb -> B:20:0x00d4). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        com.Nurgay.Nurgay.C00031 c00031;
        com.Nurgay.Nurgay nurgay;
        java.util.List searchResponse;
        com.Nurgay.Nurgay.C00031 c000312;
        com.Nurgay.Nurgay nurgay2;
        java.lang.String query2;
        int i;
        java.util.List results;
        if (continuation instanceof com.Nurgay.Nurgay.C00031) {
            c00031 = (com.Nurgay.Nurgay.C00031) continuation;
            if ((c00031.label & Integer.MIN_VALUE) != 0) {
                c00031.label -= Integer.MIN_VALUE;
                nurgay = this;
            } else {
                nurgay = this;
                c00031 = nurgay.new C00031(continuation);
            }
        }
        java.lang.Object $result = c00031.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00031.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.List searchResponse2 = new java.util.ArrayList();
                searchResponse = searchResponse2;
                int i2 = 1;
                com.Nurgay.Nurgay nurgay3 = nurgay;
                com.Nurgay.Nurgay.C00031 c000313 = c00031;
                java.lang.String query3 = query;
                if (i2 >= 8) {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = nurgay3.getMainUrl() + "/?s=" + query3 + "&page=" + i2;
                    c000313.L$0 = query3;
                    c000313.L$1 = searchResponse;
                    c000313.I$0 = i2;
                    c000313.label = 1;
                    int i3 = i2;
                    java.util.List searchResponse3 = searchResponse;
                    c000312 = c000313;
                    java.lang.Object obj = coroutine_suspended;
                    java.lang.String query4 = query3;
                    $result = com.lagradost.nicehttp.Requests.get$default(app, str, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000312, 4094, (java.lang.Object) null);
                    if ($result == obj) {
                        return obj;
                    }
                    coroutine_suspended = obj;
                    nurgay2 = nurgay3;
                    searchResponse = searchResponse3;
                    query2 = query4;
                    i = i3;
                    org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.Iterable $this$mapNotNull$iv = document.select("article.loop-video");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                        java.lang.String query5 = query2;
                        org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                        com.lagradost.cloudstream3.SearchResponse searchResult = nurgay2.toSearchResult(it);
                        if (searchResult != null) {
                            destination$iv$iv.add(searchResult);
                        }
                        query2 = query5;
                    }
                    java.lang.String query6 = query2;
                    results = (java.util.List) destination$iv$iv;
                    if (!results.isEmpty()) {
                        return searchResponse;
                    }
                    searchResponse.addAll(results);
                    i2 = i + 1;
                    nurgay3 = nurgay2;
                    c000313 = c000312;
                    query3 = query6;
                    if (i2 >= 8) {
                        return searchResponse;
                    }
                }
                break;
            case 1:
                i = c00031.I$0;
                searchResponse = (java.util.List) c00031.L$1;
                java.lang.String query7 = (java.lang.String) c00031.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c000312 = c00031;
                query2 = query7;
                nurgay2 = nurgay;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("article.loop-video");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                while (r15.hasNext()) {
                }
                java.lang.String query62 = query2;
                results = (java.util.List) destination$iv$iv2;
                if (!results.isEmpty()) {
                }
                break;
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
        com.Nurgay.Nurgay.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String title;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        java.lang.String strAttr3;
        if (continuation instanceof com.Nurgay.Nurgay.C00001) {
            c00001 = (com.Nurgay.Nurgay.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.Nurgay.Nurgay.C00001(continuation);
            }
        }
        com.Nurgay.Nurgay.C00001 c000012 = c00001;
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
        if (elementSelectFirst == null || (strAttr3 = elementSelectFirst.attr("content")) == null || (title = kotlin.text.StringsKt.trim(strAttr3).toString()) == null) {
            title = "";
        }
        org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("meta[property=og:image]");
        java.lang.String poster = (elementSelectFirst2 == null || (strAttr2 = elementSelectFirst2.attr("content")) == null) ? null : kotlin.text.StringsKt.trim(strAttr2).toString();
        org.jsoup.nodes.Element elementSelectFirst3 = document.selectFirst("meta[property=og:description]");
        java.lang.String description = (elementSelectFirst3 == null || (strAttr = elementSelectFirst3.attr("content")) == null) ? null : kotlin.text.StringsKt.trim(strAttr).toString();
        java.lang.String title2 = title;
        com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.Movie;
        com.Nurgay.Nurgay.AnonymousClass2 anonymousClass2 = new com.Nurgay.Nurgay.AnonymousClass2(poster, description, null);
        c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
        c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title2);
        c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
        c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
        c000012.label = 2;
        java.lang.Object objNewMovieLoadResponse = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title2, url2, tvType, url2, anonymousClass2, c000012);
        if (objNewMovieLoadResponse == obj) {
            return obj;
        }
        return objNewMovieLoadResponse;
    }

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay$load$2", f = "Nurgay.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Nurgay.Nurgay.AnonymousClass2(this.$poster, this.$description, continuation);
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
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:21:0x014c  */
    /* JADX WARN: Removed duplicated region for block: B:22:0x0153  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x017d  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x0180  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x018c  */
    /* JADX WARN: Removed duplicated region for block: B:40:0x0217  */
    /* JADX WARN: Removed duplicated region for block: B:49:0x0257  */
    /* JADX WARN: Removed duplicated region for block: B:51:0x025b  */
    /* JADX WARN: Removed duplicated region for block: B:55:0x02ac  */
    /* JADX WARN: Removed duplicated region for block: B:57:0x02b8  */
    /* JADX WARN: Removed duplicated region for block: B:65:0x0261 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.Nurgay.Nurgay.C00011 c00011;
        java.lang.String str;
        java.lang.Object obj;
        java.lang.String str2;
        java.lang.String data2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        kotlin.jvm.internal.Ref.BooleanRef found;
        boolean isCasting2;
        java.lang.String str3;
        java.lang.String str4;
        java.lang.Object obj3;
        java.lang.String embedUrl;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        kotlin.jvm.internal.Ref.BooleanRef found2;
        org.jsoup.nodes.Document mainDoc;
        boolean isCasting3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function16;
        java.util.Set mirrors;
        java.lang.String str5;
        boolean z;
        if (continuation instanceof com.Nurgay.Nurgay.C00011) {
            c00011 = (com.Nurgay.Nurgay.C00011) continuation;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
            } else {
                c00011 = new com.Nurgay.Nurgay.C00011(continuation);
            }
        }
        com.Nurgay.Nurgay.C00011 c000112 = c00011;
        java.lang.Object $result = c000112.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000112.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.api.Log.INSTANCE.d("Nurgay", "=== LOAD LINKS for: " + data + " ===");
                kotlin.jvm.internal.Ref.BooleanRef found3 = new kotlin.jvm.internal.Ref.BooleanRef();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c000112.L$0 = data;
                c000112.L$1 = function1;
                c000112.L$2 = function12;
                c000112.L$3 = found3;
                c000112.Z$0 = isCasting;
                c000112.label = 1;
                str = "Nurgay";
                obj = coroutine_suspended;
                str2 = " ===";
                java.lang.Object obj4 = com.lagradost.nicehttp.Requests.get$default(app, data, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000112, 4094, (java.lang.Object) null);
                if (obj4 == obj) {
                    return obj;
                }
                data2 = data;
                function13 = function1;
                function14 = function12;
                obj2 = obj4;
                found = found3;
                isCasting2 = isCasting;
                org.jsoup.nodes.Document mainDoc2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementSelectFirst = mainDoc2.selectFirst("meta[itemprop=embedUrl]");
                java.lang.String embedUrl2 = elementSelectFirst == null ? elementSelectFirst.attr("content") : null;
                java.lang.String str6 = str;
                com.lagradost.api.Log.INSTANCE.d(str6, "Embed URL: " + embedUrl2);
                str3 = embedUrl2;
                if (!(str3 != null || kotlin.text.StringsKt.isBlank(str3))) {
                    com.lagradost.api.Log.INSTANCE.d(str6, "No embedUrl found");
                    return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                }
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data2);
                c000112.L$1 = function13;
                c000112.L$2 = function14;
                c000112.L$3 = found;
                c000112.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mainDoc2);
                c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedUrl2);
                c000112.Z$0 = isCasting2;
                c000112.label = 2;
                kotlin.jvm.internal.Ref.BooleanRef found4 = found;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17 = function14;
                java.lang.String embedUrl3 = embedUrl2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18 = function13;
                boolean isCasting4 = isCasting2;
                str4 = str6;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app2, embedUrl3, (java.util.Map) null, data2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000112, 4090, (java.lang.Object) null);
                c000112 = c000112;
                if (obj3 == obj) {
                    return obj;
                }
                embedUrl = embedUrl3;
                function15 = function17;
                found2 = found4;
                mainDoc = mainDoc2;
                isCasting3 = isCasting4;
                function16 = function18;
                org.jsoup.nodes.Document embedDoc = ((com.lagradost.nicehttp.NiceResponse) obj3).getDocument();
                java.lang.Iterable $this$mapNotNull$iv = embedDoc.select("ul#mirrorMenu a.mirror-opt");
                int $i$f$mapNotNull = 0;
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                    java.lang.Iterable $this$mapNotNull$iv2 = $this$mapNotNull$iv;
                    org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    int $i$f$mapNotNull2 = $i$f$mapNotNull;
                    java.lang.String url = it.attr("data-url");
                    if (kotlin.text.StringsKt.isBlank(url)) {
                        str5 = url;
                    } else {
                        str5 = url;
                        z = kotlin.jvm.internal.Intrinsics.areEqual(url, "#") ? false : true;
                        if (!z) {
                            str5 = null;
                        }
                        if (str5 == null) {
                            destination$iv$iv.add(str5);
                        }
                        $this$mapNotNull$iv = $this$mapNotNull$iv2;
                        $i$f$mapNotNull = $i$f$mapNotNull2;
                    }
                    if (!z) {
                    }
                    if (str5 == null) {
                    }
                    $this$mapNotNull$iv = $this$mapNotNull$iv2;
                    $i$f$mapNotNull = $i$f$mapNotNull2;
                }
                mirrors = kotlin.collections.CollectionsKt.toMutableSet((java.util.List) destination$iv$iv);
                com.lagradost.api.Log.INSTANCE.d(str4, "Mirrors found: " + kotlin.collections.CollectionsKt.joinToString$default(mirrors, (java.lang.CharSequence) null, (java.lang.CharSequence) null, (java.lang.CharSequence) null, 0, (java.lang.CharSequence) null, (kotlin.jvm.functions.Function1) null, 63, (java.lang.Object) null));
                if (!mirrors.isEmpty()) {
                    com.lagradost.api.Log.INSTANCE.d(str4, "No mirrors found in embed page");
                    return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                }
                java.util.List list = kotlin.collections.CollectionsKt.toList(mirrors);
                com.Nurgay.Nurgay.C00022 c00022 = new com.Nurgay.Nurgay.C00022(function16, found2, function15, null);
                c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data2);
                c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function16);
                c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                c000112.L$3 = found2;
                c000112.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mainDoc);
                c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedUrl);
                c000112.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedDoc);
                c000112.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mirrors);
                c000112.Z$0 = isCasting3;
                c000112.label = 3;
                if (com.lagradost.cloudstream3.ParCollectionsKt.amap(list, c00022, c000112) == obj) {
                    return obj;
                }
                com.lagradost.api.Log.INSTANCE.d(str4, "=== finished loadLinks; found=" + found2.element + str2);
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found2.element);
            case 1:
                boolean isCasting5 = c000112.Z$0;
                kotlin.jvm.internal.Ref.BooleanRef found5 = (kotlin.jvm.internal.Ref.BooleanRef) c000112.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19 = (kotlin.jvm.functions.Function1) c000112.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function110 = (kotlin.jvm.functions.Function1) c000112.L$1;
                java.lang.String data3 = (java.lang.String) c000112.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                str2 = " ===";
                found = found5;
                str = "Nurgay";
                function14 = function19;
                obj2 = $result;
                isCasting2 = isCasting5;
                data2 = data3;
                function13 = function110;
                org.jsoup.nodes.Document mainDoc22 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementSelectFirst2 = mainDoc22.selectFirst("meta[itemprop=embedUrl]");
                if (elementSelectFirst2 == null) {
                }
                java.lang.String str62 = str;
                com.lagradost.api.Log.INSTANCE.d(str62, "Embed URL: " + embedUrl2);
                str3 = embedUrl2;
                if (str3 != null) {
                    if (!(str3 != null || kotlin.text.StringsKt.isBlank(str3))) {
                    }
                }
                com.lagradost.api.Log.INSTANCE.d(str4, "=== finished loadLinks; found=" + found2.element + str2);
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found2.element);
            case 2:
                boolean isCasting6 = c000112.Z$0;
                java.lang.String embedUrl4 = (java.lang.String) c000112.L$5;
                org.jsoup.nodes.Document mainDoc3 = (org.jsoup.nodes.Document) c000112.L$4;
                kotlin.jvm.internal.Ref.BooleanRef found6 = (kotlin.jvm.internal.Ref.BooleanRef) c000112.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) c000112.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) c000112.L$1;
                java.lang.String data4 = (java.lang.String) c000112.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                isCasting3 = isCasting6;
                str2 = " ===";
                embedUrl = embedUrl4;
                mainDoc = mainDoc3;
                found2 = found6;
                function15 = function111;
                function16 = function112;
                data2 = data4;
                str4 = "Nurgay";
                obj3 = $result;
                org.jsoup.nodes.Document embedDoc2 = ((com.lagradost.nicehttp.NiceResponse) obj3).getDocument();
                java.lang.Iterable $this$mapNotNull$iv3 = embedDoc2.select("ul#mirrorMenu a.mirror-opt");
                int $i$f$mapNotNull3 = 0;
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                while (r18.hasNext()) {
                }
                mirrors = kotlin.collections.CollectionsKt.toMutableSet((java.util.List) destination$iv$iv2);
                com.lagradost.api.Log.INSTANCE.d(str4, "Mirrors found: " + kotlin.collections.CollectionsKt.joinToString$default(mirrors, (java.lang.CharSequence) null, (java.lang.CharSequence) null, (java.lang.CharSequence) null, 0, (java.lang.CharSequence) null, (kotlin.jvm.functions.Function1) null, 63, (java.lang.Object) null));
                if (!mirrors.isEmpty()) {
                }
                break;
            case 3:
                boolean z2 = c000112.Z$0;
                found2 = (kotlin.jvm.internal.Ref.BooleanRef) c000112.L$3;
                kotlin.ResultKt.throwOnFailure($result);
                str2 = " ===";
                str4 = "Nurgay";
                com.lagradost.api.Log.INSTANCE.d(str4, "=== finished loadLinks; found=" + found2.element + str2);
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found2.element);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Nurgay.Nurgay$loadLinks$2, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Nurgay.kt */
    @kotlin.Metadata(d1 = {"\u0000\f\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\u0010\u0000\u001a\u00020\u00012\u0006\u0010\u0002\u001a\u00020\u0003H\n"}, d2 = {"<anonymous>", "", "url", ""}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.Nurgay$loadLinks$2", f = "Nurgay.kt", i = {0}, l = {152}, m = "invokeSuspend", n = {"url"}, nl = {161}, s = {"L$0"}, v = 2)
    static final class C00022 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<java.lang.String, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> $callback;
        final /* synthetic */ kotlin.jvm.internal.Ref.BooleanRef $found;
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> $subtitleCallback;
        /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        C00022(kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.internal.Ref.BooleanRef booleanRef, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super com.Nurgay.Nurgay.C00022> continuation) {
            super(2, continuation);
            this.$subtitleCallback = function1;
            this.$found = booleanRef;
            this.$callback = function12;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> c00022 = new com.Nurgay.Nurgay.C00022(this.$subtitleCallback, this.$found, this.$callback, continuation);
            c00022.L$0 = obj;
            return c00022;
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
                        com.lagradost.api.Log.INSTANCE.d("Nurgay", "Trying extractor for: " + url);
                        kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1 = this.$subtitleCallback;
                        final kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12 = this.$callback;
                        this.L$0 = url;
                        this.label = 1;
                        objLoadExtractor = com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(url, url, function1, new kotlin.jvm.functions.Function1() { // from class: com.Nurgay.Nurgay$loadLinks$2$$ExternalSyntheticLambda0
                            public final java.lang.Object invoke(java.lang.Object obj) {
                                return com.Nurgay.Nurgay.C00022.invokeSuspend$lambda$0(function12, (com.lagradost.cloudstream3.utils.ExtractorLink) obj);
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
                com.lagradost.api.Log.INSTANCE.d("Nurgay", "loadExtractor returned " + (ok) + " for " + url);
                if (ok) {
                    this.$found.element = true;
                }
            } catch (java.lang.Exception e) {
                com.lagradost.api.Log.INSTANCE.e("Nurgay", "Extractor failed for " + url + " -> " + e.getLocalizedMessage());
            }
            return kotlin.Unit.INSTANCE;
        }

        static final kotlin.Unit invokeSuspend$lambda$0(kotlin.jvm.functions.Function1 $callback, com.lagradost.cloudstream3.utils.ExtractorLink link) {
            com.lagradost.api.Log.INSTANCE.d("Nurgay", "EXTRACTOR CALLBACK -> " + link.getUrl());
            $callback.invoke(link);
            return kotlin.Unit.INSTANCE;
        }
    }
}
