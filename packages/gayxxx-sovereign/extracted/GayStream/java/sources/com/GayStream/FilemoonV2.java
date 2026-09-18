package com.GayStream;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u00006\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003JH\u0010\u0011\u001a\u00020\u00122\u0006\u0010\u0013\u001a\u00020\u00052\b\u0010\u0014\u001a\u0004\u0018\u00010\u00052\u0012\u0010\u0015\u001a\u000e\u0012\u0004\u0012\u00020\u0017\u0012\u0004\u0012\u00020\u00120\u00162\u0012\u0010\u0018\u001a\u000e\u0012\u0004\u0012\u00020\u0019\u0012\u0004\u0012\u00020\u00120\u0016H\u0096@¢\u0006\u0002\u0010\u001aR\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u001b"}, d2 = {"Lcom/GayStream/FilemoonV2;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "url", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "GayStream"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractors.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractors.kt\ncom/GayStream/FilemoonV2\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,301:1\n1915#2,2:302\n*S KotlinDebug\n*F\n+ 1 Extractors.kt\ncom/GayStream/FilemoonV2\n*L\n242#1:302,2\n*E\n"})
public class FilemoonV2 extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Filemoon";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://filemoon.to";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.GayStream.FilemoonV2$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.GayStream.FilemoonV2", f = "Extractors.kt", i = {0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5}, l = {223, 237, 251, 263, 278, 285}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "initialResponse", "iframeSrcUrl", "fallbackScriptData", "unpackedScript", "videoUrl", "$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "initialResponse", "iframeSrcUrl", "iframeHeaders", "$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "initialResponse", "iframeSrcUrl", "iframeHeaders", "iframeResponse", "iframeScriptData", "unpackedScript", "videoUrl", "$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "initialResponse", "iframeSrcUrl", "iframeHeaders", "iframeResponse", "iframeScriptData", "unpackedScript", "videoUrl", "resolver", "$this", "url", "referer", "subtitleCallback", "callback", "defaultHeaders", "initialResponse", "iframeSrcUrl", "iframeHeaders", "iframeResponse", "iframeScriptData", "unpackedScript", "videoUrl", "resolver", "interceptedUrl"}, nl = {224, 242, 255, 295, 282, 295}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$12", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$12", "L$13", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$12", "L$13", "L$14"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
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
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.GayStream.FilemoonV2.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.GayStream.FilemoonV2.getUrl$suspendImpl(com.GayStream.FilemoonV2.this, null, null, null, null, (kotlin.coroutines.Continuation) this);
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

    public void setName(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.name = str;
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public void setMainUrl(@org.jetbrains.annotations.NotNull java.lang.String str) {
        this.mainUrl = str;
    }

    public boolean getRequiresReferer() {
        return this.requiresReferer;
    }

    /* JADX WARN: Removed duplicated region for block: B:105:0x051a  */
    /* JADX WARN: Removed duplicated region for block: B:111:0x05e2  */
    /* JADX WARN: Removed duplicated region for block: B:113:0x05e6  */
    /* JADX WARN: Removed duplicated region for block: B:119:0x0671  */
    /* JADX WARN: Removed duplicated region for block: B:24:0x029f  */
    /* JADX WARN: Removed duplicated region for block: B:25:0x02a7  */
    /* JADX WARN: Removed duplicated region for block: B:32:0x02b7  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x02bb  */
    /* JADX WARN: Removed duplicated region for block: B:66:0x0393 A[LOOP:0: B:64:0x038d->B:66:0x0393, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:71:0x03b8  */
    /* JADX WARN: Removed duplicated region for block: B:77:0x0441  */
    /* JADX WARN: Removed duplicated region for block: B:78:0x0446  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Removed duplicated region for block: B:81:0x044a  */
    /* JADX WARN: Removed duplicated region for block: B:84:0x0459  */
    /* JADX WARN: Removed duplicated region for block: B:90:0x047e  */
    /* JADX WARN: Removed duplicated region for block: B:97:0x0490  */
    /* JADX WARN: Removed duplicated region for block: B:99:0x0493  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.GayStream.FilemoonV2 $this, java.lang.String url, java.lang.String referer, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.GayStream.FilemoonV2.AnonymousClass1 anonymousClass1;
        java.lang.String str;
        java.lang.Object obj;
        java.lang.String str2;
        java.lang.String str3;
        java.lang.String str4;
        java.lang.Object obj2;
        com.GayStream.FilemoonV2 $this2;
        java.lang.String url2;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function13;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function14;
        java.util.Map defaultHeaders;
        com.lagradost.nicehttp.NiceResponse initialResponse;
        java.lang.String str5;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        java.lang.String referer3;
        java.lang.String str6;
        java.lang.String iframeSrcUrl;
        java.lang.Object obj3;
        java.util.Map defaultHeaders2;
        java.util.Map iframeHeaders;
        com.GayStream.FilemoonV2 $this3;
        java.lang.String iframeSrcUrl2;
        int i;
        java.lang.String videoUrl;
        java.lang.Object objGenerateM3u8$default;
        java.lang.String videoUrl2;
        java.lang.String iframeSrcUrl3;
        java.util.Map defaultHeaders3;
        com.GayStream.FilemoonV2 $this4;
        java.lang.String referer4;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16;
        java.lang.String url3;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function17;
        com.lagradost.nicehttp.NiceResponse initialResponse2;
        java.lang.String fallbackScriptData;
        java.util.List groupValues;
        com.lagradost.nicehttp.NiceResponse iframeResponse;
        java.lang.String iframeScriptData;
        java.lang.String unpackedScript;
        java.lang.String videoUrl3;
        java.lang.String str7;
        java.lang.String videoUrl4;
        com.GayStream.FilemoonV2 $this5;
        boolean z;
        java.lang.Object obj4;
        java.util.Map iframeHeaders2;
        java.lang.String iframeSrcUrl4;
        java.lang.String referer5;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function19;
        com.lagradost.cloudstream3.network.WebViewResolver resolver;
        java.util.List groupValues2;
        java.lang.String interceptedUrl;
        if (continuation instanceof com.GayStream.FilemoonV2.AnonymousClass1) {
            anonymousClass1 = (com.GayStream.FilemoonV2.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.GayStream.FilemoonV2.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.util.Map defaultHeaders4 = kotlin.collections.MapsKt.mapOf(new kotlin.Pair[]{kotlin.TuplesKt.to("Referer", url), kotlin.TuplesKt.to("Sec-Fetch-Dest", "iframe"), kotlin.TuplesKt.to("Sec-Fetch-Mode", "navigate"), kotlin.TuplesKt.to("Sec-Fetch-Site", "cross-site"), kotlin.TuplesKt.to("User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0")});
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = referer;
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                anonymousClass12.L$4 = function12;
                anonymousClass12.L$5 = defaultHeaders4;
                anonymousClass12.label = 1;
                str = "FilemoonV2";
                obj = coroutine_suspended;
                str2 = "sources:\\[\\{file:\"(.*?)\"";
                str3 = "script:containsData(function(p,a,c,k,e,d))";
                str4 = "iframe";
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, defaultHeaders4, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4092, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                function13 = function1;
                function14 = function12;
                defaultHeaders = defaultHeaders4;
                initialResponse = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Element elementSelectFirst = initialResponse.getDocument().selectFirst(str4);
                java.lang.String iframeSrcUrl5 = elementSelectFirst == null ? elementSelectFirst.attr("src") : null;
                str5 = iframeSrcUrl5;
                if (!(str5 != null || str5.length() == 0)) {
                    org.jsoup.nodes.Element elementSelectFirst2 = initialResponse.getDocument().selectFirst(str3);
                    java.lang.String strData = elementSelectFirst2 != null ? elementSelectFirst2.data() : null;
                    java.lang.String fallbackScriptData2 = strData != null ? strData : "";
                    java.lang.String unpackedScript2 = new com.lagradost.cloudstream3.utils.JsUnpacker(fallbackScriptData2).unpack();
                    if (unpackedScript2 != null) {
                        i = 2;
                        kotlin.text.MatchResult matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex(str2), unpackedScript2, 0, 2, (java.lang.Object) null);
                        videoUrl = (matchResultFind$default == null || (groupValues = matchResultFind$default.getGroupValues()) == null) ? null : (java.lang.String) groupValues.get(1);
                    } else {
                        i = 2;
                        videoUrl = null;
                    }
                    java.lang.String str8 = videoUrl;
                    if (str8 == null || str8.length() == 0) {
                        com.lagradost.api.Log.INSTANCE.d(str, "No iframe and no video URL found in script fallback.");
                        return kotlin.Unit.INSTANCE;
                    }
                    com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                    java.lang.String name = $this2.getName();
                    java.lang.String mainUrl = $this2.getMainUrl();
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                    anonymousClass12.L$4 = function14;
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(defaultHeaders);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialResponse);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeSrcUrl5);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(fallbackScriptData2);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript2);
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl);
                    anonymousClass12.label = i;
                    objGenerateM3u8$default = com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion, name, videoUrl, mainUrl, (java.lang.Integer) null, defaultHeaders, (java.lang.String) null, anonymousClass12, 40, (java.lang.Object) null);
                    java.util.Map defaultHeaders5 = defaultHeaders;
                    if (objGenerateM3u8$default == obj) {
                        return obj;
                    }
                    java.lang.String str9 = videoUrl;
                    videoUrl2 = iframeSrcUrl5;
                    iframeSrcUrl3 = str9;
                    defaultHeaders3 = defaultHeaders5;
                    $this4 = $this2;
                    referer4 = referer2;
                    function16 = function14;
                    url3 = url2;
                    function17 = function13;
                    initialResponse2 = initialResponse;
                    fallbackScriptData = fallbackScriptData2;
                    java.lang.Iterable $this$forEach$iv = (java.lang.Iterable) objGenerateM3u8$default;
                    for (java.lang.Object element$iv : $this$forEach$iv) {
                        function16.invoke(element$iv);
                    }
                    return kotlin.Unit.INSTANCE;
                }
                java.util.Map defaultHeaders6 = defaultHeaders;
                java.util.Map iframeHeaders3 = kotlin.collections.MapsKt.plus(defaultHeaders6, kotlin.TuplesKt.to("Accept-Language", "en-US,en;q=0.5"));
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this2;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = referer2;
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                anonymousClass12.L$5 = defaultHeaders6;
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialResponse);
                anonymousClass12.L$7 = iframeSrcUrl5;
                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeHeaders3);
                anonymousClass12.label = 3;
                com.GayStream.FilemoonV2.AnonymousClass1 anonymousClass13 = anonymousClass12;
                com.GayStream.FilemoonV2 $this6 = $this2;
                function15 = function14;
                referer3 = referer2;
                str6 = str;
                iframeSrcUrl = str2;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app2, iframeSrcUrl5, iframeHeaders3, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4092, (java.lang.Object) null);
                anonymousClass12 = anonymousClass13;
                if (obj3 == obj) {
                    return obj;
                }
                defaultHeaders2 = defaultHeaders6;
                iframeHeaders = iframeHeaders3;
                $this3 = $this6;
                iframeSrcUrl2 = iframeSrcUrl5;
                iframeResponse = (com.lagradost.nicehttp.NiceResponse) obj3;
                org.jsoup.nodes.Element elementSelectFirst3 = iframeResponse.getDocument().selectFirst(str3);
                java.lang.String strData2 = elementSelectFirst3 == null ? elementSelectFirst3.data() : null;
                iframeScriptData = strData2 != null ? strData2 : "";
                unpackedScript = new com.lagradost.cloudstream3.utils.JsUnpacker(iframeScriptData).unpack();
                if (unpackedScript == null) {
                    videoUrl3 = null;
                    kotlin.text.MatchResult matchResultFind$default2 = kotlin.text.Regex.find$default(new kotlin.text.Regex(iframeSrcUrl), unpackedScript, 0, 2, (java.lang.Object) null);
                    if (matchResultFind$default2 != null && (groupValues2 = matchResultFind$default2.getGroupValues()) != null) {
                        videoUrl3 = (java.lang.String) groupValues2.get(1);
                    }
                } else {
                    videoUrl3 = null;
                }
                str7 = videoUrl3;
                if (str7 != null || str7.length() == 0) {
                    com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion2 = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                    java.lang.String name2 = $this3.getName();
                    java.lang.String mainUrl2 = $this3.getMainUrl();
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(defaultHeaders2);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialResponse);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeSrcUrl2);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeHeaders);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeResponse);
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeScriptData);
                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript);
                    anonymousClass12.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl3);
                    anonymousClass12.label = 4;
                    return com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion2, name2, videoUrl3, mainUrl2, (java.lang.Integer) null, defaultHeaders2, (java.lang.String) null, anonymousClass12, 40, (java.lang.Object) null) == obj ? obj : kotlin.Unit.INSTANCE;
                }
                java.util.Map defaultHeaders7 = defaultHeaders2;
                videoUrl4 = videoUrl3;
                com.lagradost.cloudstream3.network.WebViewResolver resolver2 = new com.lagradost.cloudstream3.network.WebViewResolver(new kotlin.text.Regex("(m3u8|master\\.txt)"), kotlin.collections.CollectionsKt.listOf(new kotlin.text.Regex("(m3u8|master\\.txt)")), (java.lang.String) null, false, (java.lang.String) null, (kotlin.jvm.functions.Function1) null, 15000L, 52, (kotlin.jvm.internal.DefaultConstructorMarker) null);
                java.lang.String iframeSrcUrl6 = iframeSrcUrl2;
                anonymousClass12.L$0 = $this3;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function13);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function15);
                anonymousClass12.L$5 = defaultHeaders7;
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialResponse);
                anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeSrcUrl6);
                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeHeaders);
                anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeResponse);
                anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeScriptData);
                anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript);
                anonymousClass12.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl4);
                anonymousClass12.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(resolver2);
                anonymousClass12.label = 5;
                com.GayStream.FilemoonV2.AnonymousClass1 anonymousClass14 = anonymousClass12;
                $this5 = $this3;
                java.lang.String referer6 = referer3;
                z = false;
                obj4 = com.lagradost.nicehttp.Requests.get$default(com.lagradost.cloudstream3.MainActivityKt.getApp(), iframeSrcUrl6, (java.util.Map) null, referer6, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) resolver2, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass14, 3578, (java.lang.Object) null);
                anonymousClass12 = anonymousClass14;
                if (obj4 == obj) {
                    return obj;
                }
                iframeHeaders2 = defaultHeaders7;
                iframeSrcUrl4 = iframeSrcUrl6;
                referer5 = referer6;
                function18 = function13;
                function19 = function15;
                resolver = resolver2;
                interceptedUrl = ((com.lagradost.nicehttp.NiceResponse) obj4).getUrl();
                if (interceptedUrl.length() > 0) {
                    z = true;
                }
                if (z) {
                    com.lagradost.api.Log.INSTANCE.d(str6, "No video URL intercepted in WebView fallback.");
                    return kotlin.Unit.INSTANCE;
                }
                com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion3 = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                java.lang.String name3 = $this5.getName();
                java.lang.String mainUrl3 = $this5.getMainUrl();
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this5);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer5);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function18);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function19);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeHeaders2);
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(initialResponse);
                anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeSrcUrl4);
                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeHeaders);
                anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeResponse);
                anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(iframeScriptData);
                anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpackedScript);
                anonymousClass12.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl4);
                anonymousClass12.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(resolver);
                anonymousClass12.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(interceptedUrl);
                anonymousClass12.label = 6;
                return com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion3, name3, interceptedUrl, mainUrl3, (java.lang.Integer) null, iframeHeaders2, (java.lang.String) null, anonymousClass12, 40, (java.lang.Object) null) == obj ? obj : kotlin.Unit.INSTANCE;
            case 1:
                java.util.Map defaultHeaders8 = (java.util.Map) anonymousClass12.L$5;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function110 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function111 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer7 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url4 = (java.lang.String) anonymousClass12.L$1;
                com.GayStream.FilemoonV2 $this7 = (com.GayStream.FilemoonV2) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                function14 = function110;
                str2 = "sources:\\[\\{file:\"(.*?)\"";
                function13 = function111;
                referer2 = referer7;
                url2 = url4;
                str = "FilemoonV2";
                $this2 = $this7;
                defaultHeaders = defaultHeaders8;
                obj = coroutine_suspended;
                str3 = "script:containsData(function(p,a,c,k,e,d))";
                str4 = "iframe";
                obj2 = $result;
                initialResponse = (com.lagradost.nicehttp.NiceResponse) obj2;
                org.jsoup.nodes.Element elementSelectFirst4 = initialResponse.getDocument().selectFirst(str4);
                java.lang.String iframeSrcUrl52 = elementSelectFirst4 == null ? elementSelectFirst4.attr("src") : null;
                str5 = iframeSrcUrl52;
                if (str5 != null) {
                    if (!(str5 != null || str5.length() == 0)) {
                    }
                }
            case 2:
                iframeSrcUrl3 = (java.lang.String) anonymousClass12.L$10;
                fallbackScriptData = (java.lang.String) anonymousClass12.L$8;
                videoUrl2 = (java.lang.String) anonymousClass12.L$7;
                initialResponse2 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$6;
                defaultHeaders3 = (java.util.Map) anonymousClass12.L$5;
                function16 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                function17 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                referer4 = (java.lang.String) anonymousClass12.L$2;
                url3 = (java.lang.String) anonymousClass12.L$1;
                $this4 = (com.GayStream.FilemoonV2) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                objGenerateM3u8$default = $result;
                java.lang.Iterable $this$forEach$iv2 = (java.lang.Iterable) objGenerateM3u8$default;
                while (r13.hasNext()) {
                }
                return kotlin.Unit.INSTANCE;
            case 3:
                java.util.Map iframeHeaders4 = (java.util.Map) anonymousClass12.L$8;
                java.lang.String iframeSrcUrl7 = (java.lang.String) anonymousClass12.L$7;
                com.lagradost.nicehttp.NiceResponse initialResponse3 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$6;
                java.util.Map defaultHeaders9 = (java.util.Map) anonymousClass12.L$5;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function112 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function113 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer8 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url5 = (java.lang.String) anonymousClass12.L$1;
                com.GayStream.FilemoonV2 $this8 = (com.GayStream.FilemoonV2) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this3 = $this8;
                iframeHeaders = iframeHeaders4;
                obj = coroutine_suspended;
                iframeSrcUrl = "sources:\\[\\{file:\"(.*?)\"";
                referer3 = referer8;
                url2 = url5;
                initialResponse = initialResponse3;
                defaultHeaders2 = defaultHeaders9;
                function15 = function112;
                function13 = function113;
                str6 = "FilemoonV2";
                obj3 = $result;
                str3 = "script:containsData(function(p,a,c,k,e,d))";
                iframeSrcUrl2 = iframeSrcUrl7;
                iframeResponse = (com.lagradost.nicehttp.NiceResponse) obj3;
                org.jsoup.nodes.Element elementSelectFirst32 = iframeResponse.getDocument().selectFirst(str3);
                if (elementSelectFirst32 == null) {
                }
                iframeScriptData = strData2 != null ? strData2 : "";
                unpackedScript = new com.lagradost.cloudstream3.utils.JsUnpacker(iframeScriptData).unpack();
                if (unpackedScript == null) {
                }
                str7 = videoUrl3;
                if (str7 != null) {
                    if (str7 != null || str7.length() == 0) {
                    }
                }
            case 4:
                kotlin.ResultKt.throwOnFailure($result);
            case 5:
                com.lagradost.cloudstream3.network.WebViewResolver resolver3 = (com.lagradost.cloudstream3.network.WebViewResolver) anonymousClass12.L$13;
                java.lang.String videoUrl5 = (java.lang.String) anonymousClass12.L$12;
                java.lang.String unpackedScript3 = (java.lang.String) anonymousClass12.L$11;
                java.lang.String iframeScriptData2 = (java.lang.String) anonymousClass12.L$10;
                com.lagradost.nicehttp.NiceResponse iframeResponse2 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$9;
                java.util.Map iframeHeaders5 = (java.util.Map) anonymousClass12.L$8;
                java.lang.String iframeSrcUrl8 = (java.lang.String) anonymousClass12.L$7;
                com.lagradost.nicehttp.NiceResponse initialResponse4 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$6;
                java.util.Map defaultHeaders10 = (java.util.Map) anonymousClass12.L$5;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function114 = (kotlin.jvm.functions.Function1) anonymousClass12.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function115 = (kotlin.jvm.functions.Function1) anonymousClass12.L$3;
                java.lang.String referer9 = (java.lang.String) anonymousClass12.L$2;
                resolver = resolver3;
                java.lang.String url6 = (java.lang.String) anonymousClass12.L$1;
                com.GayStream.FilemoonV2 $this9 = (com.GayStream.FilemoonV2) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                url2 = url6;
                $this5 = $this9;
                obj = coroutine_suspended;
                videoUrl4 = videoUrl5;
                unpackedScript = unpackedScript3;
                iframeResponse = iframeResponse2;
                iframeHeaders = iframeHeaders5;
                initialResponse = initialResponse4;
                iframeHeaders2 = defaultHeaders10;
                referer5 = referer9;
                str6 = "FilemoonV2";
                z = false;
                obj4 = $result;
                iframeScriptData = iframeScriptData2;
                function18 = function115;
                function19 = function114;
                iframeSrcUrl4 = iframeSrcUrl8;
                interceptedUrl = ((com.lagradost.nicehttp.NiceResponse) obj4).getUrl();
                if (interceptedUrl.length() > 0) {
                }
                if (z) {
                }
                break;
            case 6:
                kotlin.ResultKt.throwOnFailure($result);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
