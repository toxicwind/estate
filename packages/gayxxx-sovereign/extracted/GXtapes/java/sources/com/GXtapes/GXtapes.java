package com.GXtapes;

/* JADX INFO: compiled from: GXtapes.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000z\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\f\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010&\u001a\u00020(2\u0006\u0010)\u001a\u00020*2\u0006\u0010+\u001a\u00020,H\u0096@¢\u0006\u0002\u0010-J\f\u0010.\u001a\u00020/*\u000200H\u0002J\f\u00101\u001a\u00020/*\u000200H\u0002J\u001c\u00102\u001a\b\u0012\u0004\u0012\u00020/0$2\u0006\u00103\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00104J\u0016\u00105\u001a\u0002062\u0006\u00107\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00104JF\u00108\u001a\u00020\u000e2\u0006\u00109\u001a\u00020\u00052\u0006\u0010:\u001a\u00020\u000e2\u0012\u0010;\u001a\u000e\u0012\u0004\u0012\u00020=\u0012\u0004\u0012\u00020>0<2\u0012\u0010?\u001a\u000e\u0012\u0004\u0012\u00020@\u0012\u0004\u0012\u00020>0<H\u0096@¢\u0006\u0002\u0010AR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u0014\u0010\u0014\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0014\u0010\u0016\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0010R\u0014\u0010\u0018\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0010R\u001a\u0010\u001a\u001a\b\u0012\u0004\u0012\u00020\u001c0\u001bX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001d\u0010\u001eR\u0014\u0010\u001f\u001a\u00020 X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b!\u0010\"R\u001a\u0010#\u001a\b\u0012\u0004\u0012\u00020%0$X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b&\u0010'¨\u0006B"}, d2 = {"Lcom/GXtapes/GXtapes;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "hasQuickSearch", "getHasQuickSearch", "hasChromecastSupport", "getHasChromecastSupport", "hasDownloadSupport", "getHasDownloadSupport", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GXtapes"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nGXtapes.kt\nKotlin\n*S Kotlin\n*F\n+ 1 GXtapes.kt\ncom/GXtapes/GXtapes\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,169:1\n1642#2,10:170\n1915#2:180\n1916#2:182\n1652#2:183\n1642#2,10:184\n1915#2:194\n1916#2:196\n1652#2:197\n1642#2,10:198\n1915#2:208\n1916#2:210\n1652#2:211\n1642#2,10:212\n1915#2:222\n1916#2:225\n1652#2:226\n1#3:181\n1#3:195\n1#3:209\n1#3:223\n1#3:224\n*S KotlinDebug\n*F\n+ 1 GXtapes.kt\ncom/GXtapes/GXtapes\n*L\n65#1:170,10\n65#1:180\n65#1:182\n65#1:183\n104#1:184,10\n104#1:194\n104#1:196\n104#1:197\n126#1:198,10\n126#1:208\n126#1:210\n126#1:211\n148#1:212,10\n148#1:222\n148#1:225\n148#1:226\n65#1:181\n104#1:195\n126#1:209\n148#1:224\n*E\n"})
public final class GXtapes extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://gay.xtapes.tw";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "G_Xtapes";
    private final boolean hasMainPage = true;

    @org.jetbrains.annotations.NotNull
    private java.lang.String lang = "en";
    private final boolean hasQuickSearch = true;
    private final boolean hasChromecastSupport = true;
    private final boolean hasDownloadSupport = true;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("/?filtre=date&cat=0", "Latest"), kotlin.TuplesKt.to("/category/porn-movies-214660", "Full Movies"), kotlin.TuplesKt.to("/category/groupsex-gangbang-porn-129457", "Gang bang & Group"), kotlin.TuplesKt.to("/category/243741", "Active Duty"), kotlin.TuplesKt.to("/category/685019", "Bel Ami"), kotlin.TuplesKt.to("/category/651385", "Bi Latin Men"), kotlin.TuplesKt.to("/category/629527", "Broke Straight Boys"), kotlin.TuplesKt.to("/category/854356", "BroMo"), kotlin.TuplesKt.to("/category/745361", "Chaos Men"), kotlin.TuplesKt.to("/category/267515", "CockyBoys"), kotlin.TuplesKt.to("/category/861573", "Corbin Fisher"), kotlin.TuplesKt.to("/category/518197", "Disruptive Films"), kotlin.TuplesKt.to("/category/624384", "Fraternity X"), kotlin.TuplesKt.to("/category/418613", "Falcon Studio"), kotlin.TuplesKt.to("/category/37433", "Gay Hoopla"), kotlin.TuplesKt.to("/category/37840", "Gay Room"), kotlin.TuplesKt.to("/category/4793", "Gay Wire"), kotlin.TuplesKt.to("/category/452643", "GuysInSweatpants"), kotlin.TuplesKt.to("/category/298563", "Helix Studios"), kotlin.TuplesKt.to("/category/345682", "Onlyfans"), kotlin.TuplesKt.to("/category/256935", "Latin"), kotlin.TuplesKt.to("/category/432724", "Kristen Bjorn"), kotlin.TuplesKt.to("/category/571476", "[L]ucas[E]ntertain[m]ent"), kotlin.TuplesKt.to("/category/352421", "MEN"), kotlin.TuplesKt.to("/category/792756", "Next Door Studios"), kotlin.TuplesKt.to("/category/porn-parody", "Parody"), kotlin.TuplesKt.to("/category/84750", "PeterFever"), kotlin.TuplesKt.to("/category/461264", "Raging Stallion"), kotlin.TuplesKt.to("/category/349693", "Sean Cody"), kotlin.TuplesKt.to("/category/182658", "Timtales"), kotlin.TuplesKt.to("/category/36567", "William Higgins")});

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes", f = "GXtapes.kt", i = {0, 0, 0}, l = {64}, m = "getMainPage", n = {"request", "url", "page"}, nl = {65}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes", f = "GXtapes.kt", i = {0, 1, 1, 1, 1, 1, 1}, l = {120, 130}, m = "load", n = {"url", "url", "document", "title", "poster", "description", "recommendations"}, nl = {122, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes", f = "GXtapes.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1}, l = {143, 158}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "document", "found", "videoUrls", "isCasting"}, nl = {144, 167}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "Z$0"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00011(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes", f = "GXtapes.kt", i = {0, 0, 0}, l = {102}, m = "search", n = {"query", "searchResponse", "i"}, nl = {104}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GXtapes.GXtapes.this.search(null, (kotlin.coroutines.Continuation) this);
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
        com.GXtapes.GXtapes.AnonymousClass1 anonymousClass1;
        com.lagradost.cloudstream3.MainPageRequest request2;
        if (continuation instanceof com.GXtapes.GXtapes.AnonymousClass1) {
            anonymousClass1 = (com.GXtapes.GXtapes.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.GXtapes.GXtapes.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String url = page > 1 ? getMainUrl() + request.getData() + "/page/" + page : getMainUrl() + '/' + request.getData();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.I$0 = page;
                anonymousClass1.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 4094, (java.lang.Object) null);
                if ($result == coroutine_suspended) {
                    return coroutine_suspended;
                }
                request2 = request;
                break;
                break;
            case 1:
                int i = anonymousClass1.I$0;
                request2 = (com.lagradost.cloudstream3.MainPageRequest) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
        java.lang.Iterable $this$mapNotNull$iv = document.select("ul.listing-tube li");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
            if (searchResult != null) {
                destination$iv$iv.add(searchResult);
            }
        }
        java.util.List home = (java.util.List) destination$iv$iv;
        return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request2.getName(), home, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(true));
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String title = $this$toSearchResult.select("img").attr("title");
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, $this$toSearchResult.select("a").attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toSearchResult.select("img").attr("src"));
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.GXtapes.GXtapes$$ExternalSyntheticLambda1
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.GXtapes.GXtapes.toSearchResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        java.lang.String title = $this$toRecommendResult.select("img").attr("title");
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, $this$toRecommendResult.select("a").attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toRecommendResult.select("img").attr("src"));
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.GXtapes.GXtapes$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.GXtapes.GXtapes.toRecommendResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
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
        com.GXtapes.GXtapes.C00021 c00021;
        com.GXtapes.GXtapes gXtapes;
        java.util.List searchResponse;
        com.GXtapes.GXtapes.C00021 c000212;
        com.GXtapes.GXtapes gXtapes2;
        java.lang.String query2;
        int i;
        java.util.List results;
        if (continuation instanceof com.GXtapes.GXtapes.C00021) {
            c00021 = (com.GXtapes.GXtapes.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
                gXtapes = this;
            } else {
                gXtapes = this;
                c00021 = gXtapes.new C00021(continuation);
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
                com.GXtapes.GXtapes gXtapes3 = gXtapes;
                com.GXtapes.GXtapes.C00021 c000213 = c00021;
                java.lang.String query3 = query;
                if (i2 >= 6) {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = gXtapes3.getMainUrl() + "/page/" + i2 + "/?s=" + query3;
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
                    gXtapes2 = gXtapes3;
                    searchResponse = searchResponse3;
                    query2 = query4;
                    i = i3;
                    org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.Iterable $this$mapNotNull$iv = document.select("ul.listing-tube li");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                        java.lang.String query5 = query2;
                        org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                        com.lagradost.cloudstream3.SearchResponse searchResult = gXtapes2.toSearchResult(it);
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
                            gXtapes3 = gXtapes2;
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
                gXtapes2 = gXtapes;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("ul.listing-tube li");
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
        com.GXtapes.GXtapes.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String title;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        java.lang.String strAttr3;
        if (continuation instanceof com.GXtapes.GXtapes.C00001) {
            c00001 = (com.GXtapes.GXtapes.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.GXtapes.GXtapes.C00001(continuation);
            }
        }
        com.GXtapes.GXtapes.C00001 c000012 = c00001;
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
        java.lang.Iterable $this$mapNotNull$iv = document.select("ul.listing-tube li");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse recommendResult = toRecommendResult(it);
            if (recommendResult != null) {
                destination$iv$iv.add(recommendResult);
            }
        }
        java.util.List recommendations = (java.util.List) destination$iv$iv;
        java.lang.String title2 = title;
        com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.NSFW;
        com.GXtapes.GXtapes.AnonymousClass2 anonymousClass2 = new com.GXtapes.GXtapes.AnonymousClass2(poster, description, recommendations, null);
        c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
        c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title2);
        c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
        c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
        c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
        c000012.label = 2;
        java.lang.Object objNewMovieLoadResponse = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title2, url2, tvType, url2, anonymousClass2, c000012);
        return objNewMovieLoadResponse == obj ? obj : objNewMovieLoadResponse;
    }

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes$load$2", f = "GXtapes.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list, kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$recommendations = list;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.GXtapes.GXtapes.AnonymousClass2(this.$poster, this.$description, this.$recommendations, continuation);
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

    /* JADX WARN: Removed duplicated region for block: B:21:0x00f4  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x012d  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x0131  */
    /* JADX WARN: Removed duplicated region for block: B:46:0x013c A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:48:0x0137 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.GXtapes.GXtapes.C00011 c00011;
        java.lang.Object obj;
        com.GXtapes.GXtapes.C00011 c000112;
        java.lang.String data2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        boolean isCasting2;
        java.util.Iterator it;
        kotlin.jvm.internal.Ref.BooleanRef found;
        java.lang.String iframeSrc;
        java.lang.String str;
        if (continuation instanceof com.GXtapes.GXtapes.C00011) {
            c00011 = (com.GXtapes.GXtapes.C00011) continuation;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
            } else {
                c00011 = new com.GXtapes.GXtapes.C00011(continuation);
            }
        }
        java.lang.Object $result = c00011.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00011.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c00011.L$0 = data;
                c00011.L$1 = function1;
                c00011.L$2 = function12;
                c00011.Z$0 = isCasting;
                c00011.label = 1;
                com.GXtapes.GXtapes.C00011 c000113 = c00011;
                obj = coroutine_suspended;
                java.lang.Object obj3 = com.lagradost.nicehttp.Requests.get$default(app, data, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000113, 4094, (java.lang.Object) null);
                c000112 = c000113;
                if (obj3 == obj) {
                    return obj;
                }
                data2 = data;
                function13 = function1;
                function14 = function12;
                obj2 = obj3;
                isCasting2 = isCasting;
                org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                kotlin.jvm.internal.Ref.BooleanRef found2 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.lang.Iterable $this$mapNotNull$iv = document.select("#video-code iframe, iframe[src]");
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                it = $this$mapNotNull$iv.iterator();
                while (true) {
                    if (it.hasNext()) {
                        java.util.Set videoUrls = kotlin.collections.CollectionsKt.toMutableSet((java.util.List) destination$iv$iv);
                        if (videoUrls.isEmpty()) {
                            org.jsoup.nodes.Element elementSelectFirst = document.selectFirst("iframe#ifr");
                            iframeSrc = elementSelectFirst != null ? elementSelectFirst.attr("src") : null;
                            if (iframeSrc != null) {
                                java.lang.String it2 = iframeSrc;
                                kotlin.coroutines.jvm.internal.Boxing.boxBoolean(videoUrls.add(it2));
                            }
                        }
                        java.util.List list = kotlin.collections.CollectionsKt.toList(videoUrls);
                        com.GXtapes.GXtapes.AnonymousClass3 anonymousClass3 = new com.GXtapes.GXtapes.AnonymousClass3(data2, function13, found2, function14, null);
                        c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data2);
                        c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                        c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                        c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        c000112.L$4 = found2;
                        c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrls);
                        c000112.Z$0 = isCasting2;
                        c000112.label = 2;
                        if (com.lagradost.cloudstream3.ParCollectionsKt.amap(list, anonymousClass3, c000112) == obj) {
                            return obj;
                        }
                        found = found2;
                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
                    }
                    java.lang.Object element$iv$iv$iv = it.next();
                    org.jsoup.nodes.Element it3 = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    java.lang.String u = it3.attr("src");
                    if (kotlin.text.StringsKt.isBlank(u)) {
                        str = u;
                    } else {
                        str = u;
                        boolean z = kotlin.jvm.internal.Intrinsics.areEqual(u, "#") ? false : true;
                        iframeSrc = z ? str : null;
                        if (iframeSrc == null) {
                            destination$iv$iv.add(iframeSrc);
                        }
                    }
                    if (z) {
                    }
                    if (iframeSrc == null) {
                    }
                }
                break;
            case 1:
                boolean isCasting3 = c00011.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15 = (kotlin.jvm.functions.Function1) c00011.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function16 = (kotlin.jvm.functions.Function1) c00011.L$1;
                java.lang.String data3 = (java.lang.String) c00011.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c000112 = c00011;
                obj = coroutine_suspended;
                data2 = data3;
                isCasting2 = isCasting3;
                function14 = function15;
                function13 = function16;
                obj2 = $result;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                kotlin.jvm.internal.Ref.BooleanRef found22 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("#video-code iframe, iframe[src]");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                it = $this$mapNotNull$iv2.iterator();
                while (true) {
                    if (it.hasNext()) {
                    }
                }
                break;
            case 2:
                boolean z2 = c00011.Z$0;
                found = (kotlin.jvm.internal.Ref.BooleanRef) c00011.L$4;
                kotlin.ResultKt.throwOnFailure($result);
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.GXtapes.GXtapes$loadLinks$3, reason: invalid class name */
    /* JADX INFO: compiled from: GXtapes.kt */
    @kotlin.Metadata(d1 = {"\u0000\f\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\u0010\u0000\u001a\u00020\u00012\u0006\u0010\u0002\u001a\u00020\u0003H\n"}, d2 = {"<anonymous>", "", "url", ""}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GXtapes.GXtapes$loadLinks$3", f = "GXtapes.kt", i = {0}, l = {159}, m = "invokeSuspend", n = {"url"}, nl = {164}, s = {"L$0"}, v = 2)
    static final class AnonymousClass3 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<java.lang.String, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> $callback;
        final /* synthetic */ java.lang.String $data;
        final /* synthetic */ kotlin.jvm.internal.Ref.BooleanRef $found;
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> $subtitleCallback;
        /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass3(java.lang.String str, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.internal.Ref.BooleanRef booleanRef, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super com.GXtapes.GXtapes.AnonymousClass3> continuation) {
            super(2, continuation);
            this.$data = str;
            this.$subtitleCallback = function1;
            this.$found = booleanRef;
            this.$callback = function12;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass3 = new com.GXtapes.GXtapes.AnonymousClass3(this.$data, this.$subtitleCallback, this.$found, this.$callback, continuation);
            anonymousClass3.L$0 = obj;
            return anonymousClass3;
        }

        public final java.lang.Object invoke(java.lang.String str, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
            return create(str, continuation).invokeSuspend(kotlin.Unit.INSTANCE);
        }

        public final java.lang.Object invokeSuspend(java.lang.Object $result) {
            java.lang.Object objLoadExtractor;
            java.lang.String url = (java.lang.String) this.L$0;
            java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
            switch (this.label) {
                case 0:
                    kotlin.ResultKt.throwOnFailure($result);
                    java.lang.String str = this.$data;
                    kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1 = this.$subtitleCallback;
                    final kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12 = this.$callback;
                    this.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                    this.label = 1;
                    objLoadExtractor = com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(url, str, function1, new kotlin.jvm.functions.Function1() { // from class: com.GXtapes.GXtapes$loadLinks$3$$ExternalSyntheticLambda0
                        public final java.lang.Object invoke(java.lang.Object obj) {
                            return com.GXtapes.GXtapes.AnonymousClass3.invokeSuspend$lambda$0(function12, (com.lagradost.cloudstream3.utils.ExtractorLink) obj);
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
            return kotlin.Unit.INSTANCE;
        }

        static final kotlin.Unit invokeSuspend$lambda$0(kotlin.jvm.functions.Function1 $callback, com.lagradost.cloudstream3.utils.ExtractorLink link) {
            $callback.invoke(link);
            return kotlin.Unit.INSTANCE;
        }
    }
}
