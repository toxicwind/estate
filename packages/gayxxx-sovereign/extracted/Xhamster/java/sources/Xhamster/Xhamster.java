package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000v\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0006\n\u0002\u0010\"\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010 \n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0012\u0010\u0019\u001a\u0004\u0018\u00010\u001a2\u0006\u0010\u001b\u001a\u00020\u0005H\u0002J\u0012\u0010\u001c\u001a\u0004\u0018\u00010\u001d2\u0006\u0010\u001e\u001a\u00020\u001fH\u0002J \u0010 \u001a\u0004\u0018\u00010!2\u0006\u0010\"\u001a\u00020#2\u0006\u0010$\u001a\u00020%H\u0096@¢\u0006\u0002\u0010&J\u001e\u0010'\u001a\n\u0012\u0004\u0012\u00020\u001d\u0018\u00010(2\u0006\u0010)\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010*J\u0018\u0010+\u001a\u0004\u0018\u00010,2\u0006\u0010-\u001a\u00020\u0005H\u0096@¢\u0006\u0002\u0010*JF\u0010.\u001a\u00020\u000e2\u0006\u0010/\u001a\u00020\u00052\u0006\u00100\u001a\u00020\u000e2\u0012\u00101\u001a\u000e\u0012\u0004\u0012\u000203\u0012\u0004\u0012\u000204022\u0012\u00105\u001a\u000e\u0012\u0004\u0012\u000206\u0012\u0004\u0012\u00020402H\u0096@¢\u0006\u0002\u00107R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010R\u001a\u0010\u0011\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0012\u0010\u0007\"\u0004\b\u0013\u0010\tR\u001a\u0010\u0014\u001a\b\u0012\u0004\u0012\u00020\u00160\u0015X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0018¨\u00068"}, d2 = {"LXhamster/Xhamster;", "Lcom/lagradost/cloudstream3/MainAPI;", "<init>", "()V", "mainUrl", "", "getMainUrl", "()Ljava/lang/String;", "setMainUrl", "(Ljava/lang/String;)V", "name", "getName", "setName", "hasMainPage", "", "getHasMainPage", "()Z", "lang", "getLang", "setLang", "supportedTypes", "", "Lcom/lagradost/cloudstream3/TvType;", "getSupportedTypes", "()Ljava/util/Set;", "getInitialsJson", "LXhamster/InitialsJson;", "html", "parseVideoItem", "Lcom/lagradost/cloudstream3/SearchResponse;", "element", "Lorg/jsoup/nodes/Element;", "getMainPage", "Lcom/lagradost/cloudstream3/HomePageResponse;", "page", "", "request", "Lcom/lagradost/cloudstream3/MainPageRequest;", "(ILcom/lagradost/cloudstream3/MainPageRequest;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "search", "", "query", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "load", "Lcom/lagradost/cloudstream3/LoadResponse;", "url", "loadLinks", "data", "isCasting", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;ZLkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nXhamster.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Xhamster.kt\nXhamster/Xhamster\n+ 2 AppUtils.kt\ncom/lagradost/cloudstream3/utils/AppUtils\n+ 3 Extensions.kt\ncom/fasterxml/jackson/module/kotlin/ExtensionsKt\n+ 4 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 5 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,382:1\n15#2:383\n50#3:384\n43#3:385\n1#4:386\n1#4:398\n1#4:412\n1#4:426\n1#4:440\n1#4:454\n1#4:468\n1#4:482\n1#4:496\n1642#5,10:387\n1915#5:397\n1916#5:399\n1652#5:400\n1642#5,10:401\n1915#5:411\n1916#5:413\n1652#5:414\n1642#5,10:415\n1915#5:425\n1916#5:427\n1652#5:428\n1642#5,10:429\n1915#5:439\n1916#5:441\n1652#5:442\n1642#5,10:443\n1915#5:453\n1916#5:455\n1652#5:456\n1642#5,10:457\n1915#5:467\n1916#5:469\n1652#5:470\n1642#5,10:471\n1915#5:481\n1916#5:483\n1652#5:484\n1642#5,10:485\n1915#5:495\n1916#5:497\n1652#5:498\n777#5:499\n873#5,2:500\n1915#5,2:502\n1915#5,2:504\n1915#5,2:506\n*S KotlinDebug\n*F\n+ 1 Xhamster.kt\nXhamster/Xhamster\n*L\n132#1:383\n132#1:384\n132#1:385\n173#1:398\n191#1:412\n234#1:426\n250#1:440\n287#1:454\n288#1:468\n296#1:482\n306#1:496\n173#1:387,10\n173#1:397\n173#1:399\n173#1:400\n191#1:401,10\n191#1:411\n191#1:413\n191#1:414\n234#1:415,10\n234#1:425\n234#1:427\n234#1:428\n250#1:429,10\n250#1:439\n250#1:441\n250#1:442\n287#1:443,10\n287#1:453\n287#1:455\n287#1:456\n288#1:457,10\n288#1:467\n288#1:469\n288#1:470\n296#1:471,10\n296#1:481\n296#1:483\n296#1:484\n306#1:485,10\n306#1:495\n306#1:497\n306#1:498\n307#1:499\n307#1:500,2\n349#1:502,2\n356#1:504,2\n367#1:506,2\n*E\n"})
public final class Xhamster extends com.lagradost.cloudstream3.MainAPI {

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://vi.xhspot.com/gay";

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Xhamster";
    private final boolean hasMainPage = true;

    @org.jetbrains.annotations.NotNull
    private java.lang.String lang = "vi";

    @org.jetbrains.annotations.NotNull
    private final java.util.Set<com.lagradost.cloudstream3.TvType> supportedTypes = kotlin.collections.SetsKt.setOf(com.lagradost.cloudstream3.TvType.NSFW);

    /* JADX INFO: renamed from: Xhamster.Xhamster$getMainPage$1, reason: invalid class name */
    /* JADX INFO: compiled from: Xhamster.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "Xhamster.Xhamster", f = "Xhamster.kt", i = {0, 0}, l = {165}, m = "getMainPage", n = {"request", "page"}, nl = {166}, s = {"L$0", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        java.lang.Object L$0;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super Xhamster.Xhamster.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return Xhamster.Xhamster.this.getMainPage(0, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: Xhamster.Xhamster$load$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Xhamster.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "Xhamster.Xhamster", f = "Xhamster.kt", i = {0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {269, 321}, m = "load", n = {"url", "url", "document", "htmlContent", "initialData", "title", "plot", "poster", "fixedPoster", "tags", "recommendations"}, nl = {270, -1}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9"}, v = 2)
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
        java.lang.Object L$9;
        int label;
        /* synthetic */ java.lang.Object result;

