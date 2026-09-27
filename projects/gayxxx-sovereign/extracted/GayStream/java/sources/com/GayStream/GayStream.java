package com.GayStream;

/* JADX INFO: compiled from: GayStream.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000z\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\f\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010&\u001a\u00020(2\u0006\u0010)\u001a\u00020*2\u0006\u0010+\u001a\u00020,H\u0096@¢\u0006\u0002\u0010-J\f\u0010.\u001a\u00020/*\u000200H\u0002J\f\u00101\u001a\u00020/*\u000200H\u0002J\u001c\u00102\u001a\b\u0012\u0004\u0012\u00020/0$2\u0006\u00103\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00104J\u0016\u00105\u001a\u0002062\u0006\u00107\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u00104JF\u00108\u001a\u00020\u000e2\u0006\u00109\u001a\u00020\u00052\u0006\u0010:\u001a\u00020\u000e2\u0012\u0010;\u001a\u000e\u0012\u0004\u0012\u00020=\u0012\u0004\u0012\u00020>0<2\u0012\u0010?\u001a\u000e\u0012\u0004\u0012\u00020@\u0012\u0004\u0012\u00020>0<H\u0096@¢\u0006\u0002\u0010AR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u0014\u0010\u0014\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0010R\u0014\u0010\u0016\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0010R\u0014\u0010\u0018\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0019\u0010\u0010R\u001a\u0010\u001a\u001a\b\u0012\u0004\u0012\u00020\u001c0\u001bX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001d\u0010\u001eR\u0014\u0010\u001f\u001a\u00020 X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b!\u0010\"R\u001a\u0010#\u001a\b\u0012\u0004\u0012\u00020%0$X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b&\u0010'¨\u0006B"}, d2 = {"Lcom/GayStream/GayStream;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "hasQuickSearch", "getHasQuickSearch", "hasChromecastSupport", "getHasChromecastSupport", "hasDownloadSupport", "getHasDownloadSupport", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GayStream"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nGayStream.kt\nKotlin\n*S Kotlin\n*F\n+ 1 GayStream.kt\ncom/GayStream/GayStream\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,173:1\n1642#2,10:174\n1915#2:184\n1916#2:186\n1652#2:187\n1642#2,10:188\n1915#2:198\n1916#2:200\n1652#2:201\n1642#2,10:202\n1915#2:212\n1916#2:214\n1652#2:215\n1642#2,10:216\n1915#2:226\n1916#2:229\n1652#2:230\n1642#2,10:231\n1915#2:241\n1916#2:243\n1652#2:244\n1#3:185\n1#3:199\n1#3:213\n1#3:227\n1#3:228\n1#3:242\n*S KotlinDebug\n*F\n+ 1 GayStream.kt\ncom/GayStream/GayStream\n*L\n63#1:174,10\n63#1:184\n63#1:186\n63#1:187\n105#1:188,10\n105#1:198\n105#1:200\n105#1:201\n121#1:202,10\n121#1:212\n121#1:214\n121#1:215\n142#1:216,10\n142#1:226\n142#1:229\n142#1:230\n143#1:231,10\n143#1:241\n143#1:243\n143#1:244\n63#1:185\n105#1:199\n121#1:213\n142#1:228\n143#1:242\n*E\n"})
public final class GayStream extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://gaystream.pw";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "GayStream";
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
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("", "Newest"), kotlin.TuplesKt.to("/?orderby=updated", "Updated"), kotlin.TuplesKt.to("/video/category/4k", "4K"), kotlin.TuplesKt.to("/?orderby=likes", "Like"), kotlin.TuplesKt.to("/?orderby=latest", "Latest"), kotlin.TuplesKt.to("/?orderby=views", "Views"), kotlin.TuplesKt.to("/video/channel/onlyfans", "Onlyfans"), kotlin.TuplesKt.to("/performer/ashton-summers", "Ashton Summers"), kotlin.TuplesKt.to("/performer/bruno-galvez", "Bruno Galvez"), kotlin.TuplesKt.to("/performer/julio-pisco", "Julio Pisco"), kotlin.TuplesKt.to("/performer/damian-night", "Daminan Night"), kotlin.TuplesKt.to("/video/category/anal", "Anal"), kotlin.TuplesKt.to("/video/category/asian", "Asian"), kotlin.TuplesKt.to("/video/category/dp", "DP"), kotlin.TuplesKt.to("/video/category/group", "Group"), kotlin.TuplesKt.to("/video/category/homemade", "Homemade"), kotlin.TuplesKt.to("/video/category/hunk", "Hunk"), kotlin.TuplesKt.to("/video/category/interracial", "Interracial"), kotlin.TuplesKt.to("/video/category/latino", "Latino"), kotlin.TuplesKt.to("/video/category/mature", "Mature"), kotlin.TuplesKt.to("/video/category/muscle", "Muscle"), kotlin.TuplesKt.to("/video/category/promotion", "Promotion"), kotlin.TuplesKt.to("/video/category/threesome", "Threesome"), kotlin.TuplesKt.to("/video/category/uniforms", "Uniforms"), kotlin.TuplesKt.to("/video/channel/alphastudiogroup", "Alpha Studio Group"), kotlin.TuplesKt.to("/video/channel/betabetapi", "Beta Beta Pi"), kotlin.TuplesKt.to("/video/channel/caninolatino", "Canino Latino")});

    /* JADX INFO: renamed from: com.GayStream.GayStream$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream", f = "GayStream.kt", i = {0, 0, 0}, l = {60}, m = "getMainPage", n = {"request", "pageUrl", "page"}, nl = {63}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GayStream.GayStream.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.GayStream.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GayStream.GayStream$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream", f = "GayStream.kt", i = {0, 1, 1, 1, 1, 1, 1}, l = {116, 123}, m = "load", n = {"url", "url", "document", "title", "poster", "description", "recommendations"}, nl = {118, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.GayStream.GayStream.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.GayStream.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GayStream.GayStream$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream", f = "GayStream.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1}, l = {137, 160}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "document", "found", "videoUrls", "button", "isCasting"}, nl = {138, 169}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "Z$0"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00011(kotlin.coroutines.Continuation<? super com.GayStream.GayStream.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.GayStream.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.GayStream.GayStream$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream", f = "GayStream.kt", i = {0, 0, 0}, l = {104}, m = "search", n = {"query", "searchResponse", "i"}, nl = {105}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super com.GayStream.GayStream.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.GayStream.this.search(null, (kotlin.coroutines.Continuation) this);
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
        com.GayStream.GayStream.AnonymousClass1 anonymousClass1;
        com.lagradost.cloudstream3.MainPageRequest request2;
        int page2 = page;
        if (continuation instanceof com.GayStream.GayStream.AnonymousClass1) {
            anonymousClass1 = (com.GayStream.GayStream.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.GayStream.GayStream.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String pageUrl = page2 == 1 ? getMainUrl() + request.getData() : getMainUrl() + request.getData() + "/page/" + page2;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pageUrl);
                anonymousClass1.I$0 = page2;
                anonymousClass1.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, pageUrl, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 4094, (java.lang.Object) null);
                if ($result == coroutine_suspended) {
                    return coroutine_suspended;
                }
                request2 = request;
                break;
                break;
            case 1:
                page2 = anonymousClass1.I$0;
                request2 = (com.lagradost.cloudstream3.MainPageRequest) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.grid-wrap");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            int page3 = page2;
            org.jsoup.nodes.Element wrap = (org.jsoup.nodes.Element) element$iv$iv$iv;
            org.jsoup.nodes.Element elementSelectFirst = wrap.selectFirst("div.grid-item");
            com.lagradost.cloudstream3.SearchResponse searchResult = elementSelectFirst != null ? toSearchResult(elementSelectFirst) : null;
            if (searchResult != null) {
                destination$iv$iv.add(searchResult);
            }
            page2 = page3;
        }
        java.util.List items = (java.util.List) destination$iv$iv;
        boolean hasNext = document.selectFirst("a.next.page-numbers") != null;
        return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request2.getName(), items, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(hasNext));
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String title = $this$toSearchResult.select("h3.item-title").text();
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, $this$toSearchResult.select("a.item-wrap").attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toSearchResult.select("img.item-img").attr("src"));
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.GayStream.GayStream$$ExternalSyntheticLambda1
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.GayStream.GayStream.toSearchResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        java.lang.String title = $this$toRecommendResult.select("h3.item-title").text();
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, $this$toRecommendResult.select("a.item-wrap").attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toRecommendResult.select("img.item-img").attr("src"));
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.GayStream.GayStream$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.GayStream.GayStream.toRecommendResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toRecommendResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:16:0x0063  */
    /* JADX WARN: Removed duplicated region for block: B:23:0x00fd  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0129  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x0139  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x0140  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:19:0x00d0 -> B:20:0x00d9). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        com.GayStream.GayStream.C00021 c00021;
        com.GayStream.GayStream gayStream;
        java.util.List searchResponse;
        com.GayStream.GayStream.C00021 c000212;
        com.GayStream.GayStream gayStream2;
        java.lang.String query2;
        int i;
        java.util.List results;
        if (continuation instanceof com.GayStream.GayStream.C00021) {
            c00021 = (com.GayStream.GayStream.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
                gayStream = this;
            } else {
                gayStream = this;
                c00021 = gayStream.new C00021(continuation);
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
                com.GayStream.GayStream gayStream3 = gayStream;
                com.GayStream.GayStream.C00021 c000213 = c00021;
                java.lang.String query3 = query;
                if (i2 >= 6) {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = gayStream3.getMainUrl() + "/page/" + i2 + "?s=" + query3 + "&search=";
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
                    gayStream2 = gayStream3;
                    searchResponse = searchResponse3;
                    query2 = query4;
                    i = i3;
                    org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.Iterable $this$mapNotNull$iv = document.select("div.grid-item");
                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                        java.lang.String query5 = query2;
                        org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                        com.lagradost.cloudstream3.SearchResponse searchResult = gayStream2.toSearchResult(it);
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
                    gayStream3 = gayStream2;
                    c000213 = c000212;
                    query3 = query6;
                    if (i2 >= 6) {
                        return searchResponse;
                    }
                }
                break;
            case 1:
                i = c00021.I$0;
                searchResponse = (java.util.List) c00021.L$1;
                java.lang.String query7 = (java.lang.String) c00021.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c000212 = c00021;
                query2 = query7;
                gayStream2 = gayStream;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = document2.select("div.grid-item");
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
        com.GayStream.GayStream.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String title;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        java.lang.String strAttr3;
        if (continuation instanceof com.GayStream.GayStream.C00001) {
            c00001 = (com.GayStream.GayStream.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.GayStream.GayStream.C00001(continuation);
            }
        }
        com.GayStream.GayStream.C00001 c000012 = c00001;
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
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.grid-item");
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
        com.GayStream.GayStream.AnonymousClass2 anonymousClass2 = new com.GayStream.GayStream.AnonymousClass2(poster, description, recommendations, null);
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

    /* JADX INFO: renamed from: com.GayStream.GayStream$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream$load$2", f = "GayStream.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list, kotlin.coroutines.Continuation<? super com.GayStream.GayStream.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$recommendations = list;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.GayStream.GayStream.AnonymousClass2(this.$poster, this.$description, this.$recommendations, continuation);
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
    /* JADX WARN: Removed duplicated region for block: B:29:0x012f  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x0132  */
    /* JADX WARN: Removed duplicated region for block: B:32:0x0135  */
    /* JADX WARN: Removed duplicated region for block: B:37:0x015f  */
    /* JADX WARN: Removed duplicated region for block: B:69:0x0139 A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:70:0x01aa A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.GayStream.GayStream.C00011 c00011;
        java.lang.Object obj;
        com.GayStream.GayStream.C00011 c000112;
        java.lang.String data2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.Object obj2;
        boolean isCasting2;
        java.lang.Iterable $this$mapNotNull$iv;
        int $i$f$mapNotNull;
        java.lang.Iterable $this$mapNotNullTo$iv$iv;
        java.util.Iterator it;
        kotlin.jvm.internal.Ref.BooleanRef found;
        java.util.List groupValues;
        java.lang.String str;
        java.lang.String str2;
        if (continuation instanceof com.GayStream.GayStream.C00011) {
            c00011 = (com.GayStream.GayStream.C00011) continuation;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
            } else {
                c00011 = new com.GayStream.GayStream.C00011(continuation);
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
                com.GayStream.GayStream.C00011 c000113 = c00011;
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
                java.lang.Iterable $this$mapNotNull$iv2 = document.select("div.tabs-wrap button[onclick]");
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv2) {
                    org.jsoup.nodes.Element it2 = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    java.lang.String u = it2.attr("onclick");
                    if (kotlin.text.StringsKt.isBlank(u)) {
                        str = u;
                    } else {
                        str = u;
                        boolean z = kotlin.jvm.internal.Intrinsics.areEqual(u, "#") ? false : true;
                        str2 = !z ? str : null;
                        if (str2 == null) {
                            destination$iv$iv.add(str2);
                        }
                    }
                    if (!z) {
                    }
                    if (str2 == null) {
                    }
                }
                $this$mapNotNull$iv = (java.util.List) destination$iv$iv;
                $i$f$mapNotNull = 0;
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                $this$mapNotNullTo$iv$iv = $this$mapNotNull$iv;
                it = $this$mapNotNullTo$iv$iv.iterator();
                while (true) {
                    java.lang.Iterable $this$mapNotNullTo$iv$iv2 = $this$mapNotNullTo$iv$iv;
                    if (it.hasNext()) {
                        java.lang.String data3 = data2;
                        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function15 = function13;
                        java.util.Set videoUrls = kotlin.collections.CollectionsKt.toMutableSet((java.util.List) destination$iv$iv2);
                        if (videoUrls.isEmpty()) {
                            org.jsoup.nodes.Element elementSelectFirst = document.selectFirst("iframe#ifr");
                            java.lang.String iframeSrc = elementSelectFirst != null ? elementSelectFirst.attr("src") : null;
                            if (iframeSrc != null) {
                                java.lang.String it3 = iframeSrc;
                                kotlin.coroutines.jvm.internal.Boxing.boxBoolean(videoUrls.add(it3));
                            }
                        }
                        org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("a.video-download[href]");
                        java.lang.String button = elementSelectFirst2 != null ? elementSelectFirst2.attr("href") : null;
                        if (button != null) {
                            kotlin.coroutines.jvm.internal.Boxing.boxBoolean(videoUrls.add(button));
                        }
                        java.util.List list = kotlin.collections.CollectionsKt.toList(videoUrls);
                        com.GayStream.GayStream.AnonymousClass4 anonymousClass4 = new com.GayStream.GayStream.AnonymousClass4(data3, function15, found2, function14, null);
                        c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data3);
                        c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                        c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                        c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        c000112.L$4 = found2;
                        c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrls);
                        c000112.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(button);
                        c000112.Z$0 = isCasting2;
                        c000112.label = 2;
                        if (com.lagradost.cloudstream3.ParCollectionsKt.amap(list, anonymousClass4, c000112) == obj) {
                            return obj;
                        }
                        found = found2;
                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(found.element);
                    }
                    java.lang.Object element$iv$iv$iv2 = it.next();
                    java.lang.String onclick = (java.lang.String) element$iv$iv$iv2;
                    java.lang.Iterable $this$mapNotNull$iv3 = $this$mapNotNull$iv;
                    int $i$f$mapNotNull2 = $i$f$mapNotNull;
                    java.lang.String data4 = data2;
                    kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function16 = function13;
                    kotlin.text.MatchResult matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("src=(?:&quot;|\"|')(.*?)(?:&quot;|\"|')"), onclick, 0, 2, (java.lang.Object) null);
                    java.lang.String str3 = (matchResultFind$default == null || (groupValues = matchResultFind$default.getGroupValues()) == null) ? null : (java.lang.String) groupValues.get(1);
                    if (str3 != null) {
                        destination$iv$iv2.add(str3);
                    }
                    data2 = data4;
                    function13 = function16;
                    $this$mapNotNullTo$iv$iv = $this$mapNotNullTo$iv$iv2;
                    $this$mapNotNull$iv = $this$mapNotNull$iv3;
                    $i$f$mapNotNull = $i$f$mapNotNull2;
                }
                break;
            case 1:
                boolean isCasting3 = c00011.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) c00011.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18 = (kotlin.jvm.functions.Function1) c00011.L$1;
                java.lang.String data5 = (java.lang.String) c00011.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                c000112 = c00011;
                obj = coroutine_suspended;
                data2 = data5;
                isCasting2 = isCasting3;
                function14 = function17;
                function13 = function18;
                obj2 = $result;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                kotlin.jvm.internal.Ref.BooleanRef found22 = new kotlin.jvm.internal.Ref.BooleanRef();
                java.lang.Iterable $this$mapNotNull$iv22 = document2.select("div.tabs-wrap button[onclick]");
                java.util.Collection destination$iv$iv3 = new java.util.ArrayList();
                while (r17.hasNext()) {
                }
                $this$mapNotNull$iv = (java.util.List) destination$iv$iv3;
                $i$f$mapNotNull = 0;
                java.util.Collection destination$iv$iv22 = new java.util.ArrayList();
                $this$mapNotNullTo$iv$iv = $this$mapNotNull$iv;
                it = $this$mapNotNullTo$iv$iv.iterator();
                while (true) {
                    java.lang.Iterable $this$mapNotNullTo$iv$iv22 = $this$mapNotNullTo$iv$iv;
                    if (it.hasNext()) {
                    }
                    data2 = data4;
                    function13 = function16;
                    $this$mapNotNullTo$iv$iv = $this$mapNotNullTo$iv$iv22;
                    $this$mapNotNull$iv = $this$mapNotNull$iv3;
                    $i$f$mapNotNull = $i$f$mapNotNull2;
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

    /* JADX INFO: renamed from: com.GayStream.GayStream$loadLinks$4, reason: invalid class name */
    /* JADX INFO: compiled from: GayStream.kt */
    @kotlin.Metadata(d1 = {"\u0000\f\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\u0010\u0000\u001a\u00020\u00012\u0006\u0010\u0002\u001a\u00020\u0003H\n"}, d2 = {"<anonymous>", "", "url", ""}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.GayStream$loadLinks$4", f = "GayStream.kt", i = {0}, l = {161}, m = "invokeSuspend", n = {"url"}, nl = {166}, s = {"L$0"}, v = 2)
    static final class AnonymousClass4 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<java.lang.String, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> $callback;
        final /* synthetic */ java.lang.String $data;
        final /* synthetic */ kotlin.jvm.internal.Ref.BooleanRef $found;
        final /* synthetic */ kotlin.jvm.functions.Function1<com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> $subtitleCallback;
        /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass4(java.lang.String str, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.internal.Ref.BooleanRef booleanRef, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super com.GayStream.GayStream.AnonymousClass4> continuation) {
            super(2, continuation);
            this.$data = str;
            this.$subtitleCallback = function1;
            this.$found = booleanRef;
            this.$callback = function12;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass4 = new com.GayStream.GayStream.AnonymousClass4(this.$data, this.$subtitleCallback, this.$found, this.$callback, continuation);
            anonymousClass4.L$0 = obj;
            return anonymousClass4;
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
                    objLoadExtractor = com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(url, str, function1, new kotlin.jvm.functions.Function1() { // from class: com.GayStream.GayStream$loadLinks$4$$ExternalSyntheticLambda0
                        public final java.lang.Object invoke(java.lang.Object obj) {
                            return com.GayStream.GayStream.AnonymousClass4.invokeSuspend$lambda$0(function12, (com.lagradost.cloudstream3.utils.ExtractorLink) obj);
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
