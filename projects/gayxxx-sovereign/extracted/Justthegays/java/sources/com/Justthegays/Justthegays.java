package com.Justthegays;

/* JADX INFO: compiled from: Justthegays.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000z\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u001e\u0010\u001f\u001a\u00020!2\u0006\u0010\"\u001a\u00020#2\u0006\u0010$\u001a\u00020%H\u0096@¢\u0006\u0002\u0010&J\u000e\u0010'\u001a\u0004\u0018\u00010(*\u00020)H\u0002J\u000e\u0010*\u001a\u0004\u0018\u00010(*\u00020)H\u0002J\u001c\u0010+\u001a\b\u0012\u0004\u0012\u00020(0\u001d2\u0006\u0010,\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010-J\u0016\u0010.\u001a\u00020/2\u0006\u00100\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010-JF\u00101\u001a\u00020\u000e2\u0006\u00102\u001a\u00020\u00052\u0006\u00103\u001a\u00020\u000e2\u0012\u00104\u001a\u000e\u0012\u0004\u0012\u000206\u0012\u0004\u0012\u000207052\u0012\u00108\u001a\u000e\u0012\u0004\u0012\u000209\u0012\u0004\u0012\u00020705H\u0096@¢\u0006\u0002\u0010:R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u0014\u0010\u0011\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0012\u0010\u0010R\u0014\u0010\u0013\u001a\u00020\u0014X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0016R\u001a\u0010\u0017\u001a\b\u0012\u0004\u0012\u00020\u00190\u0018X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001a\u0010\u001bR\u001a\u0010\u001c\u001a\b\u0012\u0004\u0012\u00020\u001e0\u001dX\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u001f\u0010 ¨\u0006;"}, d2 = {"Lcom/Justthegays/Justthegays;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "hasDownloadSupport", "getHasDownloadSupport", "vpnStatus", "Lcom/lagradost/cloudstream3/VPNStatus;", "getVpnStatus", "()Lcom/lagradost/cloudstream3/VPNStatus;", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "mainPage", "", "Lcom/lagradost/cloudstream3/MainPageData;", "getMainPage", "()Ljava/util/List;", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "toSearchResult", "Lcom/lagradost/cloudstream3/SearchResponse;", "Lorg/jsoup/nodes/Element;", "toRecommendResult", "search", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Justthegays"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nJustthegays.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Justthegays.kt\ncom/Justthegays/Justthegays\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 4 _Sequences.kt\nkotlin/sequences/SequencesKt___SequencesKt\n*L\n1#1,189:1\n1642#2,10:190\n1915#2:200\n1916#2:202\n1652#2:203\n1642#2,10:204\n1915#2:214\n1916#2:216\n1652#2:217\n1642#2,10:218\n1915#2:228\n1916#2:230\n1652#2:231\n1915#2:232\n1916#2:235\n1915#2:236\n1916#2:238\n1642#2,10:239\n1915#2:249\n1916#2:251\n1652#2:252\n1915#2:253\n1915#2,2:256\n1916#2:258\n1586#2:261\n1661#2,3:262\n777#2:265\n873#2,2:266\n1924#2,3:268\n1#3:201\n1#3:215\n1#3:229\n1#3:237\n1#3:250\n1342#4,2:233\n1342#4,2:254\n1342#4,2:259\n*S KotlinDebug\n*F\n+ 1 Justthegays.kt\ncom/Justthegays/Justthegays\n*L\n57#1:190,10\n57#1:200\n57#1:202\n57#1:203\n93#1:204,10\n93#1:214\n93#1:216\n93#1:217\n106#1:218,10\n106#1:228\n106#1:230\n106#1:231\n129#1:232\n129#1:235\n134#1:236\n134#1:238\n140#1:239,10\n140#1:249\n140#1:251\n140#1:252\n140#1:253\n144#1:256,2\n140#1:258\n157#1:261\n157#1:262,3\n158#1:265\n158#1:266,2\n167#1:268,3\n57#1:201\n93#1:215\n106#1:229\n140#1:250\n130#1:233,2\n143#1:254,2\n154#1:259,2\n*E\n"})
public final class Justthegays extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://justthegays.com";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Justthegays";
    private final boolean hasMainPage = true;
    private final boolean hasDownloadSupport = true;

    @org.jetbrains.annotations.NotNull
    private final com.lagradost.cloudstream3.VPNStatus vpnStatus = com.lagradost.cloudstream3.VPNStatus.MightBeNeeded;

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.lagradost.cloudstream3.MainPageData> mainPage = com.lagradost.cloudstream3.MainAPIKt.mainPageOf(new kotlin.Pair[]{kotlin.TuplesKt.to(java.lang.String.valueOf(getMainUrl()), "Latest"), kotlin.TuplesKt.to(getMainUrl() + "/random/", "Random"), kotlin.TuplesKt.to(getMainUrl() + "/popular/", "Popular"), kotlin.TuplesKt.to(getMainUrl() + "/trending/", "Trending"), kotlin.TuplesKt.to(getMainUrl() + "/categories/young-twink/", "Young/Twinks"), kotlin.TuplesKt.to(getMainUrl() + "/categories/asian-052615/", "Asian"), kotlin.TuplesKt.to(getMainUrl() + "/categories/double-penetration-052615/", "Double Penetration"), kotlin.TuplesKt.to(getMainUrl() + "/categories/feet-052615/", "Feet"), kotlin.TuplesKt.to(getMainUrl() + "/categories/fisting-052615/", "Fisting"), kotlin.TuplesKt.to(getMainUrl() + "/categories/anal-052615/", "Fucking"), kotlin.TuplesKt.to(getMainUrl() + "/categories/group-052615/", "Group"), kotlin.TuplesKt.to(getMainUrl() + "/categories/jerk-off-052615/", "Jerk Off"), kotlin.TuplesKt.to(getMainUrl() + "/categories/latin-052615/", "Latin"), kotlin.TuplesKt.to(getMainUrl() + "/categories/massage-052615/", "Massage"), kotlin.TuplesKt.to(getMainUrl() + "/categories/oral-052615/", "Oral"), kotlin.TuplesKt.to(getMainUrl() + "/categories/public-052615/", "Public"), kotlin.TuplesKt.to(getMainUrl() + "/categories/young-twink-052615/", "Worship")});

    /* JADX INFO: renamed from: com.Justthegays.Justthegays$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: Justthegays.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Justthegays.Justthegays", f = "Justthegays.kt", i = {0, 0, 0, 0}, l = {52}, m = "getMainPage", n = {"request", "url", "ua", "page"}, nl = {55}, s = {"L$0", "L$1", "L$2", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Justthegays.Justthegays.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Justthegays.Justthegays.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Justthegays.Justthegays$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Justthegays.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Justthegays.Justthegays", f = "Justthegays.kt", i = {0, 0, 1, 1, 1, 1, 1, 1, 1}, l = {98, 108}, m = "load", n = {"url", "ua", "url", "ua", "doc", "title", "poster", "description", "recommendations"}, nl = {100, -1}, s = {"L$0", "L$1", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6"}, v = 2)
    static final class C00001 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super com.Justthegays.Justthegays.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Justthegays.Justthegays.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Justthegays.Justthegays$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Justthegays.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Justthegays.Justthegays", f = "Justthegays.kt", i = {0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {122, 142, 174}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "headers", "isCasting", "data", "subtitleCallback", "callback", "headers", "res", "doc", "urlRegex", "found", "$this$forEach$iv", "element$iv", "iframeUrl", "isCasting", "$i$f$forEach", "$i$a$-forEach-Justthegays$loadLinks$5", "data", "subtitleCallback", "callback", "headers", "res", "doc", "urlRegex", "found", "candidates", "$this$forEachIndexed$iv", "item$iv", "url", "friendlyName", "isCasting", "$i$f$forEachIndexed", "index$iv", "i", "$i$a$-forEachIndexed-Justthegays$loadLinks$7"}, nl = {123, 143, 173}, s = {"L$0", "L$1", "L$2", "L$3", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$10", "L$11", "Z$0", "I$0", "I$1", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$11", "L$12", "L$13", "Z$0", "I$0", "I$1", "I$2", "I$3"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        int I$2;
        int I$3;
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
        boolean Z$0;
        int label;
        /* synthetic */ java.lang.Object result;

        C00011(kotlin.coroutines.Continuation<? super com.Justthegays.Justthegays.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Justthegays.Justthegays.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Justthegays.Justthegays$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Justthegays.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Justthegays.Justthegays", f = "Justthegays.kt", i = {0, 0}, l = {88}, m = "search", n = {"query", "searchUrl"}, nl = {91}, s = {"L$0", "L$1"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super com.Justthegays.Justthegays.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Justthegays.Justthegays.this.search(null, (kotlin.coroutines.Continuation) this);
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
        com.Justthegays.Justthegays.AnonymousClass1 anonymousClass1;
        com.lagradost.cloudstream3.MainPageRequest request2;
        if (continuation instanceof com.Justthegays.Justthegays.AnonymousClass1) {
            anonymousClass1 = (com.Justthegays.Justthegays.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Justthegays.Justthegays.AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String url = page > 1 ? request.getData() + "page-5263/" + page + '/' : request.getData();
                java.util.Map ua = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"), kotlin.TuplesKt.to("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")});
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.lang.String str = getMainUrl() + '/';
                anonymousClass1.L$0 = request;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua);
                anonymousClass1.I$0 = page;
                anonymousClass1.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, ua, str, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass1, 4088, (java.lang.Object) null);
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
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.col-xl-4");
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
        java.lang.String string;
        java.lang.String strText;
        org.jsoup.nodes.Element aTag = $this$toSearchResult.selectFirst("div.item-img a");
        if (aTag == null) {
            return null;
        }
        java.lang.String href = aTag.attr("href");
        org.jsoup.nodes.Element imgElement = $this$toSearchResult.selectFirst("div.item-img img");
        final java.lang.String posterUrl = imgElement != null ? imgElement.attr("src") : null;
        org.jsoup.nodes.Element titleElement = $this$toSearchResult.selectFirst("h3.post-title a");
        if (titleElement == null || (strText = titleElement.text()) == null || (string = kotlin.text.StringsKt.trim(strText).toString()) == null) {
            string = "No Title";
        }
        java.lang.String title = string;
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, href), com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: com.Justthegays.Justthegays$$ExternalSyntheticLambda0
            public final java.lang.Object invoke(java.lang.Object obj) {
                return com.Justthegays.Justthegays.toSearchResult$lambda$0(this.f$0, posterUrl, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit toSearchResult$lambda$0(com.Justthegays.Justthegays this$0, java.lang.String $posterUrl, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl(com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this$0, $posterUrl));
        return kotlin.Unit.INSTANCE;
    }

    private final com.lagradost.cloudstream3.SearchResponse toRecommendResult(org.jsoup.nodes.Element $this$toRecommendResult) {
        return toSearchResult($this$toRecommendResult);
    }

    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        com.Justthegays.Justthegays.C00021 c00021;
        if (continuation instanceof com.Justthegays.Justthegays.C00021) {
            c00021 = (com.Justthegays.Justthegays.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
            } else {
                c00021 = new com.Justthegays.Justthegays.C00021(continuation);
            }
        }
        java.lang.Object $result = c00021.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00021.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String searchUrl = getMainUrl() + "/?s=" + query;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c00021.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(query);
                c00021.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(searchUrl);
                c00021.label = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, searchUrl, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c00021, 4094, (java.lang.Object) null);
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
        java.lang.Iterable $this$mapNotNull$iv = document.select("div.col-xl-4");
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
        com.Justthegays.Justthegays.C00001 c00001;
        java.lang.Object obj;
        java.lang.Object obj2;
        java.util.Map ua;
        java.lang.String url2;
        java.lang.String title;
        java.lang.String strAttr;
        java.lang.String strAttr2;
        if (continuation instanceof com.Justthegays.Justthegays.C00001) {
            c00001 = (com.Justthegays.Justthegays.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.Justthegays.Justthegays.C00001(continuation);
            }
        }
        com.Justthegays.Justthegays.C00001 c000012 = c00001;
        java.lang.Object it$iv$iv = c000012.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000012.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure(it$iv$iv);
                java.util.Map ua2 = kotlin.collections.MapsKt.mapOf(kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"));
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c000012.L$0 = url;
                c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua2);
                c000012.label = 1;
                obj = coroutine_suspended;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, ua2, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000012, 4092, (java.lang.Object) null);
                c000012 = c000012;
                if (obj2 == obj) {
                    return obj;
                }
                ua = ua2;
                url2 = url;
                break;
                break;
            case 1:
                java.util.Map ua3 = (java.util.Map) c000012.L$1;
                url2 = (java.lang.String) c000012.L$0;
                kotlin.ResultKt.throwOnFailure(it$iv$iv);
                obj = coroutine_suspended;
                ua = ua3;
                obj2 = it$iv$iv;
                break;
            case 2:
                kotlin.ResultKt.throwOnFailure(it$iv$iv);
                return it$iv$iv;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        org.jsoup.nodes.Document doc = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
        org.jsoup.nodes.Element elementSelectFirst = doc.selectFirst("meta[property='og:title']");
        if (elementSelectFirst == null || (title = elementSelectFirst.attr("content")) == null) {
            title = doc.title();
        }
        org.jsoup.nodes.Element elementSelectFirst2 = doc.selectFirst("meta[property='og:image']");
        java.lang.String str = "";
        if (elementSelectFirst2 == null || (strAttr = elementSelectFirst2.attr("content")) == null) {
            strAttr = "";
        }
        java.lang.String poster = strAttr;
        org.jsoup.nodes.Element elementSelectFirst3 = doc.selectFirst("meta[property='og:description']");
        if (elementSelectFirst3 != null && (strAttr2 = elementSelectFirst3.attr("content")) != null) {
            str = strAttr2;
        }
        java.lang.String description = str;
        java.lang.Iterable $this$mapNotNull$iv = doc.select("div.col-xl-4.col-lg-4.col-md-6.col-6.item.responsive-height.post");
        java.util.Collection destination$iv$iv = new java.util.ArrayList();
        for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
            java.lang.Object $result = it$iv$iv;
            org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
            com.lagradost.cloudstream3.SearchResponse recommendResult = toRecommendResult(it);
            if (recommendResult != null) {
                destination$iv$iv.add(recommendResult);
            }
            it$iv$iv = $result;
        }
        java.util.List recommendations = (java.util.List) destination$iv$iv;
        java.lang.String title2 = title;
        com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.NSFW;
        com.Justthegays.Justthegays.AnonymousClass2 anonymousClass2 = new com.Justthegays.Justthegays.AnonymousClass2(poster, description, recommendations, null);
        c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
        c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(ua);
        c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(doc);
        c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title2);
        c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster);
        c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(description);
        c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
        c000012.label = 2;
        java.lang.Object objNewMovieLoadResponse = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title2, url2, tvType, url2, anonymousClass2, c000012);
        return objNewMovieLoadResponse == obj ? obj : objNewMovieLoadResponse;
    }

    /* JADX INFO: renamed from: com.Justthegays.Justthegays$load$2, reason: invalid class name */
    /* JADX INFO: compiled from: Justthegays.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Justthegays.Justthegays$load$2", f = "Justthegays.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $description;
        final /* synthetic */ java.lang.String $poster;
        final /* synthetic */ java.util.List<com.lagradost.cloudstream3.SearchResponse> $recommendations;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, java.lang.String str2, java.util.List<? extends com.lagradost.cloudstream3.SearchResponse> list, kotlin.coroutines.Continuation<? super com.Justthegays.Justthegays.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$poster = str;
            this.$description = str2;
            this.$recommendations = list;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = new com.Justthegays.Justthegays.AnonymousClass2(this.$poster, this.$description, this.$recommendations, continuation);
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

    /* JADX WARN: Can't wrap try/catch for region: R(10:58|(1:141)|59|60|147|61|62|139|63|(1:65)(15:66|149|67|68|143|69|(2:72|70)|151|73|(7:76|(1:78)(1:79)|(1:81)|82|(2:84|154)(2:86|153)|87|74)|152|88|100|56|(11:101|(2:104|102)|155|105|(2:108|106)|156|109|(4:112|(3:157|114|161)(1:160)|159|110)|158|115|(2:117|118)(3:119|120|(6:122|(1:124)|125|(2:128|(1:130)(1:131))(1:127)|132|(1:134)(4:135|136|120|(2:137|138)(0)))(0)))(0))) */
    /* JADX WARN: Can't wrap try/catch for region: R(10:58|141|59|60|147|61|62|139|63|(1:65)(15:66|149|67|68|143|69|(2:72|70)|151|73|(7:76|(1:78)(1:79)|(1:81)|82|(2:84|154)(2:86|153)|87|74)|152|88|100|56|(11:101|(2:104|102)|155|105|(2:108|106)|156|109|(4:112|(3:157|114|161)(1:160)|159|110)|158|115|(2:117|118)(3:119|120|(6:122|(1:124)|125|(2:128|(1:130)(1:131))(1:127)|132|(1:134)(4:135|136|120|(2:137|138)(0)))(0)))(0))) */
    /* JADX WARN: Can't wrap try/catch for region: R(15:66|(1:149)|67|68|143|69|(2:72|70)|151|73|(7:76|(1:78)(1:79)|(1:81)|82|(2:84|154)(2:86|153)|87|74)|152|88|100|56|(11:101|(2:104|102)|155|105|(2:108|106)|156|109|(4:112|(3:157|114|161)(1:160)|159|110)|158|115|(2:117|118)(3:119|120|(6:122|(1:124)|125|(2:128|(1:130)(1:131))(1:127)|132|(1:134)(4:135|136|120|(2:137|138)(0)))(0)))(0)) */
    /* JADX WARN: Code restructure failed: missing block: B:90:0x0419, code lost:
    
        r1 = r53;
        r2 = r54;
        r21 = r10;
        r5 = r22;
        r22 = r11;
     */
    /* JADX WARN: Code restructure failed: missing block: B:94:0x0431, code lost:
    
        r1 = r53;
        r18 = r7;
        r21 = r10;
        r25 = r15;
        r5 = r22;
        r24 = r32;
        r22 = r11;
     */
    /* JADX WARN: Code restructure failed: missing block: B:96:0x0445, code lost:
    
        r44 = r5;
        r1 = r53;
        r18 = r7;
        r21 = r10;
        r25 = r15;
        r5 = r22;
        r24 = r9;
        r22 = r11;
     */
    /* JADX WARN: Removed duplicated region for block: B:101:0x0486  */
    /* JADX WARN: Removed duplicated region for block: B:122:0x0584  */
    /* JADX WARN: Removed duplicated region for block: B:137:0x06a6  */
    /* JADX WARN: Removed duplicated region for block: B:26:0x01e1  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x0247  */
    /* JADX WARN: Removed duplicated region for block: B:48:0x02a6  */
    /* JADX WARN: Removed duplicated region for block: B:58:0x0300  */
    /* JADX WARN: Removed duplicated region for block: B:72:0x0398 A[Catch: Exception -> 0x0418, LOOP:0: B:70:0x0392->B:72:0x0398, LOOP_END, TryCatch #2 {Exception -> 0x0418, blocks: (B:69:0x0389, B:70:0x0392, B:72:0x0398, B:73:0x03ae, B:74:0x03bd, B:76:0x03c3, B:81:0x03e6, B:82:0x03ee, B:84:0x03fc), top: B:143:0x0389 }] */
    /* JADX WARN: Removed duplicated region for block: B:76:0x03c3 A[Catch: Exception -> 0x0418, TryCatch #2 {Exception -> 0x0418, blocks: (B:69:0x0389, B:70:0x0392, B:72:0x0398, B:73:0x03ae, B:74:0x03bd, B:76:0x03c3, B:81:0x03e6, B:82:0x03ee, B:84:0x03fc), top: B:143:0x0389 }] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:135:0x0664 -> B:136:0x0689). Please report as a decompilation issue!!! */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:66:0x036a -> B:149:0x0376). Please report as a decompilation issue!!! */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:99:0x0475 -> B:100:0x047f). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        com.Justthegays.Justthegays.C00011 c00011;
        com.Justthegays.Justthegays justthegays;
        java.lang.Object $result;
        com.Justthegays.Justthegays.C00011 c000112;
        java.lang.Object obj;
        java.lang.String str;
        java.lang.String str2;
        java.lang.String data2;
        boolean isCasting2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.util.Map headers;
        java.lang.String data3;
        java.lang.String iframeUrl;
        java.util.Iterator it;
        java.lang.Iterable $this$forEach$iv;
        org.jsoup.nodes.Document doc;
        kotlin.text.Regex urlRegex;
        java.util.List found;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function16;
        com.Justthegays.Justthegays.C00011 c000113;
        boolean isCasting3;
        com.lagradost.nicehttp.NiceResponse $result2;
        java.lang.String data4;
        int $i$f$forEach;
        java.lang.String str3;
        com.Justthegays.Justthegays.C00011 c000114;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17;
        java.util.Map headers2;
        org.jsoup.nodes.Document doc2;
        kotlin.text.Regex urlRegex2;
        java.util.Iterator it2;
        java.util.List $this$forEachIndexed$iv;
        int $i$f$forEachIndexed;
        java.lang.Object obj2;
        java.util.Iterator it3;
        com.Justthegays.Justthegays.C00011 c000115;
        java.util.List candidates;
        int index$iv;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation2;
        com.Justthegays.Justthegays justthegays2;
        java.util.Map headers3;
        com.Justthegays.Justthegays.C00011 c000116;
        java.util.Iterator it4;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function18;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19;
        com.lagradost.nicehttp.NiceResponse res;
        int index$iv2;
        java.util.Map headers4;
        boolean isCasting4;
        java.lang.Object $result3;
        com.Justthegays.Justthegays justthegays3;
        org.jsoup.nodes.Document doc3;
        kotlin.text.Regex urlRegex3;
        java.lang.Object obj3;
        java.util.List found2;
        java.lang.Iterable $this$forEachIndexed$iv2;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation3 = continuation;
        if (continuation3 instanceof com.Justthegays.Justthegays.C00011) {
            c00011 = (com.Justthegays.Justthegays.C00011) continuation3;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
                justthegays = this;
            } else {
                justthegays = this;
                c00011 = justthegays.new C00011(continuation3);
            }
        }
        com.Justthegays.Justthegays.C00011 c000117 = c00011;
        java.lang.Object $result4 = c000117.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000117.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result4);
                java.util.Map headers5 = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0"), kotlin.TuplesKt.to("Referer", data)});
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c000117.L$0 = data;
                c000117.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                c000117.L$2 = function12;
                c000117.L$3 = headers5;
                c000117.Z$0 = isCasting;
                c000117.label = 1;
                $result = $result4;
                c000112 = c000117;
                obj = coroutine_suspended;
                str = "abs:data-src";
                str2 = "abs:src";
                $result4 = com.lagradost.nicehttp.Requests.get$default(app, data, headers5, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000112, 4092, (java.lang.Object) null);
                if ($result4 == obj) {
                    return obj;
                }
                data2 = data;
                isCasting2 = isCasting;
                function13 = function1;
                function14 = function12;
                headers = headers5;
                com.lagradost.nicehttp.NiceResponse res2 = (com.lagradost.nicehttp.NiceResponse) $result4;
                org.jsoup.nodes.Document doc4 = res2.getDocument();
                kotlin.text.Regex urlRegex4 = new kotlin.text.Regex("https?://[^\\s'\"]+?\\.(?:mp4|m3u8|webm)(\\?[^'\"\\s<>]*)?", kotlin.text.RegexOption.IGNORE_CASE);
                java.util.List found3 = new java.util.ArrayList();
                java.lang.Iterable $this$forEach$iv2 = doc4.select("script[type=application/ld+json]");
                for (java.lang.Object element$iv : $this$forEach$iv2) {
                    org.jsoup.nodes.Element s = (org.jsoup.nodes.Element) element$iv;
                    boolean isCasting5 = isCasting2;
                    java.lang.Object obj4 = obj;
                    com.lagradost.nicehttp.NiceResponse res3 = res2;
                    java.lang.String data5 = data2;
                    kotlin.sequences.Sequence $this$forEach$iv3 = kotlin.text.Regex.findAll$default(urlRegex4, s.data(), 0, 2, (java.lang.Object) null);
                    for (java.lang.Object element$iv2 : $this$forEach$iv3) {
                        kotlin.text.MatchResult m = (kotlin.text.MatchResult) element$iv2;
                        found3.add(m.getValue());
                    }
                    isCasting2 = isCasting5;
                    res2 = res3;
                    data2 = data5;
                    obj = obj4;
                }
                boolean isCasting6 = isCasting2;
                java.lang.Object obj5 = obj;
                com.lagradost.nicehttp.NiceResponse res4 = res2;
                java.lang.String data6 = data2;
                java.lang.Iterable $this$forEach$iv4 = doc4.select("video[src], video > source[src], source[src], video[data-src], source[data-src]");
                for (java.lang.Object element$iv3 : $this$forEach$iv4) {
                    org.jsoup.nodes.Element e = (org.jsoup.nodes.Element) element$iv3;
                    java.lang.String str4 = str2;
                    java.lang.String strAttr = e.attr(str4);
                    if (strAttr.length() == 0) {
                        str3 = str;
                        strAttr = e.attr(str3);
                    } else {
                        str3 = str;
                    }
                    java.lang.String v = strAttr;
                    if (!kotlin.text.StringsKt.isBlank(v)) {
                        found3.add(v);
                    }
                    str = str3;
                    str2 = str4;
                }
                data3 = str;
                iframeUrl = str2;
                java.lang.Iterable $this$mapNotNull$iv = doc4.select("iframe[src]");
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                    java.lang.String it5 = ((org.jsoup.nodes.Element) element$iv$iv$iv).attr(iframeUrl);
                    if (kotlin.text.StringsKt.isBlank(it5)) {
                        it5 = null;
                    }
                    if (it5 != null) {
                        destination$iv$iv.add(it5);
                    }
                }
                java.lang.Iterable $this$forEach$iv5 = (java.util.List) destination$iv$iv;
                it = $this$forEach$iv5.iterator();
                $this$forEach$iv = $this$forEach$iv5;
                doc = doc4;
                urlRegex = urlRegex4;
                found = found3;
                function15 = function14;
                function16 = function13;
                c000113 = c000112;
                coroutine_suspended = obj5;
                justthegays = this;
                isCasting3 = isCasting6;
                $result2 = res4;
                data4 = data6;
                continuation3 = continuation;
                $i$f$forEach = 0;
                if (it.hasNext()) {
                    java.lang.Object element$iv4 = it.next();
                    java.lang.String iframeUrl2 = (java.lang.String) element$iv4;
                    kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation4 = continuation3;
                    try {
                    } catch (java.lang.Exception e2) {
                        c000114 = c000113;
                        continuation3 = continuation4;
                        it2 = it;
                        urlRegex2 = urlRegex;
                        function17 = function15;
                        $result4 = $result;
                        headers2 = headers;
                        doc2 = doc;
                        break;
                    }
                    com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    c000113.L$0 = data4;
                    c000113.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function16);
                    c000113.L$2 = function15;
                    c000113.L$3 = headers;
                    c000113.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($result2);
                    c000113.L$5 = doc;
                    c000113.L$6 = urlRegex;
                    c000113.L$7 = found;
                    c000113.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEach$iv);
                    c000113.L$9 = it;
                    c000113.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv4);
                    c000113.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeUrl2);
                    c000113.Z$0 = isCasting3;
                    c000113.I$0 = $i$f$forEach;
                    c000113.I$1 = 0;
                    c000113.label = 2;
                    c000114 = c000113;
                    java.util.Map headers6 = headers;
                    $result4 = com.lagradost.nicehttp.Requests.get$default(app2, iframeUrl2, headers6, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000114, 4092, (java.lang.Object) null);
                    if ($result4 == coroutine_suspended) {
                        return coroutine_suspended;
                    }
                    continuation3 = continuation4;
                    it2 = it;
                    function17 = function15;
                    headers2 = headers6;
                    try {
                    } catch (java.lang.Exception e3) {
                        urlRegex2 = urlRegex;
                        $result4 = $result;
                        doc2 = doc;
                        break;
                    }
                    org.jsoup.nodes.Document iframeDoc = ((com.lagradost.nicehttp.NiceResponse) $result4).getDocument();
                    kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation5 = continuation3;
                    com.Justthegays.Justthegays justthegays4 = justthegays;
                    kotlin.sequences.Sequence $this$forEach$iv6 = kotlin.text.Regex.findAll$default(urlRegex, iframeDoc.html(), 0, 2, (java.lang.Object) null);
                    int $i$f$forEach2 = 0;
                    for (java.lang.Object element$iv5 : $this$forEach$iv6) {
                        kotlin.text.MatchResult m2 = (kotlin.text.MatchResult) element$iv5;
                        found.add(m2.getValue());
                        $i$f$forEach2 = $i$f$forEach2;
                        break;
                    }
                    java.lang.Iterable $this$forEach$iv7 = iframeDoc.select("video[src], source[src]");
                    for (java.lang.Object element$iv6 : $this$forEach$iv7) {
                        org.jsoup.nodes.Element el = (org.jsoup.nodes.Element) element$iv6;
                        org.jsoup.nodes.Document iframeDoc2 = iframeDoc;
                        java.lang.String strAttr2 = el.attr(iframeUrl);
                        if (strAttr2.length() == 0) {
                            strAttr2 = el.attr(data3);
                        }
                        java.lang.String v2 = strAttr2;
                        if (!kotlin.text.StringsKt.isBlank(v2)) {
                            found.add(v2);
                        }
                        iframeDoc = iframeDoc2;
                    }
                    continuation3 = continuation5;
                    justthegays = justthegays4;
                    it = it2;
                    c000113 = c000114;
                    headers = headers2;
                    function15 = function17;
                    if (it.hasNext()) {
                        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation6 = continuation3;
                        com.Justthegays.Justthegays.C00011 c000118 = c000113;
                        java.util.Map headers7 = headers;
                        kotlin.sequences.Sequence $this$forEach$iv8 = kotlin.text.Regex.findAll$default(urlRegex, doc.html(), 0, 2, (java.lang.Object) null);
                        for (java.lang.Object element$iv7 : $this$forEach$iv8) {
                            found.add(((kotlin.text.MatchResult) element$iv7).getValue());
                        }
                        java.lang.Iterable $this$map$iv = found;
                        java.util.Collection destination$iv$iv2 = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv, 10));
                        for (java.lang.Object item$iv$iv : $this$map$iv) {
                            destination$iv$iv2.add(kotlin.text.StringsKt.replace$default(kotlin.text.StringsKt.replace$default(kotlin.text.StringsKt.trim((java.lang.String) item$iv$iv).toString(), "&amp;", "&", false, 4, (java.lang.Object) null), " ", "%20", false, 4, (java.lang.Object) null));
                        }
                        java.lang.Iterable $this$filter$iv = (java.util.List) destination$iv$iv2;
                        java.util.Collection destination$iv$iv3 = new java.util.ArrayList();
                        for (java.lang.Object element$iv$iv : $this$filter$iv) {
                            if (!kotlin.text.StringsKt.isBlank((java.lang.String) element$iv$iv)) {
                                destination$iv$iv3.add(element$iv$iv);
                            }
                        }
                        java.util.List candidates2 = kotlin.collections.CollectionsKt.distinct((java.util.List) destination$iv$iv3);
                        if (candidates2.isEmpty()) {
                            java.lang.System.out.println((java.lang.Object) ("DEBUG: No video links found for " + data4));
                            return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                        }
                        $this$forEachIndexed$iv = candidates2;
                        $i$f$forEachIndexed = 0;
                        obj2 = coroutine_suspended;
                        it3 = $this$forEachIndexed$iv.iterator();
                        c000115 = c000118;
                        candidates = candidates2;
                        index$iv = 0;
                        continuation2 = continuation6;
                        justthegays2 = justthegays;
                        headers3 = headers7;
                        if (it3.hasNext()) {
                            java.lang.Object item$iv = it3.next();
                            kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation7 = continuation2;
                            int index$iv3 = index$iv + 1;
                            if (index$iv < 0) {
                                kotlin.collections.CollectionsKt.throwIndexOverflow();
                            }
                            java.lang.String url = (java.lang.String) item$iv;
                            java.lang.Iterable $this$forEachIndexed$iv3 = $this$forEachIndexed$iv;
                            java.util.List candidates3 = candidates;
                            com.Justthegays.Justthegays justthegays5 = justthegays2;
                            java.util.List found4 = found;
                            java.lang.String friendlyName = !kotlin.text.StringsKt.contains(url, "aucdn.net", true) ? kotlin.text.StringsKt.contains(url, "besthdgayporn.com", true) ? "Origin" : "Direct" : "CDN";
                            java.lang.String name = justthegays5.getName();
                            java.lang.String friendlyName2 = friendlyName;
                            java.lang.String str5 = friendlyName + ' ' + (index$iv + 1);
                            com.Justthegays.Justthegays$loadLinks$7$1 justthegays$loadLinks$7$1 = new com.Justthegays.Justthegays$loadLinks$7$1(data4, headers3, null);
                            c000115.L$0 = data4;
                            c000115.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function16);
                            c000115.L$2 = function15;
                            c000115.L$3 = headers3;
                            c000115.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($result2);
                            c000115.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(doc);
                            c000115.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(urlRegex);
                            c000115.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(found4);
                            c000115.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(candidates3);
                            c000115.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEachIndexed$iv3);
                            c000115.L$10 = it3;
                            c000115.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(item$iv);
                            c000115.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                            c000115.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(friendlyName2);
                            c000115.L$14 = function15;
                            c000115.Z$0 = isCasting3;
                            c000115.I$0 = $i$f$forEachIndexed;
                            c000115.I$1 = index$iv3;
                            c000115.I$2 = index$iv;
                            c000115.I$3 = 0;
                            c000115.label = 3;
                            kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function110 = function15;
                            int $i$f$forEachIndexed2 = $i$f$forEachIndexed;
                            boolean isCasting7 = isCasting3;
                            c000116 = c000115;
                            java.util.Iterator it6 = it3;
                            java.lang.Object objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name, str5, url, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, justthegays$loadLinks$7$1, c000116, 8, (java.lang.Object) null);
                            if (objNewExtractorLink$default == obj2) {
                                return obj2;
                            }
                            it4 = it6;
                            function18 = function110;
                            function19 = function18;
                            res = $result2;
                            index$iv2 = index$iv3;
                            headers4 = headers3;
                            isCasting4 = isCasting7;
                            $result4 = objNewExtractorLink$default;
                            $result3 = $result;
                            continuation3 = continuation7;
                            justthegays3 = justthegays5;
                            $i$f$forEachIndexed = $i$f$forEachIndexed2;
                            doc3 = doc;
                            candidates = candidates3;
                            urlRegex3 = urlRegex;
                            obj3 = obj2;
                            found2 = found4;
                            $this$forEachIndexed$iv2 = $this$forEachIndexed$iv3;
                            function18.invoke($result4);
                            continuation2 = continuation3;
                            $this$forEachIndexed$iv = $this$forEachIndexed$iv2;
                            justthegays2 = justthegays3;
                            index$iv = index$iv2;
                            obj2 = obj3;
                            urlRegex = urlRegex3;
                            isCasting3 = isCasting4;
                            it3 = it4;
                            c000115 = c000116;
                            function15 = function19;
                            found = found2;
                            doc = doc3;
                            $result = $result3;
                            headers3 = headers4;
                            $result2 = res;
                            if (it3.hasNext()) {
                                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(true);
                            }
                        }
                    }
                }
                break;
            case 1:
                isCasting2 = c000117.Z$0;
                headers = (java.util.Map) c000117.L$3;
                function14 = (kotlin.jvm.functions.Function1) c000117.L$2;
                function13 = (kotlin.jvm.functions.Function1) c000117.L$1;
                data2 = (java.lang.String) c000117.L$0;
                kotlin.ResultKt.throwOnFailure($result4);
                c000112 = c000117;
                $result = $result4;
                obj = coroutine_suspended;
                str = "abs:data-src";
                str2 = "abs:src";
                com.lagradost.nicehttp.NiceResponse res22 = (com.lagradost.nicehttp.NiceResponse) $result4;
                org.jsoup.nodes.Document doc42 = res22.getDocument();
                kotlin.text.Regex urlRegex42 = new kotlin.text.Regex("https?://[^\\s'\"]+?\\.(?:mp4|m3u8|webm)(\\?[^'\"\\s<>]*)?", kotlin.text.RegexOption.IGNORE_CASE);
                java.util.List found32 = new java.util.ArrayList();
                java.lang.Iterable $this$forEach$iv22 = doc42.select("script[type=application/ld+json]");
                while (r10.hasNext()) {
                }
                boolean isCasting62 = isCasting2;
                java.lang.Object obj52 = obj;
                com.lagradost.nicehttp.NiceResponse res42 = res22;
                java.lang.String data62 = data2;
                java.lang.Iterable $this$forEach$iv42 = doc42.select("video[src], video > source[src], source[src], video[data-src], source[data-src]");
                while (r7.hasNext()) {
                }
                data3 = str;
                iframeUrl = str2;
                java.lang.Iterable $this$mapNotNull$iv2 = doc42.select("iframe[src]");
                java.util.Collection destination$iv$iv4 = new java.util.ArrayList();
                while (r17.hasNext()) {
                }
                java.lang.Iterable $this$forEach$iv52 = (java.util.List) destination$iv$iv4;
                it = $this$forEach$iv52.iterator();
                $this$forEach$iv = $this$forEach$iv52;
                doc = doc42;
                urlRegex = urlRegex42;
                found = found32;
                function15 = function14;
                function16 = function13;
                c000113 = c000112;
                coroutine_suspended = obj52;
                justthegays = this;
                isCasting3 = isCasting62;
                $result2 = res42;
                data4 = data62;
                continuation3 = continuation;
                $i$f$forEach = 0;
                if (it.hasNext()) {
                }
                break;
            case 2:
                int i = c000117.I$1;
                $i$f$forEach = c000117.I$0;
                isCasting3 = c000117.Z$0;
                java.lang.Object obj6 = c000117.L$10;
                it2 = (java.util.Iterator) c000117.L$9;
                $this$forEach$iv = (java.lang.Iterable) c000117.L$8;
                java.util.List found5 = (java.util.List) c000117.L$7;
                urlRegex2 = (kotlin.text.Regex) c000117.L$6;
                doc2 = (org.jsoup.nodes.Document) c000117.L$5;
                $result2 = (com.lagradost.nicehttp.NiceResponse) c000117.L$4;
                headers2 = (java.util.Map) c000117.L$3;
                function17 = (kotlin.jvm.functions.Function1) c000117.L$2;
                function16 = (kotlin.jvm.functions.Function1) c000117.L$1;
                java.lang.String data7 = (java.lang.String) c000117.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result4);
                    c000114 = c000117;
                    urlRegex = urlRegex2;
                    doc = doc2;
                    data4 = data7;
                    $result = $result4;
                    data3 = "abs:data-src";
                    iframeUrl = "abs:src";
                    found = found5;
                } catch (java.lang.Exception e4) {
                    c000114 = c000117;
                    data4 = data7;
                    data3 = "abs:data-src";
                    iframeUrl = "abs:src";
                    found = found5;
                    urlRegex = urlRegex2;
                    doc = doc2;
                    $result = $result4;
                    it = it2;
                    c000113 = c000114;
                    headers = headers2;
                    function15 = function17;
                    if (it.hasNext()) {
                    }
                }
                org.jsoup.nodes.Document iframeDoc3 = ((com.lagradost.nicehttp.NiceResponse) $result4).getDocument();
                kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation52 = continuation3;
                com.Justthegays.Justthegays justthegays42 = justthegays;
                kotlin.sequences.Sequence $this$forEach$iv62 = kotlin.text.Regex.findAll$default(urlRegex, iframeDoc3.html(), 0, 2, (java.lang.Object) null);
                int $i$f$forEach22 = 0;
                while (r2.hasNext()) {
                    break;
                }
                java.lang.Iterable $this$forEach$iv72 = iframeDoc3.select("video[src], source[src]");
                while (r5.hasNext()) {
                }
                continuation3 = continuation52;
                justthegays = justthegays42;
                it = it2;
                c000113 = c000114;
                headers = headers2;
                function15 = function17;
                if (it.hasNext()) {
                }
                break;
            case 3:
                int i2 = c000117.I$3;
                int i3 = c000117.I$2;
                index$iv2 = c000117.I$1;
                int $i$f$forEachIndexed3 = c000117.I$0;
                boolean isCasting8 = c000117.Z$0;
                function18 = (kotlin.jvm.functions.Function1) c000117.L$14;
                java.lang.Object obj7 = c000117.L$11;
                java.util.Iterator it7 = (java.util.Iterator) c000117.L$10;
                java.lang.Iterable $this$forEachIndexed$iv4 = (java.lang.Iterable) c000117.L$9;
                java.util.List candidates4 = (java.util.List) c000117.L$8;
                found2 = (java.util.List) c000117.L$7;
                kotlin.text.Regex urlRegex5 = (kotlin.text.Regex) c000117.L$6;
                doc3 = (org.jsoup.nodes.Document) c000117.L$5;
                com.lagradost.nicehttp.NiceResponse res5 = (com.lagradost.nicehttp.NiceResponse) c000117.L$4;
                headers4 = (java.util.Map) c000117.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) c000117.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) c000117.L$1;
                java.lang.String data8 = (java.lang.String) c000117.L$0;
                kotlin.ResultKt.throwOnFailure($result4);
                function16 = function112;
                c000116 = c000117;
                it4 = it7;
                candidates = candidates4;
                res = res5;
                function19 = function111;
                data4 = data8;
                $result3 = $result4;
                $i$f$forEachIndexed = $i$f$forEachIndexed3;
                obj3 = coroutine_suspended;
                justthegays3 = justthegays;
                isCasting4 = isCasting8;
                urlRegex3 = urlRegex5;
                $this$forEachIndexed$iv2 = $this$forEachIndexed$iv4;
                function18.invoke($result4);
                continuation2 = continuation3;
                $this$forEachIndexed$iv = $this$forEachIndexed$iv2;
                justthegays2 = justthegays3;
                index$iv = index$iv2;
                obj2 = obj3;
                urlRegex = urlRegex3;
                isCasting3 = isCasting4;
                it3 = it4;
                c000115 = c000116;
                function15 = function19;
                found = found2;
                doc = doc3;
                $result = $result3;
                headers3 = headers4;
                $result2 = res;
                if (it3.hasNext()) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