        C00001(kotlin.coroutines.Continuation<? super Xhamster.Xhamster.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return Xhamster.Xhamster.this.load(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: Xhamster.Xhamster$loadLinks$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Xhamster.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "Xhamster.Xhamster", f = "Xhamster.kt", i = {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3}, l = {338, 349, 352, 363}, m = "loadLinks", n = {"data", "subtitleCallback", "callback", "isCasting", "data", "subtitleCallback", "callback", "document", "initialData", "foundLinks", "sources", "sourceName", "m3u8Url", "fixedM3u8Url", "isCasting", "$i$a$-let-Xhamster$loadLinks$2", "data", "subtitleCallback", "callback", "document", "initialData", "foundLinks", "sources", "sourceName", "m3u8Url", "fixedM3u8Url", "e", "isCasting", "$i$a$-let-Xhamster$loadLinks$2", "data", "subtitleCallback", "callback", "document", "initialData", "foundLinks", "sources", "sourceName", "$this$forEach$iv", "element$iv", "qualitySource", "qualityLabel", "videoUrl", "fixedVideoUrl", "isCasting", "$i$f$forEach", "$i$a$-forEach-Xhamster$loadLinks$3", "quality"}, nl = {339, 384, 354, 364}, s = {"L$0", "L$1", "L$2", "Z$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "Z$0", "I$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "Z$0", "I$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$10", "L$11", "L$12", "L$13", "L$14", "Z$0", "I$0", "I$1", "I$2"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        int I$2;
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

        C00011(kotlin.coroutines.Continuation<? super Xhamster.Xhamster.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return Xhamster.Xhamster.this.loadLinks(null, false, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: Xhamster.Xhamster$search$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Xhamster.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "Xhamster.Xhamster", f = "Xhamster.kt", i = {0, 0}, l = {220}, m = "search", n = {"query", "searchUrl"}, nl = {221}, s = {"L$0", "L$1"}, v = 2)
    static final class C00021 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        int label;
        /* synthetic */ java.lang.Object result;

        C00021(kotlin.coroutines.Continuation<? super Xhamster.Xhamster.C00021> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return Xhamster.Xhamster.this.search(null, (kotlin.coroutines.Continuation) this);
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

    @org.jetbrains.annotations.NotNull
    public java.util.Set<com.lagradost.cloudstream3.TvType> getSupportedTypes() {
        return this.supportedTypes;
    }

    private final Xhamster.InitialsJson getInitialsJson(java.lang.String html) {
        java.lang.String script;
        try {
            org.jsoup.nodes.Element elementSelectFirst = org.jsoup.Jsoup.parse(html).selectFirst("script#initials-script");
            if (elementSelectFirst != null && (script = elementSelectFirst.html()) != null) {
                java.lang.String jsonString = kotlin.text.StringsKt.removeSuffix(kotlin.text.StringsKt.removePrefix(script, "window.initials="), ";");
                com.lagradost.cloudstream3.utils.AppUtils appUtils = com.lagradost.cloudstream3.utils.AppUtils.INSTANCE;
                com.fasterxml.jackson.databind.ObjectMapper $this$readValue$iv$iv = com.lagradost.cloudstream3.MainAPIKt.getMapper();
                return (Xhamster.InitialsJson) $this$readValue$iv$iv.readValue(jsonString, new com.fasterxml.jackson.core.type.TypeReference<Xhamster.InitialsJson>() { // from class: Xhamster.Xhamster$getInitialsJson$$inlined$parseJson$1
                });
            }
            return null;
        } catch (java.lang.Exception e) {
            android.util.Log.e(getName(), "getInitialsJson failed: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    private final com.lagradost.cloudstream3.SearchResponse parseVideoItem(org.jsoup.nodes.Element element) {
        java.lang.String strAttr;
        java.lang.String strAttr2;
        java.lang.String posterUrl;
        java.lang.String it;
        org.jsoup.nodes.Element titleElement = element.selectFirst("a.mobile-video-thumb__name");
        org.jsoup.nodes.Element imageElement = element.selectFirst("a.thumb-image-container img");
        final java.lang.String fixedPoster = null;
        if (titleElement == null || (strAttr = titleElement.text()) == null) {
            strAttr = imageElement != null ? imageElement.attr("alt") : null;
            if (strAttr == null) {
                return null;
            }
        }
        java.lang.String title = strAttr;
        if (titleElement == null || (strAttr2 = titleElement.attr("href")) == null) {
            org.jsoup.nodes.Element elementSelectFirst = element.selectFirst("a.thumb-image-container");
            if (elementSelectFirst == null) {
                strAttr2 = null;
            } else {
                strAttr2 = elementSelectFirst.attr("href");
            }
            if (strAttr2 == null) {
                return null;
            }
        }
        java.lang.String href = strAttr2;
        java.lang.String fixedHref = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, href);
        java.lang.String posterUrl2 = imageElement != null ? imageElement.attr("srcset") : null;
        java.lang.String str = posterUrl2;
        if (!(str == null || kotlin.text.StringsKt.isBlank(str))) {
            posterUrl = posterUrl2;
        } else {
            posterUrl = imageElement != null ? imageElement.attr("src") : null;
        }
        if (posterUrl != null && (it = kotlin.text.StringsKt.trim(posterUrl).toString()) != null) {
            fixedPoster = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, it);
        }
        return com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, fixedHref, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: Xhamster.Xhamster$$ExternalSyntheticLambda1
            public final java.lang.Object invoke(java.lang.Object obj) {
                return Xhamster.Xhamster.parseVideoItem$lambda$1(fixedPoster, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
            }
        }, 8, (java.lang.Object) null);
    }

    static final kotlin.Unit parseVideoItem$lambda$1(java.lang.String $fixedPoster, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($fixedPoster);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:30:0x00e2  */
    /* JADX WARN: Removed duplicated region for block: B:61:0x01b8  */
    /* JADX WARN: Removed duplicated region for block: B:68:0x01d3  */
    /* JADX WARN: Removed duplicated region for block: B:70:0x01d6  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /* JADX WARN: Removed duplicated region for block: B:82:0x025b  */
    /* JADX WARN: Removed duplicated region for block: B:90:0x026d  */
    /* JADX WARN: Removed duplicated region for block: B:91:0x02a2  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getMainPage(int page, @org.jetbrains.annotations.NotNull com.lagradost.cloudstream3.MainPageRequest request, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.HomePageResponse> continuation) {
        Xhamster.Xhamster.AnonymousClass1 anonymousClass1;
        boolean z;
        com.lagradost.cloudstream3.MovieSearchResponse movieSearchResponseNewMovieSearchResponse$default;
        Xhamster.InitialsJson initialData;
        java.util.List list;
        java.util.List list2;
        java.util.List list3;
        Xhamster.VideoListProps videoListProps;
        java.lang.Iterable videoThumbProps;
        if (continuation instanceof Xhamster.Xhamster.AnonymousClass1) {
            anonymousClass1 = (Xhamster.Xhamster.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new Xhamster.Xhamster.AnonymousClass1(continuation);
            }
        }
        Xhamster.Xhamster.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                if (page > 1) {
                    return null;
                }
                android.util.Log.d(getName(), "getMainPage started for page " + page);
                try {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    java.lang.String str = getMainUrl() + '/';
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(request);
                    anonymousClass12.I$0 = page;
                    anonymousClass12.label = 1;
                    z = true;
                    movieSearchResponseNewMovieSearchResponse$default = null;
                    try {
                        $result = com.lagradost.nicehttp.Requests.get$default(app, str, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                        if ($result == coroutine_suspended) {
                            return coroutine_suspended;
                        }
                        try {
                            org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                            initialData = getInitialsJson(document.html());
                            java.util.List items = null;
                            java.lang.String listTitle = "Video Trang Chủ";
                            if (initialData == null) {
                                android.util.Log.d(getName(), "getMainPage: Parsed initialData JSON.");
                                Xhamster.LayoutPage layoutPage = initialData.getLayoutPage();
                                if (layoutPage == null || (videoListProps = layoutPage.getVideoListProps()) == null || (videoThumbProps = videoListProps.getVideoThumbProps()) == null) {
                                    list3 = null;
                                } else {
                                    java.lang.Iterable $this$mapNotNull$iv = videoThumbProps;
                                    java.util.Collection destination$iv$iv = new java.util.ArrayList();
                                    for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                                        Xhamster.VideoThumbProps item = (Xhamster.VideoThumbProps) element$iv$iv$iv;
                                        java.lang.String title = item.getTitle();
                                        if (title != null) {
                                            java.lang.String href = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, item.getPageURL());
                                            if (href == null) {
                                                movieSearchResponseNewMovieSearchResponse$default = null;
                                            } else {
                                                final java.lang.String poster = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, item.getThumbUrl());
                                                movieSearchResponseNewMovieSearchResponse$default = com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: Xhamster.Xhamster$$ExternalSyntheticLambda2
                                                    public final java.lang.Object invoke(java.lang.Object obj) {
                                                        return Xhamster.Xhamster.getMainPage$lambda$0$0(poster, (com.lagradost.cloudstream3.MovieSearchResponse) obj);
                                                    }
                                                }, 8, (java.lang.Object) null);
                                            }
                                        }
                                        if (movieSearchResponseNewMovieSearchResponse$default != null) {
                                            destination$iv$iv.add(movieSearchResponseNewMovieSearchResponse$default);
                                        }
                                        movieSearchResponseNewMovieSearchResponse$default = null;
                                    }
                                    list3 = (java.util.List) destination$iv$iv;
                                }
                                items = list3;
                                java.util.List list4 = items;
                                if (list4 == null || list4.isEmpty()) {
                                    android.util.Log.w(getName(), "getMainPage: JSON items list is null or empty after mapping.");
                                    items = null;
                                    kotlin.Unit unit = kotlin.Unit.INSTANCE;
                                } else {
                                    listTitle = "Video Trang Chủ";
                                    kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.d(getName(), "getMainPage: Mapped " + items.size() + " items from JSON."));
                                }
                            } else {
                                kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "getMainPage: Failed to parse initialData JSON."));
                            }
                            list = items;
                            if (!(list != null || list.isEmpty())) {
                                android.util.Log.w(getName(), "getMainPage: Falling back to HTML parsing.");
                                java.lang.Iterable $this$mapNotNull$iv2 = document.select("div.mobile-video-thumb");
                                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                                for (java.lang.Object element$iv$iv$iv2 : $this$mapNotNull$iv2) {
                                    org.jsoup.nodes.Document document2 = document;
                                    org.jsoup.nodes.Element element = (org.jsoup.nodes.Element) element$iv$iv$iv2;
                                    com.lagradost.cloudstream3.SearchResponse videoItem = parseVideoItem(element);
                                    if (videoItem != null) {
                                        destination$iv$iv2.add(videoItem);
                                    }
                                    document = document2;
                                }
                                items = (java.util.List) destination$iv$iv2;
                                if (items.isEmpty()) {
                                    android.util.Log.w(getName(), "getMainPage: HTML fallback also yielded no items.");
                                } else {
                                    listTitle = "Video Trang Chủ";
                                    android.util.Log.d(getName(), "getMainPage: Mapped " + items.size() + " items from HTML fallback.");
                                }
                            }
                            list2 = items;
                            if (list2 != null && !list2.isEmpty()) {
                                z = false;
                            }
                            if (z) {
                                android.util.Log.i(getName(), "getMainPage: Successfully loaded " + items.size() + " items using " + listTitle + " logic.");
                                return com.lagradost.cloudstream3.MainAPIKt.newHomePageResponse$default(listTitle, items, (java.lang.Boolean) null, 4, (java.lang.Object) null);
                            }
                            android.util.Log.e(getName(), "getMainPage: No items found from JSON or HTML.");
                            return null;
                        } catch (java.lang.Exception e) {
                            e = e;
                            android.util.Log.e(getName(), "Failed to fetch main page: " + e.getMessage());
                            return null;
                        }
                    } catch (java.lang.Exception e2) {
                        e = e2;
                        android.util.Log.e(getName(), "Failed to fetch main page: " + e.getMessage());
                        return null;
                    }
                } catch (java.lang.Exception e3) {
                    e = e3;
                }
                break;
            case 1:
                int i = anonymousClass12.I$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result);
                    z = true;
                    movieSearchResponseNewMovieSearchResponse$default = null;
                    org.jsoup.nodes.Document document3 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    initialData = getInitialsJson(document3.html());
                    java.util.List items2 = null;
                    java.lang.String listTitle2 = "Video Trang Chủ";
                    if (initialData == null) {
                    }
                    list = items2;
                    if (!(list != null || list.isEmpty())) {
                    }
                    list2 = items2;
                    if (list2 != null) {
                        z = false;
                    }
                    if (z) {
                    }
                } catch (java.lang.Exception e4) {
                    e = e4;
                    android.util.Log.e(getName(), "Failed to fetch main page: " + e.getMessage());
                    return null;
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit getMainPage$lambda$0$0(java.lang.String $poster, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($poster);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:27:0x00e9  */
    /* JADX WARN: Removed duplicated region for block: B:51:0x019c  */
    /* JADX WARN: Removed duplicated region for block: B:58:0x01b3  */
    /* JADX WARN: Removed duplicated region for block: B:60:0x01b6  */
    /* JADX WARN: Removed duplicated region for block: B:68:0x0226  */
    /* JADX WARN: Removed duplicated region for block: B:75:0x0236  */
    /* JADX WARN: Removed duplicated region for block: B:78:0x023b  */
    /* JADX WARN: Removed duplicated region for block: B:79:0x026a  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object search(@org.jetbrains.annotations.NotNull java.lang.String query, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.SearchResponse>> continuation) {
        Xhamster.Xhamster.C00021 c00021;
        com.lagradost.nicehttp.Requests app;
        Xhamster.InitialsJson initialData;
        java.util.List list;
        java.util.List list2;
        java.util.List list3;
        java.lang.Iterable videoThumbProps;
        java.lang.String href;
        com.lagradost.cloudstream3.MovieSearchResponse movieSearchResponseNewMovieSearchResponse$default;
        java.lang.String query2 = query;
        if (continuation instanceof Xhamster.Xhamster.C00021) {
            c00021 = (Xhamster.Xhamster.C00021) continuation;
            if ((c00021.label & Integer.MIN_VALUE) != 0) {
                c00021.label -= Integer.MIN_VALUE;
            } else {
                c00021 = new Xhamster.Xhamster.C00021(continuation);
            }
        }
        Xhamster.Xhamster.C00021 c000212 = c00021;
        java.lang.Object $result = c000212.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000212.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String searchUrl = getMainUrl() + "/search/" + query2;
                android.util.Log.d(getName(), "Search started for query '" + query2 + "' at URL: " + searchUrl);
                try {
                    app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    c000212.L$0 = query2;
                    c000212.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(searchUrl);
                    c000212.label = 1;
                } catch (java.lang.Exception e) {
                    e = e;
                }
                try {
                    java.lang.Object obj = com.lagradost.nicehttp.Requests.get$default(app, searchUrl, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000212, 4094, (java.lang.Object) null);
                    if (obj == coroutine_suspended) {
                        return coroutine_suspended;
                    }
                    $result = obj;
                    try {
                        org.jsoup.nodes.Document document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                        initialData = getInitialsJson(document.html());
                        java.util.List results = null;
                        if (initialData == null) {
                            android.util.Log.d(getName(), "Search: Parsed initialData JSON.");
                            Xhamster.SearchResult searchResult = initialData.getSearchResult();
                            if (searchResult == null || (videoThumbProps = searchResult.getVideoThumbProps()) == null) {
                                list3 = null;
                            } else {
                                java.lang.Iterable $this$mapNotNull$iv = videoThumbProps;
                                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                                    Xhamster.VideoThumbProps item = (Xhamster.VideoThumbProps) element$iv$iv$iv;
                                    java.lang.String title = item.getTitle();
                                    if (title == null || (href = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, item.getPageURL())) == null) {
                                        movieSearchResponseNewMovieSearchResponse$default = null;
                                    } else {
                                        final java.lang.String poster = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, item.getThumbUrl());
                                        movieSearchResponseNewMovieSearchResponse$default = com.lagradost.cloudstream3.MainAPIKt.newMovieSearchResponse$default(this, title, href, com.lagradost.cloudstream3.TvType.NSFW, false, new kotlin.jvm.functions.Function1() { // from class: Xhamster.Xhamster$$ExternalSyntheticLambda0
                                            public final java.lang.Object invoke(java.lang.Object obj2) {
                                                return Xhamster.Xhamster.search$lambda$0$0(poster, (com.lagradost.cloudstream3.MovieSearchResponse) obj2);
                                            }
                                        }, 8, (java.lang.Object) null);
                                    }
                                    if (movieSearchResponseNewMovieSearchResponse$default != null) {
                                        destination$iv$iv.add(movieSearchResponseNewMovieSearchResponse$default);
                                    }
                                }
                                list3 = (java.util.List) destination$iv$iv;
                            }
                            results = list3;
                            android.util.Log.d(getName(), "Search: Mapped " + (results != null ? results.size() : 0) + " items from JSON.");
                        } else {
                            android.util.Log.w(getName(), "Search: Failed to parse initialData JSON.");
                        }
                        list = results;
                        if (!(list != null || list.isEmpty())) {
                            android.util.Log.w(getName(), "Search: JSON results list is null or empty. Falling back to HTML parsing.");
                            java.lang.Iterable $this$mapNotNull$iv2 = document.select("div.mobile-video-thumb");
                            java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                            for (java.lang.Object element$iv$iv$iv2 : $this$mapNotNull$iv2) {
                                org.jsoup.nodes.Document document2 = document;
                                org.jsoup.nodes.Element element = (org.jsoup.nodes.Element) element$iv$iv$iv2;
                                com.lagradost.cloudstream3.SearchResponse videoItem = parseVideoItem(element);
                                if (videoItem != null) {
                                    destination$iv$iv2.add(videoItem);
                                }
                                document = document2;
                            }
                            results = (java.util.List) destination$iv$iv2;
                            android.util.Log.d(getName(), "Search: Mapped " + results.size() + " items from HTML fallback.");
                        }
                        list2 = results;
                        if (list2 != null || list2.isEmpty()) {
                            android.util.Log.i(getName(), "Search: Found " + results.size() + " results for query '" + query2 + "'.");
                            return results;
                        }
                        android.util.Log.e(getName(), "Search: No results found for query '" + query2 + "'.");
                        return null;
                    } catch (java.lang.Exception e2) {
                        e = e2;
                        android.util.Log.e(getName(), "Failed to fetch search page: " + e.getMessage());
                        e.printStackTrace();
                        return null;
                    }
                } catch (java.lang.Exception e3) {
                    e = e3;
                    android.util.Log.e(getName(), "Failed to fetch search page: " + e.getMessage());
                    e.printStackTrace();
                    return null;
                }
            case 1:
                query2 = (java.lang.String) c000212.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result);
                    org.jsoup.nodes.Document document3 = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    initialData = getInitialsJson(document3.html());
                    java.util.List results2 = null;
                    if (initialData == null) {
                    }
                    list = results2;
                    if (!(list != null || list.isEmpty())) {
                    }
                    list2 = results2;
                    if (list2 != null || list2.isEmpty()) {
                    }
                } catch (java.lang.Exception e4) {
                    e = e4;
                    android.util.Log.e(getName(), "Failed to fetch search page: " + e.getMessage());
                    e.printStackTrace();
                    return null;
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit search$lambda$0$0(java.lang.String $poster, com.lagradost.cloudstream3.MovieSearchResponse $this$newMovieSearchResponse) {
        $this$newMovieSearchResponse.setPosterUrl($poster);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:105:0x0253  */
    /* JADX WARN: Removed duplicated region for block: B:111:0x0283 A[Catch: Exception -> 0x03b9, TRY_LEAVE, TryCatch #1 {Exception -> 0x03b9, blocks: (B:108:0x0262, B:109:0x027d, B:111:0x0283), top: B:174:0x0262 }] */
    /* JADX WARN: Removed duplicated region for block: B:119:0x02b6  */
    /* JADX WARN: Removed duplicated region for block: B:122:0x02cd A[Catch: Exception -> 0x03b7, TryCatch #3 {Exception -> 0x03b7, blocks: (B:113:0x0297, B:115:0x029d, B:117:0x02a7, B:120:0x02b8, B:122:0x02cd, B:124:0x02d3, B:126:0x02f2, B:127:0x0317, B:129:0x031d, B:131:0x0335, B:133:0x033e, B:134:0x0354, B:136:0x035a, B:138:0x0370, B:141:0x037b, B:144:0x038a, B:146:0x039f, B:148:0x03a5), top: B:178:0x0297 }] */
    /* JADX WARN: Removed duplicated region for block: B:123:0x02d2  */
    /* JADX WARN: Removed duplicated region for block: B:126:0x02f2 A[Catch: Exception -> 0x03b7, TryCatch #3 {Exception -> 0x03b7, blocks: (B:113:0x0297, B:115:0x029d, B:117:0x02a7, B:120:0x02b8, B:122:0x02cd, B:124:0x02d3, B:126:0x02f2, B:127:0x0317, B:129:0x031d, B:131:0x0335, B:133:0x033e, B:134:0x0354, B:136:0x035a, B:138:0x0370, B:141:0x037b, B:144:0x038a, B:146:0x039f, B:148:0x03a5), top: B:178:0x0297 }] */
    /* JADX WARN: Removed duplicated region for block: B:157:0x03f5  */
    /* JADX WARN: Removed duplicated region for block: B:158:0x03fe  */
    /* JADX WARN: Removed duplicated region for block: B:161:0x0465 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:162:0x0466  */
    /* JADX WARN: Removed duplicated region for block: B:35:0x00fa  */
    /* JADX WARN: Removed duplicated region for block: B:37:0x0102  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x0107  */
    /* JADX WARN: Removed duplicated region for block: B:40:0x010a  */
    /* JADX WARN: Removed duplicated region for block: B:50:0x0130  */
    /* JADX WARN: Removed duplicated region for block: B:52:0x014f  */
    /* JADX WARN: Removed duplicated region for block: B:58:0x015e  */
    /* JADX WARN: Removed duplicated region for block: B:63:0x0177  */
    /* JADX WARN: Removed duplicated region for block: B:72:0x018e  */
    /* JADX WARN: Removed duplicated region for block: B:76:0x019b  */
    /* JADX WARN: Removed duplicated region for block: B:78:0x019e  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001c  */
    /* JADX WARN: Removed duplicated region for block: B:96:0x0206  */
    /* JADX WARN: Removed duplicated region for block: B:99:0x0226  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object load(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super com.lagradost.cloudstream3.LoadResponse> continuation) {
        Xhamster.Xhamster.C00001 c00001;
        java.lang.String url2;
        com.lagradost.nicehttp.Requests app;
        java.lang.Object obj;
        org.jsoup.nodes.Document document;
        Xhamster.InitialsJson initialData;
        java.lang.String title;
        java.lang.String str;
        java.lang.String strText;
        java.lang.String string;
        java.lang.String strText2;
        java.lang.String thumbBig;
        Xhamster.VideoEntity videoEntity;
        java.util.Collection collection;
        java.util.List tags;
        kotlin.jvm.internal.Ref.ObjectRef recommendations;
        Xhamster.InitialsJson initialData2;
        java.util.ArrayList arrayList;
        Xhamster.VideoTagsComponent videoTagsComponent;
        java.lang.Iterable tags2;
        Xhamster.XPlayerSettings xplayerSettings;
        Xhamster.Poster poster;
        Xhamster.VideoEntity videoEntity2;
        Xhamster.VideoEntity videoEntity3;
        if (continuation instanceof Xhamster.Xhamster.C00001) {
            c00001 = (Xhamster.Xhamster.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new Xhamster.Xhamster.C00001(continuation);
            }
        }
        Xhamster.Xhamster.C00001 c000012 = c00001;
        java.lang.Object $result = c000012.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000012.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                android.util.Log.d(getName(), "Loading URL: " + url);
                try {
                    app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    c000012.L$0 = url;
                    c000012.label = 1;
                    obj = coroutine_suspended;
                } catch (java.lang.Exception e) {
                    e = e;
                    url2 = url;
                }
                try {
                    $result = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000012, 4094, (java.lang.Object) null);
                    c000012 = c000012;
                    if ($result == obj) {
                        return obj;
                    }
                    url2 = url;
                    try {
                        document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                        java.lang.String htmlContent = document.html();
                        initialData = getInitialsJson(htmlContent);
                        if (initialData != null || (videoEntity3 = initialData.getVideoEntity()) == null || (title = videoEntity3.getTitle()) == null) {
                            org.jsoup.nodes.Element elementSelectFirst = document.selectFirst("meta[property=og:title]");
                            title = elementSelectFirst == null ? elementSelectFirst.attr("content") : null;
                            if (title != null) {
                                org.jsoup.nodes.Element elementSelectFirst2 = document.selectFirst("title");
                                if (elementSelectFirst2 == null || (strText = elementSelectFirst2.text()) == null) {
                                    str = null;
                                } else {
                                    str = null;
                                    java.lang.String strSubstringBefore$default = kotlin.text.StringsKt.substringBefore$default(strText, "|", (java.lang.String) null, 2, (java.lang.Object) null);
                                    if (strSubstringBefore$default != null) {
                                        title = kotlin.text.StringsKt.trim(strSubstringBefore$default).toString();
                                    }
                                    if (title == null) {
                                        Xhamster.Xhamster $this$load_u24lambda_u240 = this;
                                        android.util.Log.e($this$load_u24lambda_u240.getName(), "Could not find title for " + url2);
                                        return str;
                                    }
                                }
                                title = str;
                                if (title == null) {
                                }
                            } else {
                                str = null;
                            }
                        } else {
                            str = null;
                        }
                        if (initialData != null || (videoEntity2 = initialData.getVideoEntity()) == null || (string = videoEntity2.getDescription()) == null) {
                            org.jsoup.nodes.Element elementSelectFirst3 = document.selectFirst("div.video-description p[itemprop=description]");
                            string = (elementSelectFirst3 != null || (strText2 = elementSelectFirst3.text()) == null) ? str : kotlin.text.StringsKt.trim(strText2).toString();
                        }
                        java.lang.String plot = string;
                        if (initialData != null || (xplayerSettings = initialData.getXplayerSettings()) == null || (poster = xplayerSettings.getPoster()) == null || (thumbBig = poster.getUrl()) == null) {
                            thumbBig = (initialData != null || (videoEntity = initialData.getVideoEntity()) == null) ? str : videoEntity.getThumbBig();
                            if (thumbBig == null) {
                                org.jsoup.nodes.Element elementSelectFirst4 = document.selectFirst("meta[property=og:image]");
                                thumbBig = elementSelectFirst4 != null ? elementSelectFirst4.attr("content") : str;
                            }
                        }
                        java.lang.String poster2 = thumbBig;
                        java.lang.String fixedPoster = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, poster2);
                        if (initialData != null || (videoTagsComponent = initialData.getVideoTagsComponent()) == null || (tags2 = videoTagsComponent.getTags()) == null) {
                            java.lang.Iterable $this$mapNotNull$iv = document.select("section[data-role=video-tags] a.item");
                            java.util.Collection destination$iv$iv = new java.util.ArrayList();
                            for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                                org.jsoup.nodes.Element it = (org.jsoup.nodes.Element) element$iv$iv$iv;
                                java.lang.String strText3 = it.text();
                                if (strText3 != null) {
                                    destination$iv$iv.add(strText3);
                                }
                            }
                            collection = (java.util.List) destination$iv$iv;
                            if (collection.isEmpty()) {
                                collection = null;
                            }
                            tags = collection;
                        } else {
                            java.lang.Iterable $this$mapNotNull$iv2 = tags2;
                            java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                            for (java.lang.Object element$iv$iv$iv2 : $this$mapNotNull$iv2) {
                                Xhamster.Tag it2 = (Xhamster.Tag) element$iv$iv$iv2;
                                java.lang.String name = it2.getName();
                                if (name != null) {
                                    destination$iv$iv2.add(name);
                                }
                            }
                            tags = (java.util.List) destination$iv$iv2;
                        }
                        recommendations = new kotlin.jvm.internal.Ref.ObjectRef();
                        try {
                            java.lang.Iterable $this$mapNotNull$iv3 = document.select("div[data-role=video-related] div.mobile-video-thumb");
                            java.util.Collection destination$iv$iv3 = new java.util.ArrayList();
                            for (java.lang.Object element$iv$iv$iv3 : $this$mapNotNull$iv3) {
                                org.jsoup.nodes.Element element = (org.jsoup.nodes.Element) element$iv$iv$iv3;
                                initialData2 = initialData;
                                try {
                                    com.lagradost.cloudstream3.SearchResponse videoItem = parseVideoItem(element);
                                    if (videoItem != null) {
                                        destination$iv$iv3.add(videoItem);
                                    }
                                    initialData = initialData2;
                                } catch (java.lang.Exception e2) {
                                    e = e2;
                                    android.util.Log.e(getName(), "Error parsing recommendations from HTML: " + e.getMessage());
                                    e.printStackTrace();
                                    recommendations.element = null;
                                    java.lang.String name2 = getName();
                                    java.lang.StringBuilder sbAppend = new java.lang.StringBuilder().append("Final recommendations count being added to LoadResponse: ");
                                    java.util.List list = (java.util.List) recommendations.element;
                                    android.util.Log.i(name2, sbAppend.append(list != null ? kotlin.coroutines.jvm.internal.Boxing.boxInt(list.size()) : null).toString());
                                    com.lagradost.cloudstream3.TvType tvType = com.lagradost.cloudstream3.TvType.NSFW;
                                    Xhamster.Xhamster.AnonymousClass7 anonymousClass7 = new Xhamster.Xhamster.AnonymousClass7(plot, fixedPoster, tags, recommendations, null);
                                    c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                                    c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                    c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(htmlContent);
                                    c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialData2);
                                    c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
                                    c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(plot);
                                    c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster2);
                                    c000012.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedPoster);
                                    c000012.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(tags);
                                    c000012.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
                                    c000012.label = 2;
                                    $result = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType, url2, anonymousClass7, c000012);
                                    if ($result == obj) {
                                    }
                                }
                                break;
                            }
                            initialData2 = initialData;
                            arrayList = (java.util.List) destination$iv$iv3;
                            if (arrayList.isEmpty()) {
                                arrayList = null;
                            }
                            recommendations.element = arrayList;
                            java.lang.String name3 = getName();
                            java.lang.StringBuilder sbAppend2 = new java.lang.StringBuilder().append("Found ");
                            java.util.List list2 = (java.util.List) recommendations.element;
                            android.util.Log.d(name3, sbAppend2.append(list2 == null ? list2.size() : 0).append(" recommendations using HTML selector '").append("div[data-role=video-related] div.mobile-video-thumb").append("'.").toString());
                            if (recommendations.element == null) {
                                android.util.Log.w(getName(), "Primary HTML selector for recommendations failed, trying broader selector.");
                                java.lang.Iterable $this$mapNotNull$iv4 = document.select("ul.thumb-list div.mobile-video-thumb");
                                java.util.Collection destination$iv$iv4 = new java.util.ArrayList();
                                for (java.lang.Object element$iv$iv$iv4 : $this$mapNotNull$iv4) {
                                    org.jsoup.nodes.Element it3 = (org.jsoup.nodes.Element) element$iv$iv$iv4;
                                    com.lagradost.cloudstream3.SearchResponse videoItem2 = parseVideoItem(it3);
                                    if (videoItem2 != null) {
                                        destination$iv$iv4.add(videoItem2);
                                    }
                                }
                                java.lang.Iterable $this$filter$iv = (java.util.List) destination$iv$iv4;
                                java.util.Collection destination$iv$iv5 = new java.util.ArrayList();
                                for (java.lang.Object element$iv$iv : $this$filter$iv) {
                                    com.lagradost.cloudstream3.SearchResponse it4 = (com.lagradost.cloudstream3.SearchResponse) element$iv$iv;
                                    if (!kotlin.jvm.internal.Intrinsics.areEqual(it4.getUrl(), url2)) {
                                        destination$iv$iv5.add(element$iv$iv);
                                    }
                                }
                                java.util.ArrayList arrayList2 = (java.util.List) destination$iv$iv5;
                                if (arrayList2.isEmpty()) {
                                    arrayList2 = null;
                                }
                                recommendations.element = arrayList2;
                                java.lang.String name4 = getName();
                                java.lang.StringBuilder sbAppend3 = new java.lang.StringBuilder().append("Found ");
                                java.util.List list3 = (java.util.List) recommendations.element;
                                android.util.Log.d(name4, sbAppend3.append(list3 != null ? list3.size() : 0).append(" recommendations using broader HTML selector.").toString());
                            }
                            break;
                        } catch (java.lang.Exception e3) {
                            e = e3;
                            initialData2 = initialData;
                        }
                        java.lang.String name22 = getName();
                        java.lang.StringBuilder sbAppend4 = new java.lang.StringBuilder().append("Final recommendations count being added to LoadResponse: ");
                        java.util.List list4 = (java.util.List) recommendations.element;
                        android.util.Log.i(name22, sbAppend4.append(list4 != null ? kotlin.coroutines.jvm.internal.Boxing.boxInt(list4.size()) : null).toString());
                        com.lagradost.cloudstream3.TvType tvType2 = com.lagradost.cloudstream3.TvType.NSFW;
                        Xhamster.Xhamster.AnonymousClass7 anonymousClass72 = new Xhamster.Xhamster.AnonymousClass7(plot, fixedPoster, tags, recommendations, null);
                        c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                        c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(htmlContent);
                        c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialData2);
                        c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
                        c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(plot);
                        c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster2);
                        c000012.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedPoster);
                        c000012.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(tags);
                        c000012.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
                        c000012.label = 2;
                        $result = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType2, url2, anonymousClass72, c000012);
                        return $result == obj ? obj : $result;
                    } catch (java.lang.Exception e4) {
                        e = e4;
                        android.util.Log.e(getName(), "Failed to load URL " + url2 + ": " + e.getMessage());
                        return null;
                    }
                } catch (java.lang.Exception e5) {
                    e = e5;
                    url2 = url;
                    android.util.Log.e(getName(), "Failed to load URL " + url2 + ": " + e.getMessage());
                    return null;
                }
            case 1:
                java.lang.String url3 = (java.lang.String) c000012.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result);
                    url2 = url3;
                    obj = coroutine_suspended;
                    document = ((com.lagradost.nicehttp.NiceResponse) $result).getDocument();
                    java.lang.String htmlContent2 = document.html();
                    initialData = getInitialsJson(htmlContent2);
                    if (initialData != null) {
                        org.jsoup.nodes.Element elementSelectFirst5 = document.selectFirst("meta[property=og:title]");
                        if (elementSelectFirst5 == null) {
                        }
                        if (title != null) {
                        }
                        if (initialData != null) {
                            org.jsoup.nodes.Element elementSelectFirst32 = document.selectFirst("div.video-description p[itemprop=description]");
                            if (elementSelectFirst32 != null) {
                                java.lang.String plot2 = string;
                                if (initialData != null) {
                                    if (initialData != null) {
                                        if (thumbBig == null) {
                                        }
                                        java.lang.String poster22 = thumbBig;
                                        java.lang.String fixedPoster2 = com.lagradost.cloudstream3.MainAPIKt.fixUrlNull(this, poster22);
                                        if (initialData != null) {
                                            java.lang.Iterable $this$mapNotNull$iv5 = document.select("section[data-role=video-tags] a.item");
                                            java.util.Collection destination$iv$iv6 = new java.util.ArrayList();
                                            while (r18.hasNext()) {
                                            }
                                            collection = (java.util.List) destination$iv$iv6;
                                            if (collection.isEmpty()) {
                                            }
                                            tags = collection;
                                            recommendations = new kotlin.jvm.internal.Ref.ObjectRef();
                                            java.lang.Iterable $this$mapNotNull$iv32 = document.select("div[data-role=video-related] div.mobile-video-thumb");
                                            java.util.Collection destination$iv$iv32 = new java.util.ArrayList();
                                            while (r19.hasNext()) {
                                                break;
                                            }
                                            initialData2 = initialData;
                                            arrayList = (java.util.List) destination$iv$iv32;
                                            if (arrayList.isEmpty()) {
                                            }
                                            recommendations.element = arrayList;
                                            java.lang.String name32 = getName();
                                            java.lang.StringBuilder sbAppend22 = new java.lang.StringBuilder().append("Found ");
                                            java.util.List list22 = (java.util.List) recommendations.element;
                                            android.util.Log.d(name32, sbAppend22.append(list22 == null ? list22.size() : 0).append(" recommendations using HTML selector '").append("div[data-role=video-related] div.mobile-video-thumb").append("'.").toString());
                                            if (recommendations.element == null) {
                                            }
                                            java.lang.String name222 = getName();
                                            java.lang.StringBuilder sbAppend42 = new java.lang.StringBuilder().append("Final recommendations count being added to LoadResponse: ");
                                            java.util.List list42 = (java.util.List) recommendations.element;
                                            android.util.Log.i(name222, sbAppend42.append(list42 != null ? kotlin.coroutines.jvm.internal.Boxing.boxInt(list42.size()) : null).toString());
                                            com.lagradost.cloudstream3.TvType tvType22 = com.lagradost.cloudstream3.TvType.NSFW;
                                            Xhamster.Xhamster.AnonymousClass7 anonymousClass722 = new Xhamster.Xhamster.AnonymousClass7(plot2, fixedPoster2, tags, recommendations, null);
                                            c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                                            c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                            c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(htmlContent2);
                                            c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialData2);
                                            c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(title);
                                            c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(plot2);
                                            c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(poster22);
                                            c000012.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedPoster2);
                                            c000012.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(tags);
                                            c000012.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(recommendations);
                                            c000012.label = 2;
                                            $result = com.lagradost.cloudstream3.MainAPIKt.newMovieLoadResponse(this, title, url2, tvType22, url2, anonymousClass722, c000012);
                                            if ($result == obj) {
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (java.lang.Exception e6) {
                    e = e6;
                    url2 = url3;
                    android.util.Log.e(getName(), "Failed to load URL " + url2 + ": " + e.getMessage());
                    return null;
                }
            case 2:
                kotlin.ResultKt.throwOnFailure($result);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: Xhamster.Xhamster$load$7, reason: invalid class name */
    /* JADX INFO: compiled from: Xhamster.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/MovieLoadResponse;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "Xhamster.Xhamster$load$7", f = "Xhamster.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass7 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.MovieLoadResponse, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $fixedPoster;
        final /* synthetic */ java.lang.String $plot;
        final /* synthetic */ kotlin.jvm.internal.Ref.ObjectRef<java.util.List<com.lagradost.cloudstream3.SearchResponse>> $recommendations;
        final /* synthetic */ java.util.List<java.lang.String> $tags;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass7(java.lang.String str, java.lang.String str2, java.util.List<java.lang.String> list, kotlin.jvm.internal.Ref.ObjectRef<java.util.List<com.lagradost.cloudstream3.SearchResponse>> objectRef, kotlin.coroutines.Continuation<? super Xhamster.Xhamster.AnonymousClass7> continuation) {
            super(2, continuation);
            this.$plot = str;
            this.$fixedPoster = str2;
            this.$tags = list;
            this.$recommendations = objectRef;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass7 = new Xhamster.Xhamster.AnonymousClass7(this.$plot, this.$fixedPoster, this.$tags, this.$recommendations, continuation);
            anonymousClass7.L$0 = obj;
            return anonymousClass7;
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
                    $this$newMovieLoadResponse.setPlot(this.$plot);
                    $this$newMovieLoadResponse.setPosterUrl(this.$fixedPoster);
                    $this$newMovieLoadResponse.setTags(this.$tags);
                    $this$newMovieLoadResponse.setRecommendations((java.util.List) this.$recommendations.element);
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }

    /* JADX WARN: Code restructure failed: missing block: B:166:0x0591, code lost:
    
        r18 = r15;
        kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(r35.getName(), "MP4 source item missing quality or url: " + r0));
        r19 = r34;
        r21 = r6;
        r7 = r7;
        r11 = r11;
        r6 = r5;
        r2 = r33;
        r5 = r4;
        r4 = r3;
        r3 = r35;
        r8 = r8;
     */
    /* JADX WARN: Removed duplicated region for block: B:102:0x059f  */
    /* JADX WARN: Removed duplicated region for block: B:106:0x05d1  */
    /* JADX WARN: Removed duplicated region for block: B:132:0x06a1  */
    /* JADX WARN: Removed duplicated region for block: B:135:0x06bc  */
    /* JADX WARN: Removed duplicated region for block: B:35:0x01fd  */
    /* JADX WARN: Removed duplicated region for block: B:37:0x020f  */
    /* JADX WARN: Removed duplicated region for block: B:60:0x02c8 A[Catch: Exception -> 0x0304, TRY_LEAVE, TryCatch #8 {Exception -> 0x0304, blocks: (B:57:0x02bb, B:58:0x02c2, B:60:0x02c8), top: B:162:0x02bb }] */
    /* JADX WARN: Removed duplicated region for block: B:75:0x03ba A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:76:0x03bb  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /* JADX WARN: Removed duplicated region for block: B:81:0x03fd  */
    /* JADX WARN: Removed duplicated region for block: B:88:0x0421  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:98:0x0518 -> B:99:0x0535). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object loadLinks(@org.jetbrains.annotations.NotNull java.lang.String data, boolean isCasting, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation) {
        Xhamster.Xhamster.C00011 c00011;
        java.lang.Object $result;
        java.lang.Object obj;
        java.lang.String data2;
        boolean isCasting2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        org.jsoup.nodes.Document document;
        Xhamster.InitialsJson initialsJson;
        java.lang.String data3;
        java.lang.String sourceName;
        Xhamster.VideoSources sources;
        Xhamster.InitialsJson initialData;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks;
        Xhamster.HlsSources hls;
        Xhamster.HlsSource h264;
        java.lang.String m3u8Url;
        java.lang.String m3u8Url2;
        java.lang.String fixedM3u8Url;
        java.lang.String m3u8Url3;
        java.lang.String sourceName2;
        Xhamster.VideoSources sources2;
        Xhamster.InitialsJson initialData2;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks2;
        int i;
        Xhamster.VideoSources sources3;
        java.lang.Object objGenerateM3u8$default;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function15;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks3;
        java.lang.String sourceName3;
        java.lang.String fixedM3u8Url2;
        java.lang.String data4;
        boolean isCasting3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16;
        Xhamster.VideoSources sources4;
        Xhamster.InitialsJson initialData3;
        java.lang.String m3u8Url4;
        int i2;
        Xhamster.InitialsJson initialData4;
        Xhamster.VideoSources sources5;
        boolean z;
        java.lang.Object objNewExtractorLink$default;
        java.lang.String fixedM3u8Url3;
        boolean isCasting4;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks4;
        java.lang.String sourceName4;
        java.lang.String sourceName5;
        int i3;
        java.util.Iterator it;
        boolean isCasting5;
        java.lang.String str;
        Xhamster.Xhamster xhamster;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation2;
        Xhamster.StandardSources standard;
        java.lang.Iterable h2642;
        java.util.Iterator it2;
        java.lang.String sourceName6;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function18;
        Xhamster.Xhamster.C00011 c000112;
        boolean isCasting6;
        java.lang.Object obj2;
        int $i$f$forEach;
        java.lang.Iterable $this$forEach$iv;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation3;
        Xhamster.XPlayerSettings xplayerSettings;
        Xhamster.Xhamster xhamster2;
        Xhamster.Subtitles subtitles;
        java.lang.Iterable $this$forEach$iv2;
        Xhamster.Xhamster xhamster3;
        Xhamster.InitialsJson initialData5;
        java.lang.String data5;
        Xhamster.VideoSources sources6;
        org.jsoup.nodes.Document document2;
        java.lang.Iterable $this$forEach$iv3;
        Xhamster.VideoSources sources7;
        java.lang.String data6;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks5;
        Xhamster.InitialsJson initialData6;
        Xhamster.Xhamster xhamster4;
        Xhamster.Xhamster.C00011 c000113;
        kotlin.jvm.internal.Ref.BooleanRef foundLinks6;
        java.lang.Object $result2;
        java.lang.String sourceName7;
        org.jsoup.nodes.Document document3;
        int i4;
        java.lang.String qualityLabel;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19;
        java.lang.Object element$iv;
        Xhamster.Xhamster xhamster5 = this;
        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation4 = continuation;
        if (continuation4 instanceof Xhamster.Xhamster.C00011) {
            c00011 = (Xhamster.Xhamster.C00011) continuation4;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
            } else {
                c00011 = xhamster5.new C00011(continuation4);
            }
        }
        Xhamster.Xhamster.C00011 c000114 = c00011;
        java.lang.Object $result3 = c000114.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000114.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result3);
                android.util.Log.d(xhamster5.getName(), "LoadLinks started for: " + data);
                try {
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    c000114.L$0 = data;
                    c000114.L$1 = function1;
                    c000114.L$2 = function12;
                    c000114.Z$0 = isCasting;
                    c000114.label = 1;
                    $result = $result3;
                    obj = coroutine_suspended;
                    try {
                        $result3 = com.lagradost.nicehttp.Requests.get$default(app, data, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000114, 4094, (java.lang.Object) null);
                        c000114 = c000114;
                        if ($result3 == obj) {
                            return obj;
                        }
                        data2 = data;
                        isCasting2 = isCasting;
                        function13 = function1;
                        function14 = function12;
                        try {
                            document = ((com.lagradost.nicehttp.NiceResponse) $result3).getDocument();
                            initialsJson = getInitialsJson(document.html());
                            if (initialsJson != null) {
                                Xhamster.Xhamster $this$loadLinks_u24lambda_u240 = this;
                                android.util.Log.e($this$loadLinks_u24lambda_u240.getName(), "Failed to parse JSON for loadLinks.");
                                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                            }
                            kotlin.jvm.internal.Ref.BooleanRef foundLinks7 = new kotlin.jvm.internal.Ref.BooleanRef();
                            Xhamster.XPlayerSettings xplayerSettings2 = initialsJson.getXplayerSettings();
                            Xhamster.VideoSources sources8 = xplayerSettings2 != null ? xplayerSettings2.getSources() : null;
                            java.lang.String sourceName8 = getName();
                            if (sources8 != null && (hls = sources8.getHls()) != null && (h264 = hls.getH264()) != null && (m3u8Url = h264.getUrl()) != null) {
                                java.lang.String fixedM3u8Url4 = com.lagradost.cloudstream3.MainAPIKt.fixUrl(this, m3u8Url);
                                android.util.Log.d(getName(), "Found HLS url: " + fixedM3u8Url4);
                                try {
                                    com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                                    c000114.L$0 = data2;
                                    c000114.L$1 = function13;
                                    c000114.L$2 = function14;
                                    c000114.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                    c000114.L$4 = initialsJson;
                                    c000114.L$5 = foundLinks7;
                                    c000114.L$6 = sources8;
                                    c000114.L$7 = sourceName8;
                                    c000114.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8Url);
                                    c000114.L$9 = fixedM3u8Url4;
                                    c000114.Z$0 = isCasting2;
                                    c000114.I$0 = 0;
                                    c000114.label = 2;
                                    sources3 = sources8;
                                    Xhamster.Xhamster.C00011 c000115 = c000114;
                                    fixedM3u8Url = fixedM3u8Url4;
                                    m3u8Url2 = m3u8Url;
                                    try {
                                        objGenerateM3u8$default = com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion, sourceName8, fixedM3u8Url, data2, (java.lang.Integer) null, (java.util.Map) null, (java.lang.String) null, c000115, 56, (java.lang.Object) null);
                                        c000114 = c000115;
                                    } catch (java.lang.Exception e) {
                                        e = e;
                                        c000114 = c000115;
                                        m3u8Url3 = data2;
                                        sourceName2 = sourceName8;
                                        sources2 = sources3;
                                        initialData2 = initialsJson;
                                        foundLinks2 = foundLinks7;
                                        i = 0;
                                        java.lang.Exception e2 = e;
                                        android.util.Log.e(getName(), "M3u8Helper failed: " + e2.getMessage());
                                        Xhamster.Xhamster$loadLinks$2$2 xhamster$loadLinks$2$2 = new Xhamster.Xhamster$loadLinks$2$2(m3u8Url3, null);
                                        c000114.L$0 = m3u8Url3;
                                        c000114.L$1 = function13;
                                        c000114.L$2 = function14;
                                        c000114.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                        c000114.L$4 = initialData2;
                                        c000114.L$5 = foundLinks2;
                                        c000114.L$6 = sources2;
                                        c000114.L$7 = sourceName2;
                                        c000114.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8Url2);
                                        c000114.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedM3u8Url);
                                        c000114.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(e2);
                                        c000114.L$11 = function14;
                                        c000114.Z$0 = isCasting2;
                                        c000114.I$0 = i;
                                        c000114.label = 3;
                                        kotlin.jvm.internal.Ref.BooleanRef foundLinks8 = foundLinks2;
                                        initialData4 = initialData2;
                                        sources5 = sources2;
                                        java.lang.String data7 = m3u8Url3;
                                        z = true;
                                        objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(sourceName2, sourceName2 + " HLS", fixedM3u8Url, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, xhamster$loadLinks$2$2, c000114, 8, (java.lang.Object) null);
                                        if (objNewExtractorLink$default == obj) {
                                        }
                                    }
                                } catch (java.lang.Exception e3) {
                                    e = e3;
                                    m3u8Url2 = m3u8Url;
                                    fixedM3u8Url = fixedM3u8Url4;
                                    m3u8Url3 = data2;
                                    sourceName2 = sourceName8;
                                    sources2 = sources8;
                                    initialData2 = initialsJson;
                                    foundLinks2 = foundLinks7;
                                    i = 0;
                                }
                                if (objGenerateM3u8$default == obj) {
                                    return obj;
                                }
                                function15 = function13;
                                foundLinks3 = foundLinks7;
                                sourceName3 = sourceName8;
                                fixedM3u8Url2 = fixedM3u8Url;
                                data4 = data2;
                                isCasting3 = isCasting2;
                                function16 = function14;
                                sources4 = sources3;
                                initialData3 = initialsJson;
                                m3u8Url4 = m3u8Url2;
                                i2 = 0;
                                $result3 = objGenerateM3u8$default;
                                try {
                                    int $i$f$forEach2 = 0;
                                    it = ((java.lang.Iterable) $result3).iterator();
                                    while (it.hasNext()) {
                                        java.lang.Object element$iv2 = it.next();
                                        com.lagradost.cloudstream3.utils.ExtractorLink link = (com.lagradost.cloudstream3.utils.ExtractorLink) element$iv2;
                                        int $i$f$forEach3 = $i$f$forEach2;
                                        function16.invoke(link);
                                        java.util.Iterator it3 = it;
                                        try {
                                            foundLinks3.element = true;
                                            it = it3;
                                            $i$f$forEach2 = $i$f$forEach3;
                                        } catch (java.lang.Exception e4) {
                                            e = e4;
                                            fixedM3u8Url = fixedM3u8Url2;
                                            m3u8Url2 = m3u8Url4;
                                            m3u8Url3 = data4;
                                            sources2 = sources4;
                                            isCasting2 = isCasting3;
                                            initialData2 = initialData3;
                                            function14 = function16;
                                            sourceName2 = sourceName3;
                                            i = i2;
                                            foundLinks2 = foundLinks3;
                                            function13 = function15;
                                            java.lang.Exception e22 = e;
                                            android.util.Log.e(getName(), "M3u8Helper failed: " + e22.getMessage());
                                            Xhamster.Xhamster$loadLinks$2$2 xhamster$loadLinks$2$22 = new Xhamster.Xhamster$loadLinks$2$2(m3u8Url3, null);
                                            c000114.L$0 = m3u8Url3;
                                            c000114.L$1 = function13;
                                            c000114.L$2 = function14;
                                            c000114.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                            c000114.L$4 = initialData2;
                                            c000114.L$5 = foundLinks2;
                                            c000114.L$6 = sources2;
                                            c000114.L$7 = sourceName2;
                                            c000114.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8Url2);
                                            c000114.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedM3u8Url);
                                            c000114.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(e22);
                                            c000114.L$11 = function14;
                                            c000114.Z$0 = isCasting2;
                                            c000114.I$0 = i;
                                            c000114.label = 3;
                                            kotlin.jvm.internal.Ref.BooleanRef foundLinks82 = foundLinks2;
                                            initialData4 = initialData2;
                                            sources5 = sources2;
                                            java.lang.String data72 = m3u8Url3;
                                            z = true;
                                            objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(sourceName2, sourceName2 + " HLS", fixedM3u8Url, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, xhamster$loadLinks$2$22, c000114, 8, (java.lang.Object) null);
                                            if (objNewExtractorLink$default == obj) {
                                            }
                                        }
                                        break;
                                    }
                                    data3 = data4;
                                    isCasting5 = isCasting3;
                                    sourceName = sourceName3;
                                    foundLinks = foundLinks3;
                                    initialData = initialData3;
                                    function13 = function15;
                                    function14 = function16;
                                } catch (java.lang.Exception e5) {
                                    e = e5;
                                    fixedM3u8Url = fixedM3u8Url2;
                                    m3u8Url2 = m3u8Url4;
                                    m3u8Url3 = data4;
                                    sources2 = sources4;
                                    isCasting2 = isCasting3;
                                    initialData2 = initialData3;
                                    function14 = function16;
                                    sourceName2 = sourceName3;
                                    i = i2;
                                    foundLinks2 = foundLinks3;
                                    function13 = function15;
                                }
                                sources = sources4;
                                isCasting2 = isCasting5;
                                if (sources != null) {
                                }
                                str = null;
                                kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No Standard H264 sources found in JSON."));
                                xhamster = this;
                                continuation2 = continuation;
                                xplayerSettings = initialData.getXplayerSettings();
                                if (xplayerSettings != null) {
                                }
                                if (!foundLinks.element) {
                                }
                                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
                            }
                            kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No HLS source found in JSON."));
                            data3 = data2;
                            sourceName = sourceName8;
                            sources = sources8;
                            initialData = initialsJson;
                            foundLinks = foundLinks7;
                            if (sources != null || (standard = sources.getStandard()) == null || (h2642 = standard.getH264()) == null) {
                                str = null;
                                kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No Standard H264 sources found in JSON."));
                                xhamster = this;
                                continuation2 = continuation;
                                xplayerSettings = initialData.getXplayerSettings();
                                if (xplayerSettings != null || (subtitles = xplayerSettings.getSubtitles()) == null || ($this$forEach$iv2 = subtitles.getTracks()) == null) {
                                    xhamster2 = xhamster;
                                    kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(xhamster2.getName(), "No subtitle tracks found in JSON."));
                                } else {
                                    for (java.lang.Object element$iv3 : $this$forEach$iv2) {
                                        kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation5 = continuation2;
                                        Xhamster.SubtitleTrack track = (Xhamster.SubtitleTrack) element$iv3;
                                        Xhamster.SubtitleUrls urls = track.getUrls();
                                        java.lang.String subUrl = urls != null ? urls.getVtt() : str;
                                        java.lang.String lang = track.getLang();
                                        if (lang == null && (lang = track.getLabel()) == null) {
                                            lang = "Unknown";
                                        }
                                        java.lang.String lang2 = lang;
                                        if (subUrl != null) {
                                            xhamster3 = xhamster;
                                            initialData5 = initialData;
                                            java.lang.String fixedSubUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrl(xhamster, subUrl);
                                            java.lang.String name = xhamster3.getName();
                                            data5 = data3;
                                            java.lang.StringBuilder sbAppend = new java.lang.StringBuilder().append("Found subtitle: Lang=").append(lang2);
                                            sources6 = sources;
                                            android.util.Log.d(name, sbAppend.append(", URL=").append(fixedSubUrl).toString());
                                            try {
                                                function13.invoke(new com.lagradost.cloudstream3.SubtitleFile(lang2, fixedSubUrl));
                                            } catch (java.lang.Exception e6) {
                                                e6.printStackTrace();
                                            }
                                        } else {
                                            xhamster3 = xhamster;
                                            initialData5 = initialData;
                                            data5 = data3;
                                            sources6 = sources;
                                            kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(xhamster3.getName(), "Subtitle track missing VTT url: " + track));
                                        }
                                        continuation2 = continuation5;
                                        initialData = initialData5;
                                        sources = sources6;
                                        xhamster = xhamster3;
                                        data3 = data5;
                                    }
                                    xhamster2 = xhamster;
                                }
                                if (!foundLinks.element) {
                                    android.util.Log.w(xhamster2.getName(), "No video links (M3U8 or MP4) were found.");
                                }
                                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
                            }
                            java.lang.Iterable $this$forEach$iv4 = h2642;
                            it2 = $this$forEach$iv4.iterator();
                            sourceName6 = sourceName;
                            function18 = function14;
                            c000112 = c000114;
                            isCasting6 = isCasting2;
                            obj2 = obj;
                            $i$f$forEach = 0;
                            xhamster = this;
                            $this$forEach$iv = $this$forEach$iv4;
                            continuation3 = continuation;
                            if (!it2.hasNext()) {
                                java.lang.Object element$iv4 = it2.next();
                                kotlin.coroutines.Continuation<? super java.lang.Boolean> continuation6 = continuation3;
                                Xhamster.StandardSourceQuality qualitySource = (Xhamster.StandardSourceQuality) element$iv4;
                                java.lang.Iterable $this$forEach$iv5 = $this$forEach$iv;
                                java.lang.String qualityLabel2 = qualitySource.getQuality();
                                Xhamster.Xhamster xhamster6 = xhamster;
                                java.lang.String videoUrl = qualitySource.getUrl();
                                if (qualityLabel2 == null || videoUrl == null) {
                                    document2 = document;
                                    kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(xhamster6.getName(), "MP4 source item missing quality or url: " + qualitySource));
                                    $this$forEach$iv3 = $this$forEach$iv5;
                                    sources7 = sources;
                                    obj2 = obj2;
                                    sourceName6 = sourceName6;
                                    data6 = data3;
                                    continuation4 = continuation6;
                                    foundLinks5 = foundLinks;
                                    initialData6 = initialData;
                                    xhamster4 = xhamster6;
                                    c000112 = c000112;
                                    continuation3 = continuation4;
                                    xhamster = xhamster4;
                                    initialData = initialData6;
                                    foundLinks = foundLinks5;
                                    data3 = data6;
                                    document = document2;
                                    $this$forEach$iv = $this$forEach$iv3;
                                    sources = sources7;
                                    if (!it2.hasNext()) {
                                        continuation2 = continuation3;
                                        str = null;
                                        xplayerSettings = initialData.getXplayerSettings();
                                        if (xplayerSettings != null) {
                                            xhamster2 = xhamster;
                                            kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(xhamster2.getName(), "No subtitle tracks found in JSON."));
                                        }
                                        if (!foundLinks.element) {
                                        }
                                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
                                    }
                                } else {
                                    Xhamster.VideoSources sources9 = sources;
                                    java.lang.String fixedVideoUrl = com.lagradost.cloudstream3.MainAPIKt.fixUrl(xhamster6, videoUrl);
                                    java.lang.Integer intOrNull = kotlin.text.StringsKt.toIntOrNull(kotlin.text.StringsKt.replace$default(qualityLabel2, "p", "", false, 4, (java.lang.Object) null));
                                    int quality = intOrNull != null ? intOrNull.intValue() : com.lagradost.cloudstream3.utils.Qualities.Unknown.getValue();
                                    org.jsoup.nodes.Document document4 = document;
                                    java.lang.Object obj3 = obj2;
                                    android.util.Log.d(xhamster6.getName(), "Found MP4 link: " + qualityLabel2 + " - " + fixedVideoUrl);
                                    java.lang.String str2 = sourceName6 + " MP4 " + qualityLabel2;
                                    Xhamster.Xhamster$loadLinks$3$1 xhamster$loadLinks$3$1 = new Xhamster.Xhamster$loadLinks$3$1(data3, quality, null);
                                    c000112.L$0 = data3;
                                    c000112.L$1 = function13;
                                    c000112.L$2 = function18;
                                    c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document4);
                                    c000112.L$4 = initialData;
                                    c000112.L$5 = foundLinks;
                                    c000112.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(sources9);
                                    c000112.L$7 = sourceName6;
                                    c000112.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEach$iv5);
                                    c000112.L$9 = it2;
                                    c000112.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv4);
                                    c000112.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(qualitySource);
                                    c000112.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(qualityLabel2);
                                    c000112.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl);
                                    c000112.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedVideoUrl);
                                    c000112.L$15 = function18;
                                    c000112.Z$0 = isCasting6;
                                    c000112.I$0 = $i$f$forEach;
                                    c000112.I$1 = 0;
                                    c000112.I$2 = quality;
                                    c000112.label = 4;
                                    c000113 = c000112;
                                    java.lang.String sourceName9 = sourceName6;
                                    java.lang.Object objNewExtractorLink$default2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(sourceName9, str2, fixedVideoUrl, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, xhamster$loadLinks$3$1, c000113, 8, (java.lang.Object) null);
                                    if (objNewExtractorLink$default2 == obj3) {
                                        return obj3;
                                    }
                                    kotlin.jvm.internal.Ref.BooleanRef booleanRef = foundLinks;
                                    $result3 = objNewExtractorLink$default2;
                                    foundLinks6 = booleanRef;
                                    obj2 = obj3;
                                    $result2 = $result;
                                    sourceName7 = sourceName9;
                                    document3 = document4;
                                    $this$forEach$iv3 = $this$forEach$iv5;
                                    i4 = 0;
                                    qualityLabel = qualityLabel2;
                                    function19 = function18;
                                    element$iv = qualitySource;
                                    continuation4 = continuation6;
                                    xhamster5 = xhamster6;
                                    sources7 = sources9;
                                    function19.invoke($result3);
                                    foundLinks6.element = true;
                                    initialData6 = initialData;
                                    document2 = document3;
                                    xhamster4 = xhamster5;
                                    sourceName6 = sourceName7;
                                    $result = $result2;
                                    data6 = data3;
                                    foundLinks5 = foundLinks6;
                                    c000112 = c000113;
                                    continuation3 = continuation4;
                                    xhamster = xhamster4;
                                    initialData = initialData6;
                                    foundLinks = foundLinks5;
                                    data3 = data6;
                                    document = document2;
                                    $this$forEach$iv = $this$forEach$iv3;
                                    sources = sources7;
                                    if (!it2.hasNext()) {
                                    }
                                }
                            }
                        } catch (java.lang.Exception e7) {
                            e = e7;
                            android.util.Log.e(getName(), "Failed to get document for loadLinks: " + e.getMessage());
                            return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                        }
                    } catch (java.lang.Exception e8) {
                        e = e8;
                        android.util.Log.e(getName(), "Failed to get document for loadLinks: " + e.getMessage());
                        return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                    }
                } catch (java.lang.Exception e9) {
                    e = e9;
                }
                break;
            case 1:
                boolean isCasting7 = c000114.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function110 = (kotlin.jvm.functions.Function1) c000114.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) c000114.L$1;
                java.lang.String data8 = (java.lang.String) c000114.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result3);
                    $result = $result3;
                    obj = coroutine_suspended;
                    isCasting2 = isCasting7;
                    function14 = function110;
                    function13 = function111;
                    data2 = data8;
                    document = ((com.lagradost.nicehttp.NiceResponse) $result3).getDocument();
                    initialsJson = getInitialsJson(document.html());
                    if (initialsJson != null) {
                    }
                } catch (java.lang.Exception e10) {
                    e = e10;
                    android.util.Log.e(getName(), "Failed to get document for loadLinks: " + e.getMessage());
                    return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(false);
                }
                break;
            case 2:
                i2 = c000114.I$0;
                isCasting3 = c000114.Z$0;
                fixedM3u8Url2 = (java.lang.String) c000114.L$9;
                m3u8Url4 = (java.lang.String) c000114.L$8;
                sourceName3 = (java.lang.String) c000114.L$7;
                sources4 = (Xhamster.VideoSources) c000114.L$6;
                foundLinks3 = (kotlin.jvm.internal.Ref.BooleanRef) c000114.L$5;
                initialData3 = (Xhamster.InitialsJson) c000114.L$4;
                document = (org.jsoup.nodes.Document) c000114.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) c000114.L$2;
                function15 = (kotlin.jvm.functions.Function1) c000114.L$1;
                data4 = (java.lang.String) c000114.L$0;
                try {
                    kotlin.ResultKt.throwOnFailure($result3);
                    $result = $result3;
                    obj = coroutine_suspended;
                    function16 = function112;
                    int $i$f$forEach22 = 0;
                    it = ((java.lang.Iterable) $result3).iterator();
                    while (it.hasNext()) {
                        break;
                    }
                    data3 = data4;
                    isCasting5 = isCasting3;
                    sourceName = sourceName3;
                    foundLinks = foundLinks3;
                    initialData = initialData3;
                    function13 = function15;
                    function14 = function16;
                } catch (java.lang.Exception e11) {
                    e = e11;
                    m3u8Url3 = data4;
                    sources2 = sources4;
                    isCasting2 = isCasting3;
                    initialData2 = initialData3;
                    function14 = function112;
                    m3u8Url2 = m3u8Url4;
                    $result = $result3;
                    obj = coroutine_suspended;
                    fixedM3u8Url = fixedM3u8Url2;
                    sourceName2 = sourceName3;
                    i = i2;
                    foundLinks2 = foundLinks3;
                    function13 = function15;
                    java.lang.Exception e222 = e;
                    android.util.Log.e(getName(), "M3u8Helper failed: " + e222.getMessage());
                    Xhamster.Xhamster$loadLinks$2$2 xhamster$loadLinks$2$222 = new Xhamster.Xhamster$loadLinks$2$2(m3u8Url3, null);
                    c000114.L$0 = m3u8Url3;
                    c000114.L$1 = function13;
                    c000114.L$2 = function14;
                    c000114.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                    c000114.L$4 = initialData2;
                    c000114.L$5 = foundLinks2;
                    c000114.L$6 = sources2;
                    c000114.L$7 = sourceName2;
                    c000114.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8Url2);
                    c000114.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fixedM3u8Url);
                    c000114.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(e222);
                    c000114.L$11 = function14;
                    c000114.Z$0 = isCasting2;
                    c000114.I$0 = i;
                    c000114.label = 3;
                    kotlin.jvm.internal.Ref.BooleanRef foundLinks822 = foundLinks2;
                    initialData4 = initialData2;
                    sources5 = sources2;
                    java.lang.String data722 = m3u8Url3;
                    z = true;
                    objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(sourceName2, sourceName2 + " HLS", fixedM3u8Url, (com.lagradost.cloudstream3.utils.ExtractorLinkType) null, xhamster$loadLinks$2$222, c000114, 8, (java.lang.Object) null);
                    if (objNewExtractorLink$default == obj) {
                        return obj;
                    }
                    java.lang.String str3 = fixedM3u8Url;
                    $result3 = objNewExtractorLink$default;
                    fixedM3u8Url3 = str3;
                    isCasting4 = isCasting2;
                    function17 = function14;
                    foundLinks4 = foundLinks822;
                    sourceName4 = sourceName2;
                    sourceName5 = data722;
                    i3 = i;
                    function17.invoke($result3);
                    foundLinks4.element = z;
                    isCasting5 = isCasting4;
                    foundLinks = foundLinks4;
                    sourceName = sourceName4;
                    sources4 = sources5;
                    initialData = initialData4;
                    data3 = sourceName5;
                    sources = sources4;
                    isCasting2 = isCasting5;
                    if (sources != null) {
                    }
                    str = null;
                    kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No Standard H264 sources found in JSON."));
                    xhamster = this;
                    continuation2 = continuation;
                    xplayerSettings = initialData.getXplayerSettings();
                    if (xplayerSettings != null) {
                    }
                    if (!foundLinks.element) {
                    }
                    return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
                }
                sources = sources4;
                isCasting2 = isCasting5;
                if (sources != null) {
                }
                str = null;
                kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No Standard H264 sources found in JSON."));
                xhamster = this;
                continuation2 = continuation;
                xplayerSettings = initialData.getXplayerSettings();
                if (xplayerSettings != null) {
                }
                if (!foundLinks.element) {
                }
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
            case 3:
                int i5 = c000114.I$0;
                isCasting4 = c000114.Z$0;
                function17 = (kotlin.jvm.functions.Function1) c000114.L$11;
                java.lang.String fixedM3u8Url5 = (java.lang.String) c000114.L$9;
                sourceName4 = (java.lang.String) c000114.L$7;
                Xhamster.VideoSources sources10 = (Xhamster.VideoSources) c000114.L$6;
                kotlin.jvm.internal.Ref.BooleanRef foundLinks9 = (kotlin.jvm.internal.Ref.BooleanRef) c000114.L$5;
                Xhamster.InitialsJson initialData7 = (Xhamster.InitialsJson) c000114.L$4;
                org.jsoup.nodes.Document document5 = (org.jsoup.nodes.Document) c000114.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function113 = (kotlin.jvm.functions.Function1) c000114.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function114 = (kotlin.jvm.functions.Function1) c000114.L$1;
                java.lang.String data9 = (java.lang.String) c000114.L$0;
                kotlin.ResultKt.throwOnFailure($result3);
                sourceName5 = data9;
                $result = $result3;
                obj = coroutine_suspended;
                fixedM3u8Url3 = fixedM3u8Url5;
                sources5 = sources10;
                foundLinks4 = foundLinks9;
                initialData4 = initialData7;
                i3 = i5;
                z = true;
                document = document5;
                function13 = function114;
                function14 = function113;
                function17.invoke($result3);
                foundLinks4.element = z;
                isCasting5 = isCasting4;
                foundLinks = foundLinks4;
                sourceName = sourceName4;
                sources4 = sources5;
                initialData = initialData4;
                data3 = sourceName5;
                sources = sources4;
                isCasting2 = isCasting5;
                if (sources != null) {
                }
                str = null;
                kotlin.coroutines.jvm.internal.Boxing.boxInt(android.util.Log.w(getName(), "No Standard H264 sources found in JSON."));
                xhamster = this;
                continuation2 = continuation;
                xplayerSettings = initialData.getXplayerSettings();
                if (xplayerSettings != null) {
                }
                if (!foundLinks.element) {
                }
                return kotlin.coroutines.jvm.internal.Boxing.boxBoolean(foundLinks.element);
            case 4:
                int i6 = c000114.I$2;
                int i7 = c000114.I$1;
                int $i$f$forEach4 = c000114.I$0;
                boolean isCasting8 = c000114.Z$0;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function115 = (kotlin.jvm.functions.Function1) c000114.L$15;
                java.lang.String qualityLabel3 = (java.lang.String) c000114.L$12;
                java.lang.Object qualitySource2 = (Xhamster.StandardSourceQuality) c000114.L$11;
                java.lang.Object obj4 = c000114.L$10;
                java.util.Iterator it4 = (java.util.Iterator) c000114.L$9;
                $this$forEach$iv3 = (java.lang.Iterable) c000114.L$8;
                sourceName7 = (java.lang.String) c000114.L$7;
                sources7 = (Xhamster.VideoSources) c000114.L$6;
                kotlin.jvm.internal.Ref.BooleanRef foundLinks10 = (kotlin.jvm.internal.Ref.BooleanRef) c000114.L$5;
                Xhamster.InitialsJson initialData8 = (Xhamster.InitialsJson) c000114.L$4;
                document3 = (org.jsoup.nodes.Document) c000114.L$3;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function116 = (kotlin.jvm.functions.Function1) c000114.L$2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function117 = (kotlin.jvm.functions.Function1) c000114.L$1;
                java.lang.String data10 = (java.lang.String) c000114.L$0;
                kotlin.ResultKt.throwOnFailure($result3);
                c000113 = c000114;
                qualityLabel = qualityLabel3;
                initialData = initialData8;
                function13 = function117;
                obj2 = coroutine_suspended;
                element$iv = qualitySource2;
                function19 = function115;
                data3 = data10;
                $result2 = $result3;
                $i$f$forEach = $i$f$forEach4;
                foundLinks6 = foundLinks10;
                function18 = function116;
                isCasting6 = isCasting8;
                i4 = i7;
                it2 = it4;
                function19.invoke($result3);
                foundLinks6.element = true;
                initialData6 = initialData;
                document2 = document3;
                xhamster4 = xhamster5;
                sourceName6 = sourceName7;
                $result = $result2;
                data6 = data3;
                foundLinks5 = foundLinks6;
                c000112 = c000113;
                continuation3 = continuation4;
                xhamster = xhamster4;
                initialData = initialData6;
                foundLinks = foundLinks5;
                data3 = data6;
                document = document2;
                $this$forEach$iv = $this$forEach$iv3;
                sources = sources7;
                if (!it2.hasNext()) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
