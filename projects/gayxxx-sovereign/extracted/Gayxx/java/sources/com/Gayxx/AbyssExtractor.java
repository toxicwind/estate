package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u00100\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0014"}, d2 = {"Lcom/Gayxx/AbyssExtractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/AbyssExtractor\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,451:1\n1915#2,2:452\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/AbyssExtractor\n*L\n405#1:452,2\n*E\n"})
public class AbyssExtractor extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Abyss";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://abyss.to";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.Gayxx.AbyssExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.AbyssExtractor", f = "Extractor.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3}, l = {390, 397, 412, 425}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response", "document", "m3u8", "$i$a$-let-AbyssExtractor$getUrl$2", "$this", "url", "referer", "response", "document", "$this$forEach$iv", "element$iv", "script", "data", "unpacked", "m3u8", "$i$f$forEach", "$i$a$-forEach-AbyssExtractor$getUrl$3", "$i$a$-let-AbyssExtractor$getUrl$3$1", "$i$a$-let-AbyssExtractor$getUrl$3$1$1", "$this", "url", "referer", "response", "document", "file", "$i$a$-let-AbyssExtractor$getUrl$4"}, nl = {391, 396, 411, 424}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "I$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "I$0", "I$1", "I$2", "I$3", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        int I$2;
        int I$3;
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
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.AbyssExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.AbyssExtractor.getUrl$suspendImpl(com.Gayxx.AbyssExtractor.this, null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.Nullable
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String str, @org.jetbrains.annotations.Nullable java.lang.String str2, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        return getUrl$suspendImpl(this, str, str2, continuation);
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

    /* JADX WARN: Removed duplicated region for block: B:37:0x01a3  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gayxx.AbyssExtractor $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gayxx.AbyssExtractor.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        java.lang.Object obj2;
        com.Gayxx.AbyssExtractor $this2;
        java.lang.String url2;
        java.lang.String referer2;
        org.jsoup.nodes.Document document;
        kotlin.text.MatchResult matchResultFind$default;
        java.util.Iterator it;
        org.jsoup.nodes.Element elementSelectFirst;
        java.lang.String file;
        java.lang.String unpacked;
        java.util.List groupValues;
        java.lang.String m3u8;
        java.lang.Object objNewExtractorLink;
        if (continuation instanceof com.Gayxx.AbyssExtractor.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.AbyssExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Gayxx.AbyssExtractor.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                java.lang.String mainUrl = referer == null ? $this.getMainUrl() : referer;
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, mainUrl, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4090, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) obj2;
                document = response.getDocument();
                int i = 2;
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("(https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*)"), response.getText(), 0, 2, (java.lang.Object) null);
                if (matchResultFind$default == null && (m3u8 = matchResultFind$default.getValue()) != null) {
                    java.lang.String name = $this2.getName();
                    java.lang.String name2 = $this2.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                    com.Gayxx.AbyssExtractor$getUrl$2$1 abyssExtractor$getUrl$2$1 = new com.Gayxx.AbyssExtractor$getUrl$2$1($this2, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8);
                    anonymousClass12.I$0 = 0;
                    anonymousClass12.label = 2;
                    objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, name2, m3u8, infer_type, abyssExtractor$getUrl$2$1, anonymousClass12);
                    return objNewExtractorLink == obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
                }
                java.lang.Iterable $this$forEach$iv = document.select("script");
                it = $this$forEach$iv.iterator();
                while (it.hasNext()) {
                    java.lang.Object element$iv = it.next();
                    org.jsoup.nodes.Element script = (org.jsoup.nodes.Element) element$iv;
                    java.lang.String data = script.data();
                    java.lang.Object $result2 = $result;
                    java.util.Iterator it2 = it;
                    if (kotlin.text.StringsKt.contains$default(data, "sources", false, i, (java.lang.Object) null) && (unpacked = new com.lagradost.cloudstream3.utils.JsUnpacker(data).unpack()) != null) {
                        kotlin.text.MatchResult matchResultFind$default2 = kotlin.text.Regex.find$default(new kotlin.text.Regex("file\\s*:\\s*\"([^\"]+\\.m3u8[^\"]*)\""), unpacked, 0, 2, (java.lang.Object) null);
                        if (matchResultFind$default2 != null && (groupValues = matchResultFind$default2.getGroupValues()) != null) {
                            java.lang.String m3u82 = (java.lang.String) groupValues.get(1);
                            if (m3u82 != null) {
                                java.lang.String name3 = $this2.getName();
                                java.lang.String name4 = $this2.getName();
                                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                                com.Gayxx.AbyssExtractor$getUrl$3$1$1$1 abyssExtractor$getUrl$3$1$1$1 = new com.Gayxx.AbyssExtractor$getUrl$3$1$1$1($this2, null);
                                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEach$iv);
                                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv);
                                anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(script);
                                anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data);
                                anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(unpacked);
                                anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u82);
                                anonymousClass12.I$0 = 0;
                                anonymousClass12.I$1 = 0;
                                anonymousClass12.I$2 = 0;
                                anonymousClass12.I$3 = 0;
                                anonymousClass12.label = 3;
                                $result = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name3, name4, m3u82, infer_type2, abyssExtractor$getUrl$3$1$1$1, anonymousClass12);
                                return $result == obj ? obj : kotlin.collections.CollectionsKt.listOf($result);
                            }
                        }
                    }
                    it = it2;
                    $result = $result2;
                    i = 2;
                }
                elementSelectFirst = document.selectFirst("source[src]");
                if (elementSelectFirst != null || (file = elementSelectFirst.attr("src")) == null) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.lang.String name5 = $this2.getName();
                java.lang.String name6 = $this2.getName();
                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type3 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                com.Gayxx.AbyssExtractor$getUrl$4$1 abyssExtractor$getUrl$4$1 = new com.Gayxx.AbyssExtractor$getUrl$4$1($this2, null);
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(file);
                anonymousClass12.I$0 = 0;
                anonymousClass12.label = 4;
                $result = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name5, name6, file, infer_type3, abyssExtractor$getUrl$4$1, anonymousClass12);
                return $result == obj ? obj : kotlin.collections.CollectionsKt.listOf($result);
            case 1:
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$1;
                com.Gayxx.AbyssExtractor $this3 = (com.Gayxx.AbyssExtractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this3;
                referer2 = referer3;
                obj = coroutine_suspended;
                url2 = url3;
                obj2 = $result;
                com.lagradost.nicehttp.NiceResponse response2 = (com.lagradost.nicehttp.NiceResponse) obj2;
                document = response2.getDocument();
                int i2 = 2;
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("(https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*)"), response2.getText(), 0, 2, (java.lang.Object) null);
                if (matchResultFind$default == null) {
                    break;
                }
                java.lang.Iterable $this$forEach$iv2 = document.select("script");
                it = $this$forEach$iv2.iterator();
                while (it.hasNext()) {
                }
                elementSelectFirst = document.selectFirst("source[src]");
                if (elementSelectFirst != null) {
                    break;
                }
                return kotlin.collections.CollectionsKt.emptyList();
            case 2:
                int i3 = anonymousClass12.I$0;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
            case 3:
                int i4 = anonymousClass12.I$3;
                int i5 = anonymousClass12.I$2;
                int i6 = anonymousClass12.I$1;
                int i7 = anonymousClass12.I$0;
                java.lang.Object obj3 = anonymousClass12.L$6;
                kotlin.ResultKt.throwOnFailure($result);
            case 4:
                int i8 = anonymousClass12.I$0;
                kotlin.ResultKt.throwOnFailure($result);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
