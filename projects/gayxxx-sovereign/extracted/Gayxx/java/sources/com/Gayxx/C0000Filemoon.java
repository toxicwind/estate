package com.Gayxx;

/* JADX INFO: renamed from: com.Gayxx.Filemoon, reason: case insensitive filesystem */
/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000<\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003JH\u0010\u000e\u001a\u00020\u000f2\u0006\u0010\u0010\u001a\u00020\u00052\b\u0010\u0011\u001a\u0004\u0018\u00010\u00052\u0012\u0010\u0012\u001a\u000e\u0012\u0004\u0012\u00020\u0014\u0012\u0004\u0012\u00020\u000f0\u00132\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0016\u0012\u0004\u0012\u00020\u000f0\u0013H\u0096@¢\u0006\u0002\u0010\u0017J\u0012\u0010\u0018\u001a\u0004\u0018\u00010\u00052\u0006\u0010\u0019\u001a\u00020\u001aH\u0002R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u001b"}, d2 = {"Lcom/Gayxx/Filemoon;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "unpackJs", "script", "Lorg/jsoup/nodes/Element;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/Filemoon\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,451:1\n1915#2,2:452\n1#3:454\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/Filemoon\n*L\n343#1:452,2\n*E\n"})
public class C0000Filemoon extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Filemoon";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://filemoon.sx";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.Gayxx.Filemoon$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.Filemoon", f = "Extractor.kt", i = {0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1}, l = {337, 339}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "subtitleCallback", "callback", "$this", "url", "referer", "subtitleCallback", "callback", "doc", "link"}, nl = {338, 343}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.C0000Filemoon.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.C0000Filemoon.getUrl$suspendImpl(com.Gayxx.C0000Filemoon.this, null, null, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.Nullable
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String str, @org.jetbrains.annotations.Nullable java.lang.String str2, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, @org.jetbrains.annotations.NotNull kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return getUrl$suspendImpl(this, str, str2, function1, function12, continuation);
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

    /* JADX WARN: Removed duplicated region for block: B:25:0x00ef  */
    /* JADX WARN: Removed duplicated region for block: B:27:0x00f2  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x015c A[LOOP:0: B:32:0x0156->B:34:0x015c, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gayxx.C0000Filemoon $this, java.lang.String url, java.lang.String referer, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.Gayxx.C0000Filemoon.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        com.Gayxx.C0000Filemoon $this2;
        java.lang.String url2;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        java.lang.Object obj2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.lang.String strUnpackJs;
        java.lang.String link;
        java.lang.Object objGenerateM3u8$default;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String strSubstringAfter$default;
        if (continuation instanceof com.Gayxx.C0000Filemoon.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.C0000Filemoon.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Gayxx.C0000Filemoon.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                anonymousClass12.L$4 = function12;
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                java.lang.Object obj3 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj3 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                function13 = function1;
                obj2 = obj3;
                function14 = function12;
                org.jsoup.nodes.Document doc = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                strUnpackJs = $this2.unpackJs((org.jsoup.nodes.Element) doc);
                link = null;
                if (strUnpackJs != null && (strSubstringAfter$default = kotlin.text.StringsKt.substringAfter$default(strUnpackJs, "file:\"", (java.lang.String) null, 2, (java.lang.Object) null)) != null) {
                    link = kotlin.text.StringsKt.substringBefore$default(strSubstringAfter$default, "\"", (java.lang.String) null, 2, (java.lang.Object) null);
                }
                com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                java.lang.String name = $this2.getName();
                if (link != null) {
                    return kotlin.Unit.INSTANCE;
                }
                java.lang.String str = $this2.getMainUrl() + '/';
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = function14;
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(doc);
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                anonymousClass12.label = 2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = function14;
                objGenerateM3u8$default = com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion, name, link, str, (java.lang.Integer) null, (java.util.Map) null, (java.lang.String) null, anonymousClass12, 56, (java.lang.Object) null);
                if (objGenerateM3u8$default == obj) {
                    return obj;
                }
                function15 = function16;
                java.lang.Iterable $this$forEach$iv = (java.lang.Iterable) objGenerateM3u8$default;
                for (java.lang.Object element$iv : $this$forEach$iv) {
                    function15.invoke(element$iv);
                }
                return kotlin.Unit.INSTANCE;
            case 1:
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$1;
                com.Gayxx.C0000Filemoon $this3 = (com.Gayxx.C0000Filemoon) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this3;
                obj = coroutine_suspended;
                function14 = function17;
                function13 = function18;
                referer2 = referer3;
                url2 = url3;
                obj2 = $result;
                org.jsoup.nodes.Document doc2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                strUnpackJs = $this2.unpackJs((org.jsoup.nodes.Element) doc2);
                link = null;
                if (strUnpackJs != null) {
                    link = kotlin.text.StringsKt.substringBefore$default(strSubstringAfter$default, "\"", (java.lang.String) null, 2, (java.lang.Object) null);
                }
                com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion2 = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                java.lang.String name2 = $this2.getName();
                if (link != null) {
                }
                break;
            case 2:
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.ResultKt.throwOnFailure($result);
                function15 = function19;
                objGenerateM3u8$default = $result;
                java.lang.Iterable $this$forEach$iv2 = (java.lang.Iterable) objGenerateM3u8$default;
                while (r11.hasNext()) {
                }
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private final java.lang.String unpackJs(org.jsoup.nodes.Element script) {
        java.lang.Object next;
        java.lang.String it;
        java.util.Iterator it2 = script.select("script").iterator();
        while (true) {
            if (!it2.hasNext()) {
                next = null;
                break;
            }
            next = it2.next();
            if (kotlin.text.StringsKt.contains$default(((org.jsoup.nodes.Element) next).data(), "eval(function(p,a,c,k,e,d)", false, 2, (java.lang.Object) null)) {
                break;
            }
        }
        org.jsoup.nodes.Element element = (org.jsoup.nodes.Element) next;
        if (element == null || (it = element.data()) == null) {
            return null;
        }
        return com.lagradost.cloudstream3.utils.ExtractorApiKt.getAndUnpack(it);
    }
}
