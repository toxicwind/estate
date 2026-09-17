package com.BoyfriendTV;

/* JADX INFO: compiled from: BoyfriendTV.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000z\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010\u001f\u001a\u00020!2\u0006\u0010\"\u001a\u00020#2\u0006\u0010$\u001a\u00020%H\u0096@¢\u0006\u0002\u0010&J\u000e\u0010'\u001a\u0004\u0018\u00010(*\u00020)H\u0002J\u000e\u0010*\u001a\u0004\u0018\u00010(*\u00020)H\u0002J\u001c\u0010+\u001a\b\u0012\u0004\u0012\u00020(0\u001d2\u0006\u0010,\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010-J\u0018\u0010.\u001a\u0004\u0018\u00010/2\u0006\u00100\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010-JF\u00101\u001a\u00020\u000e2\u0006\u00102\u001a\u00020\u00052\u0006\u00103\u001a\u00020\u000e2\u0012\u00104\u001a\u000e\u0012\u0004\u0012\u000206\u0012\u0004\u0012\u000207052\u0012\u00108\u001a\u000e\u0012\u0004\u0012\u000209\u0012\u0004\u0012\u00020705H\u0096@¢\u0006\u0002\u0010:R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u0014\u0010\u0011\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0012\u0010\u0010R\u0014\u0010\u0013\u001a\u00020\u0014X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0016R\u001a\u0010\u0017\u001a\b\u0012\u0004\u0012\u00020\u00190\u0018X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001a\u0010\u001bR\u001a\u0010\u001c\u001a\b\u0012\u0004\u0012\u00020\u001e0\u001dX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001f\u0010 ¨\u0006;"}, d2 = {"Lcom/BoyfriendTV/BoyfriendTV;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "hasDownloadSupport", "getHasDownloadSupport", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "BoyfriendTV"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nBoyfriendTV.kt\nKotlin\n*S Kotlin\n*F\n+ 1 BoyfriendTV.kt\ncom/BoyfriendTV/BoyfriendTV\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,211:1\n1642#2,10:212\n1915#2:222\n1916#2:224\n1652#2:225\n1642#2,10:226\n1915#2:236\n1916#2:238\n1652#2:239\n1586#2:241\n1661#2,3:242\n777#2:245\n873#2,2:246\n1642#2,10:248\n1915#2:258\n1916#2:260\n1652#2:261\n1915#2,2:262\n1#3:223\n1#3:237\n1#3:240\n1#3:259\n*S KotlinDebug\n*F\n+ 1 BoyfriendTV.kt\ncom/BoyfriendTV/BoyfriendTV\n*L\n46#1:212,10\n46#1:222\n46#1:224\n46#1:225\n79#1:226,10\n79#1:236\n79#1:238\n79#1:239\n97#1:241\n97#1:242,3\n98#1:245\n98#1:246,2\n100#1:248,10\n100#1:258\n100#1:260\n100#1:261\n207#1:262,2\n46#1:223\n79#1:237\n100#1:259\n*E\n"})
public final class BoyfriendTV extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://www.boyfriendtv.com";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Boyfriendtv";
    private final boolean hasMainPage = true;
    private final boolean hasDownloadSupport = true;

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to("", "Trending"), kotlin.TuplesKt.to("/?filter_quality=hd&s=&sort=newest", "Mới nhất"), kotlin.TuplesKt.to("/?filter_quality=hd&s=&sort=most-popular", "Phổ biến"), kotlin.TuplesKt.to("/search/?q=Vietnamese", "Việt Nam"), kotlin.TuplesKt.to("/search/?q=asian&hot=", "Asian"), kotlin.TuplesKt.to("/?filter_quality=hd&s=&sort=most-popular", "Phổ biến"), kotlin.TuplesKt.to("/search/?q=chinese&hot=&quality=hd", "Tung Của"), kotlin.TuplesKt.to("/tags/brazilian/?filter_quality=hd", "Bờ ra sin"), kotlin.TuplesKt.to("/tags/gangbang/?filter_quality=hd", "Chịch tập thể"), kotlin.TuplesKt.to("/tags/latinos/?filter_quality=hd", "Mỹ da màu"), kotlin.TuplesKt.to("/search/?q=facedownassup&quality=hd", "Face down Ass up"), kotlin.TuplesKt.to("/search/?q=sketchysex&quality=hd", "Sketchy Sex"), kotlin.TuplesKt.to("/search/?q=fraternity&quality=hd", "Fraternity X"), kotlin.TuplesKt.to("/search/?q=slamrush", "Slam Rush")});

    /* JADX INFO: renamed from: com.BoyfriendTV.BoyfriendTV$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: BoyfriendTV.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.BoyfriendTV.BoyfriendTV", f = "BoyfriendTV.kt", i = {0, 0, 0}, l = {44}, m = "getMainPage", n = {"request", "pageUrl", "page"}, nl = {46}, s = {"L$0", "L$1", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.BoyfriendTV.BoyfriendTV.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.BoyfriendTV.BoyfriendTV.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.BoyfriendTV.BoyfriendTV$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: BoyfriendTV.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.BoyfriendTV.BoyfriendTV", f = "BoyfriendTV.kt", i = {0, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {84, 104}, m = "load", n = {"url", "url", "document", "ldJsonText", "ldJson", "title", "description", "poster", "tags", "recommendations"}, nl = {86, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        java.lang.Object L$7;
        java.lang.Object L$8;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.BoyfriendTV.BoyfriendTV.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.BoyfriendTV.BoyfriendTV.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.BoyfriendTV.BoyfriendTV$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: BoyfriendTV.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.BoyfriendTV.BoyfriendTV", f = "BoyfriendTV.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3}, l = {119, 136, 172, 193}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "html", "templateMatch", "templateUrl", "masterUrl", "isCasting", "data", "subtitleCallback", "callback", "html", "templateMatch", "templateUrl", "masterUrl", "masterContent", "links", "baseDomain", "lines", "currentResolution", "line", "variantPath", "fullVariantUrl", "isCasting", "quality", "data", "subtitleCallback", "callback", "html", "templateMatch", "templateUrl", "masterUrl", "masterContent", "links", "isCasting"}, nl = {125, 139, 177, 198}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$13", "L$14", "L$15", "Z$0", "I$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "Z$0"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
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
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00011(kotlin.coroutines.Continuation<? super com.BoyfriendTV.BoyfriendTV.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.BoyfriendTV.BoyfriendTV.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.BoyfriendTV.BoyfriendTV$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: BoyfriendTV.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.BoyfriendTV.BoyfriendTV", f = "BoyfriendTV.kt", i = {0, 0}, l = {78}, m = "search", n = {"query", "url"}, nl = {79}, s = {"L$0", "L$1"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super com.BoyfriendTV.BoyfriendTV.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.BoyfriendTV.BoyfriendTV.this.search(null, (kotlin.coroutines.Continuation) this);
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

    public boolean getHasDownloadSupport() {
        return this.hasDownloadSupport;
    }

    @org.jetbrains.annotations.NotNull
    public com.lagradost.cloudstream3.VPNStatus getVpnStatus() {
        return this.vpnStatus;
    }

    @org.jetbrains.annotations.NotNull
    public java.util.Set<com.lagradost.cloudstream3.TvType> getSupportedTypes() {
        return this.supportedTypes;
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
        com.BoyfriendTV.BoyfriendTV.AnonymousClass1 anonymousClass1;
        java.lang.StringBuilder sb;
        java.lang.StringBuilder sbAppend;
        com.lagradost.cloudstream3.MainPageRequest request2;
        if (continuation instanceof com.BoyfriendTV.BoyfriendTV.AnonymousClass1) {
            anonymousClass1 = (com.BoyfriendTV.BoyfriendTV.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.BoyfriendTV.BoyfriendTV.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                if (page == 1) {
                    sb = new java.lang.StringBuilder();
                    sbAppend = sb.append(getMainUrl()).append(request.getData());
                } else {
                    sb = new java.lang.StringBuilder();
                    sbAppend = sb.append(getMainUrl()).append(request.getData()).append("/?page=").append(page);
                }
                java.lang.String pageUrl = sbAppend.toString();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pageUrl);
                anonymousClass1.I$0 = page;
                anonymousClass1.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, pageUrl, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 4094, (java.lang.Object) null);
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
        java.lang.Iterable $this$mapNotNull$iv = document.select("ul.media-listing-grid.main-listing-grid-offset li");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
            if (searchResult != null) {
                destination$iv$iv.add(searchResult);
            }
        }
        java.util.List items = (java.util.List) destination$iv$iv;
        return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse(new com.lagradost.cloudstream3.HomePageList(request2.getName(), items, true), kotlin.coroutines.jvm.internal.Boxing.boxBoolean(!items.isEmpty()));
    }

    private final com.lagradost.cloudstream3.SearchResponse toSearchResult(org.jsoup.nodes.Element $this$toSearchResult) {
        java.lang.String title;
        org.jsoup.nodes.Element elementSelectFirst = $this$toSearchResult.selectFirst("p.titlevideospot a");
        if (elementSelectFirst == null || (title = elementSelectFirst.text()) == null) {
            return null;
        }
        org.jsoup.nodes.Element elementSelectFirst2 = $this$toSearchResult.selectFirst("a");
        kotlin.jvm.internal.Intrinsics.checkNotNull(elementSelectFirst2);
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, elementSelectFirst2.attr("href"));
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, $this$toSearchResult.select("img").attr("src"));
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.Movie, false, new kotlin.jvm.functions.Function1() { // from class: com.BoyfriendTV.BoyfriendTV$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.BoyfriendTV.BoyfriendTV.toSearchResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        java.lang.String title;
        org.jsoup.nodes.Element elementSelectFirst = $this$toRecommendResult.selectFirst(".media-item__title");
        if (elementSelectFirst == null || (title = elementSelectFirst.text()) == null) {
            return null;
        }
        org.jsoup.nodes.Element elementSelectFirst2 = $this$toRecommendResult.selectFirst("a");
        kotlin.jvm.internal.Intrinsics.checkNotNull(elementSelectFirst2);
        java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, elementSelectFirst2.attr("href"));
        com.BoyfriendTV.BoyfriendTV boyfriendTV = this;
        org.jsoup.nodes.Element elementSelectFirst3 = $this$toRecommendResult.selectFirst("img");
        final java.lang.String posterUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(boyfriendTV, elementSelectFirst3 != null ? elementSelectFirst3.attr("src") : null);
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.Movie, false, new kotlin.jvm.functions.Function1() { // from class: com.BoyfriendTV.BoyfriendTV$$ExternalSyntheticLambda1
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.BoyfriendTV.BoyfriendTV.toRecommendResult$lambda$0(posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toRecommendResult$lambda$0(java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($posterUrl);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        com.BoyfriendTV.BoyfriendTV.C00021 c00021;
        if (continuation instanceof com.BoyfriendTV.BoyfriendTV.C00021) {
            c00021 = (com.BoyfriendTV.BoyfriendTV.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
            } else {
                c00021 = new com.BoyfriendTV.BoyfriendTV.C00021(continuation);
            }
        }
        java.lang.Object $result = c00021.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00021.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String url = getMainUrl() + "/search/?q=" + query;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c00021.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(query);
                c00021.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                c00021.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c00021, 4094, (java.lang.Object) null);
                if ($result == coroutine_suspended) {
                    return coroutine_suspended;
                }
                break;
                break;
            case 1:
                kotlin.ResultKt.throwOnFailure($result);
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
        java.lang.Iterable $this$mapNotNull$iv = document.select("ul.media-listing-grid.main-listing-grid-offset li");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse searchResult = toSearchResult(it);
            if (searchResult != null) {
                destination$iv$iv.add(searchResult);
            }
        }
        return (java.util.List) destination$iv$iv;
    }

    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object load(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.LoadResponse> continuation) {
        com.BoyfriendTV.BoyfriendTV.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.lang.String url2;
        org.jsoup.nodes.Element elementSelectFirst;
        java.lang.String ldJsonText;
        org.json.JSONObject ldJson;
        java.lang.String title;
        java.lang.String it;
        if (continuation instanceof com.BoyfriendTV.BoyfriendTV.C00001) {
            c00001 = (com.BoyfriendTV.BoyfriendTV.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.BoyfriendTV.BoyfriendTV.C00001(continuation);
            }
        }
        com.BoyfriendTV.BoyfriendTV.C00001 c000012 = c00001;
        java.lang.Object element$iv$iv = c000012.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000012.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure(element$iv$iv);
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
                org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                elementSelectFirst = document.selectFirst("script[type=application/ld+json]");
                if (elementSelectFirst != null || (ldJsonText = elementSelectFirst.data()) == null || (title = (ldJson = new org.json.JSONObject(ldJsonText)).optString("name")) == null) {
                    return null;
                }
                java.lang.String description = ldJson.optString("description", "");
                org.json.JSONArray jSONArrayOptJSONArray = ldJson.optJSONArray("thumbnailUrl");
                java.lang.String poster = (jSONArrayOptJSONArray == null || (it = jSONArrayOptJSONArray.optString(0)) == null) ? null : com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, it);
                java.lang.Iterable $this$map$iv = kotlin.text.StringsKt.split$default(description, new java.lang.String[]{","}, false, 0, 6, (java.lang.Object) null);
                java.util.Collection destination$iv$iv = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv, 10));
                for (java.lang.Object item$iv$iv : $this$map$iv) {
                    destination$iv$iv.add(kotlin.text.StringsKt.replace$default(kotlin.text.StringsKt.trim((java.lang.String) item$iv$iv).toString(), "-", "", false, 4, (java.lang.Object) null));
                }
                java.lang.Iterable $this$filter$iv = (java.util.List) destination$iv$iv;
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv2 : $this$filter$iv) {
                    java.lang.Object $result = element$iv$iv;
                    java.lang.String it2 = (java.lang.String) element$iv$iv2;
                    if ((kotlin.text.StringsKt.isBlank(it2) || org.jsoup.internal.StringUtil.isNumeric(it2)) ? false : true) {
                        destination$iv$iv2.add(element$iv$iv2);
                    }
                    element$iv$iv = $result;
                }
                java.util.List tags = (java.util.List) destination$iv$iv2;
                java.lang.Iterable $this$mapNotNull$iv = document.select(".media-item");
                java.util.Collection destination$iv$iv3 = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                    java.lang.Iterable $this$mapNotNull$iv2 = $this$mapNotNull$iv;
                    com.lagradost.cloudstream3.SearchResponse recommendResult = toRecommendResult((org.jsoup.nodes.Element) element$iv$iv$iv);
                    if (recommendResult != null) {
                        destination$iv$iv3.add(recommendResult);
                    }
                    $this$mapNotNull$iv = $this$mapNotNull$iv2;
                }
                java.util.List recommendations = (java.util.List) destination$iv$iv3;
                com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.NSFW;
                com.BoyfriendTV.BoyfriendTV.AnonymousClass2 anonymousClass2 = new com.BoyfriendTV.BoyfriendTV.AnonymousClass2(poster, description, tags, recommendations, null);
                c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ldJsonText);
                c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ldJson);
                c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
                c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
                c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
                c000012.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(tags);
                c000012.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
                c000012.label = 2;
                element$iv$iv = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType, url2, anonymousClass2, c000012);
                return element$iv$iv == obj ? obj : element$iv$iv;
            case 1:
                java.lang.String url3 = (java.lang.String) c000012.L$0;
                kotlin.ResultKt.throwOnFailure(element$iv$iv);
                obj = coroutine_suspended;
                url2 = url3;
                obj2 = element$iv$iv;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                elementSelectFirst = document2.selectFirst("script[type=application/ld+json]");
                if (elementSelectFirst != null) {
                }
                return null;
            case 2:
                kotlin.ResultKt.throwOnFailure(element$iv$iv);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.BoyfriendTV.BoyfriendTV$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: BoyfriendTV.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.BoyfriendTV.BoyfriendTV$load$2", f = "BoyfriendTV.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        final /* synthetic */ java.util.List<java.lang.String> $tags;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<java.lang.String> list, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list2, kotlin.coroutines.Continuation<? super com.BoyfriendTV.BoyfriendTV.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$tags = list;
            this.$recommendations = list2;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.BoyfriendTV.BoyfriendTV.AnonymousClass2(this.$poster, this.$description, this.$tags, this.$recommendations, continuation);
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
                    $this$newMovieLoadResponse.setTags(this.$tags);
                    $this$newMovieLoadResponse.setRecommendations(this.$recommendations);
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }

    /* JADX WARN: Path cross not found for [B:61:0x0365, B:65:0x036e], limit reached: 155 */
    /* JADX WARN: Path cross not found for [B:65:0x036e, B:61:0x0365], limit reached: 155 */
    /* JADX WARN: Removed duplicated region for block: B:121:0x0661  */
    /* JADX WARN: Removed duplicated region for block: B:126:0x06f6  */
    /* JADX WARN: Removed duplicated region for block: B:130:0x0706 A[LOOP:0: B:128:0x0700->B:130:0x0706, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:61:0x0365  */
    /* JADX WARN: Removed duplicated region for block: B:67:0x0371  */
    /* JADX WARN: Removed duplicated region for block: B:72:0x03b0  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:113:0x0558 -> B:114:0x0574). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.BoyfriendTV.BoyfriendTV.C00011 c00011;
        com.BoyfriendTV.BoyfriendTV boyfriendTV;
        java.lang.String str;
        java.lang.Object obj;
        java.lang.String str2;
        java.lang.String str3;
        java.lang.String str4;
        java.lang.Object obj2;
        java.lang.String str5;
        java.lang.Object $result;
        java.lang.Object obj3;
        java.lang.String data2;
        boolean isCasting2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        kotlin.text.MatchResult templateMatch;
        java.util.List groupValues;
        java.lang.String str6;
        java.lang.String templateUrl;
        com.BoyfriendTV.BoyfriendTV.C00011 c000112;
        boolean z;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String str7;
        java.lang.Object obj4;
        java.lang.String str8;
        java.lang.String html;
        java.lang.String str9;
        java.lang.String masterUrl;
        java.lang.String variantPath;
        kotlin.text.MatchResult templateMatch2;
        java.lang.String templateUrl2;
        boolean isCasting3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16;
        java.lang.String baseDomain;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17;
        com.lagradost.nicehttp.Requests app;
        java.lang.Object obj5;
        java.lang.String str10;
        java.util.Map mapMapOf;
        boolean isCasting4;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function18;
        java.lang.Object obj6;
        java.lang.String masterUrl2;
        java.lang.String masterContent;
        java.util.ArrayList links;
        java.lang.String str11;
        java.lang.Object $result2;
        java.lang.String str12;
        java.lang.String str13;
        java.lang.String masterUrl3;
        char c;
        com.BoyfriendTV.BoyfriendTV boyfriendTV2;
        java.lang.String masterUrl4;
        boolean isCasting5;
        kotlin.text.MatchResult templateMatch3;
        java.lang.Object $result3;
        java.lang.Object obj7;
        java.util.List links2;
        java.lang.String templateUrl3;
        com.BoyfriendTV.BoyfriendTV.C00011 c000113;
        java.lang.String templateUrl4;
        java.lang.String html2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19;
        java.lang.String str14;
        boolean isCasting6;
        int i;
        java.lang.String baseDomain2;
        java.util.List lines;
        java.lang.Object obj8;
        boolean isCasting7;
        java.lang.Integer currentResolution;
        java.util.Iterator it;
        com.BoyfriendTV.BoyfriendTV.C00011 c000114;
        java.lang.Object $result4;
        java.lang.String masterUrl5;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation2;
        java.lang.String html3;
        kotlin.text.MatchResult templateMatch4;
        java.lang.String html4;
        java.lang.String masterUrl6;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function110;
        java.util.List links3;
        java.lang.Object $result5;
        java.util.List groupValues2;
        java.lang.String str15;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation3;
        java.lang.String masterUrl7;
        com.BoyfriendTV.BoyfriendTV.C00011 c000115;
        java.lang.Object obj9;
        java.lang.String line;
        java.lang.String variantPath2;
        java.lang.String masterUrl8;
        java.lang.Object obj10;
        boolean isCasting8;
        java.lang.Integer currentResolution2;
        java.util.Iterator it2;
        char c2;
        java.lang.String fullVariantUrl;
        int quality;
        char c3;
        java.util.Iterator it3;
        java.lang.String variantPath3;
        java.lang.String masterUrl9;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function111;
        java.lang.String data3;
        java.lang.String data4;
        com.BoyfriendTV.BoyfriendTV.C00011 c000116;
        java.lang.String line2;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation4 = continuation;
        if (continuation4 instanceof com.BoyfriendTV.BoyfriendTV.C00011) {
            c00011 = (com.BoyfriendTV.BoyfriendTV.C00011) continuation4;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
                boyfriendTV = this;
            } else {
                boyfriendTV = this;
                c00011 = boyfriendTV.new C00011(continuation4);
            }
        }
        com.BoyfriendTV.BoyfriendTV.C00011 c000117 = c00011;
        java.lang.Object $result6 = c000117.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000117.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result6);
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.util.Map mapMapOf2 = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"), kotlin.TuplesKt.to("Referer", "https://www.boyfriendtv.com/")});
                c000117.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data);
                c000117.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                c000117.L$2 = function12;
                c000117.Z$0 = isCasting;
                c000117.label = 1;
                str = "#EXT-X-STREAM-INF";
                obj = "Referer";
                str2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                str3 = "User-Agent";
                str4 = "https://www.boyfriendtv.com/";
                obj2 = coroutine_suspended;
                str5 = null;
                $result = $result6;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app2, data, mapMapOf2, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000117, 4092, (java.lang.Object) null);
                c000117 = c000117;
                if (obj3 == obj2) {
                    return obj2;
                }
                data2 = data;
                isCasting2 = isCasting;
                function13 = function1;
                function14 = function12;
                java.lang.String html5 = ((com.lagradost.nicehttp.NiceResponse) obj3).getText();
                templateMatch = kotlin.text.Regex.find$default(new kotlin.text.Regex("\"hlsAuto\"\\s*:\\s*\"([^\"]+)\""), html5, 0, 2, str5);
                if (templateMatch != null || (groupValues = templateMatch.getGroupValues()) == null || (str6 = (java.lang.String) groupValues.get(1)) == null || (templateUrl = kotlin.text.StringsKt.replace$default(str6, "\\/", "/", false, 4, (java.lang.Object) null)) == null) {
                    return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                }
                try {
                    app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    kotlin.Pair[] pairArr = new kotlin.Pair[2];
                    java.lang.String str16 = str2;
                    java.lang.String str17 = str3;
                    try {
                        pairArr[0] = kotlin.TuplesKt.to(str17, str16);
                        obj5 = obj;
                        str10 = str4;
                    } catch (java.lang.Exception e) {
                        c000112 = c000117;
                        z = isCasting2;
                        function15 = function14;
                        str7 = templateUrl;
                        str8 = str16;
                        html = str17;
                        obj4 = obj;
                        str9 = str4;
                        masterUrl = str7;
                        variantPath = html5;
                        templateMatch2 = templateMatch;
                        templateUrl2 = templateUrl;
                        isCasting3 = z;
                        function16 = function15;
                        baseDomain = data2;
                        function17 = function13;
                        masterUrl2 = masterUrl;
                        masterContent = str5;
                        links = new java.util.ArrayList();
                        str11 = masterContent;
                        if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                        }
                        java.lang.Object obj11 = obj2;
                        $result2 = obj4;
                        str12 = str8;
                        str13 = html;
                        masterUrl3 = str9;
                        c = 1;
                        boyfriendTV2 = this;
                        masterUrl4 = masterUrl2;
                        isCasting5 = isCasting3;
                        templateMatch3 = templateMatch2;
                        $result3 = $result;
                        obj7 = obj11;
                        links2 = links;
                        templateUrl3 = templateUrl2;
                        c000113 = c000112;
                        templateUrl4 = masterContent;
                        html2 = variantPath;
                        function19 = function16;
                        if (links2.isEmpty()) {
                        }
                    }
                    try {
                        pairArr[1] = kotlin.TuplesKt.to(obj5, str10);
                        mapMapOf = kotlin.collections.MapsKt.mapOf(pairArr);
                        c000117.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data2);
                        c000117.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                        c000117.L$2 = function14;
                        c000117.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(html5);
                        c000117.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateMatch);
                        c000117.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateUrl);
                        c000117.L$6 = templateUrl;
                        c000117.Z$0 = isCasting2;
                        c000117.label = 2;
                        isCasting4 = isCasting2;
                        function18 = function14;
                        str9 = str10;
                        obj4 = obj5;
                        str8 = str16;
                        html = str17;
                        c000112 = c000117;
                    } catch (java.lang.Exception e2) {
                        c000112 = c000117;
                        z = isCasting2;
                        function15 = function14;
                        str7 = templateUrl;
                        str8 = str16;
                        html = str17;
                        obj4 = obj5;
                        str9 = str10;
                        masterUrl = str7;
                        variantPath = html5;
                        templateMatch2 = templateMatch;
                        templateUrl2 = templateUrl;
                        isCasting3 = z;
                        function16 = function15;
                        baseDomain = data2;
                        function17 = function13;
                        masterUrl2 = masterUrl;
                        masterContent = str5;
                        links = new java.util.ArrayList();
                        str11 = masterContent;
                        if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                        }
                        java.lang.Object obj112 = obj2;
                        $result2 = obj4;
                        str12 = str8;
                        str13 = html;
                        masterUrl3 = str9;
                        c = 1;
                        boyfriendTV2 = this;
                        masterUrl4 = masterUrl2;
                        isCasting5 = isCasting3;
                        templateMatch3 = templateMatch2;
                        $result3 = $result;
                        obj7 = obj112;
                        links2 = links;
                        templateUrl3 = templateUrl2;
                        c000113 = c000112;
                        templateUrl4 = masterContent;
                        html2 = variantPath;
                        function19 = function16;
                        if (links2.isEmpty()) {
                        }
                    }
                } catch (java.lang.Exception e3) {
                    c000112 = c000117;
                    z = isCasting2;
                    function15 = function14;
                    str7 = templateUrl;
                    obj4 = obj;
                    str8 = str2;
                    html = str3;
                }
                try {
                    obj6 = com.lagradost.nicehttp.Requests.get$default(app, templateUrl, mapMapOf, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000112, 4092, (java.lang.Object) null);
                    break;
                } catch (java.lang.Exception e4) {
                    masterUrl = templateUrl;
                    variantPath = html5;
                    templateMatch2 = templateMatch;
                    templateUrl2 = templateUrl;
                    isCasting3 = isCasting4;
                    function16 = function18;
                    baseDomain = data2;
                    function17 = function13;
                    masterUrl2 = masterUrl;
                    masterContent = str5;
                    links = new java.util.ArrayList();
                    str11 = masterContent;
                    if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                    }
                    java.lang.Object obj1122 = obj2;
                    $result2 = obj4;
                    str12 = str8;
                    str13 = html;
                    masterUrl3 = str9;
                    c = 1;
                    boyfriendTV2 = this;
                    masterUrl4 = masterUrl2;
                    isCasting5 = isCasting3;
                    templateMatch3 = templateMatch2;
                    $result3 = $result;
                    obj7 = obj1122;
                    links2 = links;
                    templateUrl3 = templateUrl2;
                    c000113 = c000112;
                    templateUrl4 = masterContent;
                    html2 = variantPath;
                    function19 = function16;
                    if (links2.isEmpty()) {
                    }
                }
                if (obj6 == obj2) {
                    return obj2;
                }
                masterUrl = templateUrl;
                variantPath = html5;
                templateMatch2 = templateMatch;
                templateUrl2 = templateUrl;
                isCasting3 = isCasting4;
                function16 = function18;
                $result6 = obj6;
                baseDomain = data2;
                function17 = function13;
                try {
                    java.lang.String str18 = masterUrl;
                    masterContent = ((com.lagradost.nicehttp.NiceResponse) $result6).getText();
                    masterUrl2 = str18;
                } catch (java.lang.Exception e5) {
                    masterUrl2 = masterUrl;
                    masterContent = str5;
                }
                links = new java.util.ArrayList();
                str11 = masterContent;
                if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                    str14 = str;
                    isCasting6 = false;
                    i = 2;
                    if (kotlin.text.StringsKt.contains$default(masterContent, str14, false, 2, str5)) {
                        baseDomain2 = kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringBefore$default(masterUrl2, "/key=", str5, 2, str5), "/media=", str5, 2, str5);
                        lines = kotlin.text.StringsKt.lines(masterContent);
                        boyfriendTV2 = this;
                        obj8 = obj2;
                        isCasting7 = isCasting3;
                        currentResolution = null;
                        it = lines.iterator();
                        c000114 = c000112;
                        $result4 = $result;
                        masterUrl5 = masterUrl2;
                        continuation2 = continuation;
                        while (it.hasNext()) {
                            java.lang.String line3 = (java.lang.String) it.next();
                            java.lang.String masterContent2 = masterContent;
                            if (kotlin.text.StringsKt.startsWith$default(line3, str14, isCasting6, i, (java.lang.Object) null)) {
                                java.lang.String str19 = str14;
                                java.lang.String templateUrl5 = templateUrl2;
                                kotlin.text.MatchResult resMatch = kotlin.text.Regex.find$default(new kotlin.text.Regex("RESOLUTION=\\d+x(\\d+)"), line3, 0, i, (java.lang.Object) null);
                                if (resMatch != null && (groupValues2 = resMatch.getGroupValues()) != null) {
                                    java.lang.String str20 = (java.lang.String) groupValues2.get(1);
                                    java.lang.Integer intOrNull = str20 != null ? kotlin.text.StringsKt.toIntOrNull(str20) : null;
                                    currentResolution = intOrNull;
                                    masterContent = masterContent2;
                                    templateUrl2 = templateUrl5;
                                    str14 = str19;
                                    isCasting6 = false;
                                }
                                currentResolution = intOrNull;
                                masterContent = masterContent2;
                                templateUrl2 = templateUrl5;
                                str14 = str19;
                                isCasting6 = false;
                            } else {
                                str15 = str14;
                                java.lang.String templateUrl6 = templateUrl2;
                                if (kotlin.text.StringsKt.startsWith$default(line3, "#", false, i, (java.lang.Object) null) || kotlin.text.StringsKt.isBlank(line3)) {
                                    continuation3 = continuation2;
                                    masterUrl7 = masterUrl5;
                                    c000115 = c000114;
                                    obj9 = obj4;
                                    line = str8;
                                    variantPath2 = html;
                                    masterUrl8 = str9;
                                    obj10 = obj8;
                                    isCasting8 = isCasting7;
                                    currentResolution2 = currentResolution;
                                    it2 = it;
                                } else {
                                    java.lang.String variantPath4 = kotlin.text.StringsKt.trim(line3).toString();
                                    c2 = 1;
                                    if (kotlin.text.StringsKt.startsWith$default(variantPath4, "http", false, i, (java.lang.Object) null)) {
                                        fullVariantUrl = variantPath4;
                                    } else if (kotlin.text.StringsKt.startsWith$default(variantPath4, "/", false, i, (java.lang.Object) null)) {
                                        fullVariantUrl = baseDomain2 + variantPath4;
                                    } else {
                                        java.lang.String basePath = kotlin.text.StringsKt.substringBeforeLast$default(masterUrl5, "/", (java.lang.String) null, i, (java.lang.Object) null);
                                        fullVariantUrl = basePath + '/' + variantPath4;
                                    }
                                    currentResolution2 = currentResolution;
                                    quality = currentResolution2 != null ? currentResolution2.intValue() : -1;
                                    continuation3 = continuation2;
                                    c3 = 2;
                                    if (!kotlin.collections.CollectionsKt.listOf(new java.lang.Integer[]{kotlin.coroutines.jvm.internal.Boxing.boxInt(1080), kotlin.coroutines.jvm.internal.Boxing.boxInt(720), kotlin.coroutines.jvm.internal.Boxing.boxInt(480), kotlin.coroutines.jvm.internal.Boxing.boxInt(240)}).contains(kotlin.coroutines.jvm.internal.Boxing.boxInt(quality)) && quality != -1) {
                                        it2 = it;
                                        masterUrl7 = masterUrl5;
                                        c000115 = c000114;
                                        obj9 = obj4;
                                        line = str8;
                                        variantPath2 = html;
                                        masterUrl8 = str9;
                                        obj10 = obj8;
                                        isCasting8 = isCasting7;
                                    }
                                    java.lang.String name = boyfriendTV2.getName();
                                    java.lang.String str21 = "BoyfriendTV " + (quality > 0 ? new java.lang.StringBuilder().append(quality).append('p').toString() : "Auto");
                                    c000114.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(baseDomain);
                                    c000114.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function17);
                                    c000114.L$2 = function16;
                                    c000114.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(variantPath);
                                    c000114.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateMatch2);
                                    c000114.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateUrl6);
                                    c000114.L$6 = masterUrl5;
                                    c000114.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(masterContent2);
                                    c000114.L$8 = links;
                                    c000114.L$9 = baseDomain2;
                                    c000114.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(lines);
                                    c000114.L$11 = currentResolution2;
                                    it3 = it;
                                    c000114.L$12 = it3;
                                    c000114.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(line3);
                                    c000114.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(variantPath4);
                                    c000114.L$15 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fullVariantUrl);
                                    boolean isCasting9 = isCasting7;
                                    c000114.Z$0 = isCasting9;
                                    c000114.I$0 = quality;
                                    c000114.label = 3;
                                    com.BoyfriendTV.BoyfriendTV.C00011 c000118 = c000114;
                                    java.lang.Object objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name, str21, fullVariantUrl, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, (kotlin.jvm.functions.Function2) null, c000118, 24, (java.lang.Object) null);
                                    java.lang.Object obj12 = obj8;
                                    if (objNewExtractorLink$default == obj12) {
                                        return obj12;
                                    }
                                    variantPath3 = variantPath;
                                    masterUrl9 = masterUrl5;
                                    currentResolution = currentResolution2;
                                    isCasting7 = isCasting9;
                                    obj8 = obj12;
                                    function111 = function16;
                                    data3 = baseDomain;
                                    masterContent = masterContent2;
                                    continuation4 = continuation3;
                                    data4 = baseDomain2;
                                    $result6 = objNewExtractorLink$default;
                                    c000116 = c000118;
                                    line2 = templateUrl6;
                                    com.lagradost.cloudstream3.utils.ExtractorLink link = (com.lagradost.cloudstream3.utils.ExtractorLink) $result6;
                                    link.setQuality(quality);
                                    kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation5 = continuation4;
                                    java.lang.String str22 = str9;
                                    link.setReferer(str22);
                                    java.util.Iterator it4 = it3;
                                    kotlin.Pair[] pairArr2 = new kotlin.Pair[3];
                                    pairArr2[0] = kotlin.TuplesKt.to(html, str8);
                                    pairArr2[c2] = kotlin.TuplesKt.to("Origin", "https://www.boyfriendtv.com");
                                    pairArr2[c3] = kotlin.TuplesKt.to(obj4, str22);
                                    link.setHeaders(kotlin.collections.MapsKt.mapOf(pairArr2));
                                    links.add(link);
                                    continuation2 = continuation5;
                                    templateUrl2 = line2;
                                    it = it4;
                                    variantPath = variantPath3;
                                    function16 = function111;
                                    baseDomain2 = data4;
                                    masterUrl5 = masterUrl9;
                                    str14 = str15;
                                    isCasting6 = false;
                                    c000114 = c000116;
                                    baseDomain = data3;
                                    i = 2;
                                    while (it.hasNext()) {
                                    }
                                }
                                templateUrl2 = templateUrl6;
                                it = it2;
                                str9 = masterUrl8;
                                str8 = line;
                                html = variantPath2;
                                obj4 = obj9;
                                currentResolution = currentResolution2;
                                isCasting7 = isCasting8;
                                obj8 = obj10;
                                c000114 = c000115;
                                masterUrl5 = masterUrl7;
                                str14 = str15;
                                isCasting6 = false;
                                i = 2;
                                masterContent = masterContent2;
                                continuation2 = continuation3;
                            }
                        }
                        java.lang.String masterUrl10 = masterUrl5;
                        com.BoyfriendTV.BoyfriendTV.C00011 c000119 = c000114;
                        java.lang.String templateUrl7 = templateUrl2;
                        str12 = str8;
                        str13 = html;
                        masterUrl3 = str9;
                        obj7 = obj8;
                        isCasting5 = isCasting7;
                        c = 1;
                        templateUrl4 = masterContent;
                        templateMatch3 = templateMatch2;
                        $result3 = $result4;
                        masterUrl4 = masterUrl10;
                        templateUrl3 = templateUrl7;
                        $result2 = obj4;
                        links2 = links;
                        c000113 = c000119;
                        html2 = variantPath;
                        function19 = function16;
                        if (links2.isEmpty()) {
                            java.lang.Iterable $this$forEach$iv = links2;
                            while (r5.hasNext()) {
                            }
                            java.lang.Iterable $this$forEach$iv2 = links2;
                            return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(!((java.util.Collection) $this$forEach$iv2).isEmpty());
                        }
                        java.lang.String name2 = boyfriendTV2.getName();
                        c000113.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(baseDomain);
                        c000113.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function17);
                        c000113.L$2 = function19;
                        c000113.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(html2);
                        c000113.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateMatch3);
                        c000113.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateUrl3);
                        c000113.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(masterUrl4);
                        c000113.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(templateUrl4);
                        c000113.L$8 = links2;
                        c000113.L$9 = null;
                        c000113.L$10 = null;
                        c000113.L$11 = null;
                        c000113.L$12 = null;
                        c000113.L$13 = null;
                        c000113.L$14 = null;
                        c000113.L$15 = null;
                        c000113.Z$0 = isCasting5;
                        c000113.label = 4;
                        java.lang.Object objNewExtractorLink$default2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name2, "BoyfriendTV", masterUrl4, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, (kotlin.jvm.functions.Function2) null, c000113, 24, (java.lang.Object) null);
                        if (objNewExtractorLink$default2 == obj7) {
                            return obj7;
                        }
                        html3 = html2;
                        templateMatch4 = templateMatch3;
                        html4 = templateUrl3;
                        masterUrl6 = templateUrl4;
                        function110 = function19;
                        links3 = links2;
                        $result5 = $result3;
                        $result6 = objNewExtractorLink$default2;
                        com.lagradost.cloudstream3.utils.ExtractorLink fallbackLink = (com.lagradost.cloudstream3.utils.ExtractorLink) $result6;
                        fallbackLink.setQuality(-1);
                        fallbackLink.setReferer(masterUrl3);
                        kotlin.Pair[] pairArr3 = new kotlin.Pair[2];
                        pairArr3[0] = kotlin.TuplesKt.to(str13, str12);
                        pairArr3[c] = kotlin.TuplesKt.to($result2, masterUrl3);
                        fallbackLink.setHeaders(kotlin.collections.MapsKt.mapOf(pairArr3));
                        links3.add(fallbackLink);
                        links2 = links3;
                        function19 = function110;
                        java.lang.Iterable $this$forEach$iv3 = links2;
                        for (java.lang.Object element$iv : $this$forEach$iv3) {
                            com.lagradost.cloudstream3.utils.ExtractorLink it5 = (com.lagradost.cloudstream3.utils.ExtractorLink) element$iv;
                            function19.invoke(it5);
                        }
                        java.lang.Iterable $this$forEach$iv22 = links2;
                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(!((java.util.Collection) $this$forEach$iv22).isEmpty());
                    }
                }
                java.lang.Object obj11222 = obj2;
                $result2 = obj4;
                str12 = str8;
                str13 = html;
                masterUrl3 = str9;
                c = 1;
                boyfriendTV2 = this;
                masterUrl4 = masterUrl2;
                isCasting5 = isCasting3;
                templateMatch3 = templateMatch2;
                $result3 = $result;
                obj7 = obj11222;
                links2 = links;
                templateUrl3 = templateUrl2;
                c000113 = c000112;
                templateUrl4 = masterContent;
                html2 = variantPath;
                function19 = function16;
                if (links2.isEmpty()) {
                }
                break;
            case 1:
                boolean isCasting10 = c000117.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) c000117.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function113 = (kotlin.jvm.functions.Function1) c000117.L$1;
                java.lang.String data5 = (java.lang.String) c000117.L$0;
                kotlin.ResultKt.throwOnFailure($result6);
                $result = $result6;
                obj2 = coroutine_suspended;
                function14 = function112;
                function13 = function113;
                data2 = data5;
                obj = "Referer";
                str2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                str3 = "User-Agent";
                str4 = "https://www.boyfriendtv.com/";
                str = "#EXT-X-STREAM-INF";
                str5 = null;
                isCasting2 = isCasting10;
                obj3 = $result;
                java.lang.String html52 = ((com.lagradost.nicehttp.NiceResponse) obj3).getText();
                templateMatch = kotlin.text.Regex.find$default(new kotlin.text.Regex("\"hlsAuto\"\\s*:\\s*\"([^\"]+)\""), html52, 0, 2, str5);
                if (templateMatch != null) {
                }
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
            case 2:
                isCasting3 = c000117.Z$0;
                masterUrl = (java.lang.String) c000117.L$6;
                templateUrl2 = (java.lang.String) c000117.L$5;
                templateMatch2 = (kotlin.text.MatchResult) c000117.L$4;
                variantPath = (java.lang.String) c000117.L$3;
                function16 = (kotlin.jvm.functions.Function1) c000117.L$2;
                function17 = (kotlin.jvm.functions.Function1) c000117.L$1;
                baseDomain = (java.lang.String) c000117.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result6);
                    $result = $result6;
                    obj2 = coroutine_suspended;
                    obj4 = "Referer";
                    str8 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                    html = "User-Agent";
                    str9 = "https://www.boyfriendtv.com/";
                    str = "#EXT-X-STREAM-INF";
                    str5 = null;
                    c000112 = c000117;
                    java.lang.String str182 = masterUrl;
                    masterContent = ((com.lagradost.nicehttp.NiceResponse) $result6).getText();
                    masterUrl2 = str182;
                } catch (java.lang.Exception e6) {
                    $result = $result6;
                    obj2 = coroutine_suspended;
                    obj4 = "Referer";
                    str8 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                    html = "User-Agent";
                    str9 = "https://www.boyfriendtv.com/";
                    str = "#EXT-X-STREAM-INF";
                    str5 = null;
                    c000112 = c000117;
                    masterUrl2 = masterUrl;
                    masterContent = str5;
                    links = new java.util.ArrayList();
                    str11 = masterContent;
                    if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                    }
                    java.lang.Object obj112222 = obj2;
                    $result2 = obj4;
                    str12 = str8;
                    str13 = html;
                    masterUrl3 = str9;
                    c = 1;
                    boyfriendTV2 = this;
                    masterUrl4 = masterUrl2;
                    isCasting5 = isCasting3;
                    templateMatch3 = templateMatch2;
                    $result3 = $result;
                    obj7 = obj112222;
                    links2 = links;
                    templateUrl3 = templateUrl2;
                    c000113 = c000112;
                    templateUrl4 = masterContent;
                    html2 = variantPath;
                    function19 = function16;
                    if (links2.isEmpty()) {
                    }
                }
                links = new java.util.ArrayList();
                str11 = masterContent;
                if (str11 != null) {
                }
                if (!(str11 != null || kotlin.text.StringsKt.isBlank(str11))) {
                }
                java.lang.Object obj1122222 = obj2;
                $result2 = obj4;
                str12 = str8;
                str13 = html;
                masterUrl3 = str9;
                c = 1;
                boyfriendTV2 = this;
                masterUrl4 = masterUrl2;
                isCasting5 = isCasting3;
                templateMatch3 = templateMatch2;
                $result3 = $result;
                obj7 = obj1122222;
                links2 = links;
                templateUrl3 = templateUrl2;
                c000113 = c000112;
                templateUrl4 = masterContent;
                html2 = variantPath;
                function19 = function16;
                if (links2.isEmpty()) {
                }
                break;
            case 3:
                int quality2 = c000117.I$0;
                boolean isCasting11 = c000117.Z$0;
                java.util.Iterator it6 = (java.util.Iterator) c000117.L$12;
                java.lang.Integer currentResolution3 = (java.lang.Integer) c000117.L$11;
                java.util.List lines2 = (java.util.List) c000117.L$10;
                data4 = (java.lang.String) c000117.L$9;
                java.util.List links4 = (java.util.List) c000117.L$8;
                java.lang.String masterContent3 = (java.lang.String) c000117.L$7;
                masterUrl9 = (java.lang.String) c000117.L$6;
                java.lang.String templateUrl8 = (java.lang.String) c000117.L$5;
                kotlin.text.MatchResult templateMatch5 = (kotlin.text.MatchResult) c000117.L$4;
                java.lang.String html6 = (java.lang.String) c000117.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function114 = (kotlin.jvm.functions.Function1) c000117.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function115 = (kotlin.jvm.functions.Function1) c000117.L$1;
                java.lang.String data6 = (java.lang.String) c000117.L$0;
                kotlin.ResultKt.throwOnFailure($result6);
                obj8 = coroutine_suspended;
                isCasting7 = isCasting11;
                currentResolution = currentResolution3;
                obj4 = "Referer";
                str8 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                html = "User-Agent";
                str9 = "https://www.boyfriendtv.com/";
                str15 = "#EXT-X-STREAM-INF";
                quality = quality2;
                templateMatch2 = templateMatch5;
                variantPath3 = html6;
                c2 = 1;
                c3 = 2;
                lines = lines2;
                function17 = function115;
                function111 = function114;
                data3 = data6;
                c000116 = c000117;
                $result4 = $result6;
                it3 = it6;
                links = links4;
                masterContent = masterContent3;
                boyfriendTV2 = boyfriendTV;
                line2 = templateUrl8;
                com.lagradost.cloudstream3.utils.ExtractorLink link2 = (com.lagradost.cloudstream3.utils.ExtractorLink) $result6;
                link2.setQuality(quality);
                kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation52 = continuation4;
                java.lang.String str222 = str9;
                link2.setReferer(str222);
                java.util.Iterator it42 = it3;
                kotlin.Pair[] pairArr22 = new kotlin.Pair[3];
                pairArr22[0] = kotlin.TuplesKt.to(html, str8);
                pairArr22[c2] = kotlin.TuplesKt.to("Origin", "https://www.boyfriendtv.com");
                pairArr22[c3] = kotlin.TuplesKt.to(obj4, str222);
                link2.setHeaders(kotlin.collections.MapsKt.mapOf(pairArr22));
                links.add(link2);
                continuation2 = continuation52;
                templateUrl2 = line2;
                it = it42;
                variantPath = variantPath3;
                function16 = function111;
                baseDomain2 = data4;
                masterUrl5 = masterUrl9;
                str14 = str15;
                isCasting6 = false;
                c000114 = c000116;
                baseDomain = data3;
                i = 2;
                while (it.hasNext()) {
                }
                java.lang.String masterUrl102 = masterUrl5;
                com.BoyfriendTV.BoyfriendTV.C00011 c0001192 = c000114;
                java.lang.String templateUrl72 = templateUrl2;
                str12 = str8;
                str13 = html;
                masterUrl3 = str9;
                obj7 = obj8;
                isCasting5 = isCasting7;
                c = 1;
                templateUrl4 = masterContent;
                templateMatch3 = templateMatch2;
                $result3 = $result4;
                masterUrl4 = masterUrl102;
                templateUrl3 = templateUrl72;
                $result2 = obj4;
                links2 = links;
                c000113 = c0001192;
                html2 = variantPath;
                function19 = function16;
                if (links2.isEmpty()) {
                }
                break;
            case 4:
                boolean z2 = c000117.Z$0;
                java.util.List links5 = (java.util.List) c000117.L$8;
                java.lang.String masterContent4 = (java.lang.String) c000117.L$7;
                java.lang.String templateUrl9 = (java.lang.String) c000117.L$5;
                templateMatch4 = (kotlin.text.MatchResult) c000117.L$4;
                html3 = (java.lang.String) c000117.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function116 = (kotlin.jvm.functions.Function1) c000117.L$2;
                kotlin.ResultKt.throwOnFailure($result6);
                str12 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36";
                masterUrl3 = "https://www.boyfriendtv.com/";
                c = 1;
                $result2 = "Referer";
                masterUrl6 = masterContent4;
                html4 = templateUrl9;
                links3 = links5;
                function110 = function116;
                str13 = "User-Agent";
                $result5 = $result6;
                com.lagradost.cloudstream3.utils.ExtractorLink fallbackLink2 = (com.lagradost.cloudstream3.utils.ExtractorLink) $result6;
                fallbackLink2.setQuality(-1);
                fallbackLink2.setReferer(masterUrl3);
                kotlin.Pair[] pairArr32 = new kotlin.Pair[2];
                pairArr32[0] = kotlin.TuplesKt.to(str13, str12);
                pairArr32[c] = kotlin.TuplesKt.to($result2, masterUrl3);
                fallbackLink2.setHeaders(kotlin.collections.MapsKt.mapOf(pairArr32));
                links3.add(fallbackLink2);
                links2 = links3;
                function19 = function110;
                java.lang.Iterable $this$forEach$iv32 = links2;
                while (r5.hasNext()) {
                }
                java.lang.Iterable $this$forEach$iv222 = links2;
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(!((java.util.Collection) $this$forEach$iv222).isEmpty());
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
