package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u0011\u001a\n\u0012\u0004\u0012\u00020\u0013\u0018\u00010\u00122\u0006\u0010\u0014\u001a\u00020\u00052\b\u0010\u0015\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0016R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006\u0017"}, d2 = {"Lcom/Gayxx/vvide0Extractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/vvide0Extractor\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,451:1\n1586#2:452\n1661#2,3:453\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/vvide0Extractor\n*L\n124#1:452\n124#1:453,3\n*E\n"})
public class vvide0Extractor extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "vvide0";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://vvide0.com";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.Gayxx.vvide0Extractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.vvide0Extractor", f = "Extractor.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {112, 120, 137}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response0", "passMd5Path", "token", "md5Url", "$this", "url", "referer", "response0", "passMd5Path", "token", "md5Url", "res", "videoData", "randomStr", "link", "quality"}, nl = {115, 121, 136}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$10;
        java.lang.Object L$11;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.vvide0Extractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.vvide0Extractor.getUrl$suspendImpl(com.Gayxx.vvide0Extractor.this, null, null, (kotlin.coroutines.Continuation) this);
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

    /* JADX WARN: Removed duplicated region for block: B:26:0x01a3 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:27:0x01a4  */
    /* JADX WARN: Removed duplicated region for block: B:31:0x01d9 A[LOOP:0: B:29:0x01d3->B:31:0x01d9, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:37:0x02b1  */
    /* JADX WARN: Removed duplicated region for block: B:40:0x0321 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:41:0x0322  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gayxx.vvide0Extractor $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gayxx.vvide0Extractor.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        int i2;
        java.lang.String url2;
        java.lang.String referer2;
        java.lang.Object obj2;
        com.Gayxx.vvide0Extractor $this2;
        java.lang.String response0;
        kotlin.text.MatchResult matchResultFind$default;
        java.lang.String passMd5Path;
        java.lang.String passMd5Path2;
        java.lang.Object obj3;
        java.lang.String url3;
        java.lang.String referer3;
        java.lang.String response02;
        java.lang.String passMd5Path3;
        com.Gayxx.vvide0Extractor $this3;
        java.lang.String token;
        kotlin.collections.IntIterator it;
        java.lang.Object objNewExtractorLink;
        java.util.List groupValues;
        if (continuation instanceof com.Gayxx.vvide0Extractor.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.vvide0Extractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Gayxx.vvide0Extractor.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = url;
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                i = 0;
                i2 = 2;
                java.lang.Object obj4 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj4 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                obj2 = obj4;
                $this2 = $this;
                response0 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("/pass_md5/[^'\"]+"), response0, i, i2, (java.lang.Object) null);
                if (matchResultFind$default == null && (passMd5Path = matchResultFind$default.getValue()) != null) {
                    java.lang.String token2 = kotlin.text.StringsKt.substringAfterLast$default(passMd5Path, "/", (java.lang.String) null, i2, (java.lang.Object) null);
                    java.lang.String md5Url = $this2.getMainUrl() + passMd5Path;
                    com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    anonymousClass12.L$0 = $this2;
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = response0;
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path);
                    anonymousClass12.L$5 = token2;
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url);
                    anonymousClass12.label = i2;
                    com.Gayxx.vvide0Extractor.AnonymousClass1 anonymousClass13 = anonymousClass12;
                    com.Gayxx.vvide0Extractor $this4 = $this2;
                    passMd5Path2 = passMd5Path;
                    obj3 = com.lagradost.nicehttp.Requests.get$default(app2, md5Url, (java.util.Map) null, url2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass13, 4090, (java.lang.Object) null);
                    anonymousClass12 = anonymousClass13;
                    if (obj3 != obj) {
                        return obj;
                    }
                    url3 = url2;
                    referer3 = referer2;
                    response02 = response0;
                    passMd5Path3 = token2;
                    $this3 = $this4;
                    token = md5Url;
                    com.lagradost.nicehttp.NiceResponse res = (com.lagradost.nicehttp.NiceResponse) obj3;
                    java.lang.String videoData = res.getText();
                    java.lang.Iterable $this$map$iv = new kotlin.ranges.IntRange(1, 10);
                    java.util.Collection destination$iv$iv = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv, 10));
                    java.lang.Iterable $this$mapTo$iv$iv = $this$map$iv;
                    it = $this$mapTo$iv$iv.iterator();
                    while (it.hasNext()) {
                        it.nextInt();
                        destination$iv$iv.add(kotlin.coroutines.jvm.internal.Boxing.boxChar(((java.lang.Character) kotlin.collections.CollectionsKt.random(kotlin.collections.CollectionsKt.plus(kotlin.collections.CollectionsKt.plus(new kotlin.ranges.CharRange('a', 'z'), new kotlin.ranges.CharRange('A', 'Z')), new kotlin.ranges.CharRange('0', '9')), kotlin.random.Random.Default)).charValue()));
                        $this$map$iv = $this$map$iv;
                        $this$mapTo$iv$iv = $this$mapTo$iv$iv;
                    }
                    java.lang.String randomStr = kotlin.collections.CollectionsKt.joinToString$default((java.util.List) destination$iv$iv, "", (java.lang.CharSequence) null, (java.lang.CharSequence) null, 0, (java.lang.CharSequence) null, (kotlin.jvm.functions.Function1) null, 62, (java.lang.Object) null);
                    java.lang.String link = videoData + randomStr + "?token=" + passMd5Path3 + "&expiry=" + java.lang.System.currentTimeMillis();
                    kotlin.text.MatchResult matchResultFind$default2 = kotlin.text.Regex.find$default(new kotlin.text.Regex("(\\d{3,4})[pP]"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response02, "<title>", (java.lang.String) null, 2, (java.lang.Object) null), "</title>", (java.lang.String) null, 2, (java.lang.Object) null), 0, 2, (java.lang.Object) null);
                    java.lang.String quality = (matchResultFind$default2 != null || (groupValues = matchResultFind$default2.getGroupValues()) == null) ? null : (java.lang.String) groupValues.get(1);
                    java.lang.String videoData2 = $this3.getName();
                    java.lang.String name = $this3.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                    com.Gayxx.vvide0Extractor.AnonymousClass2 anonymousClass2 = $this3.new AnonymousClass2(quality, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path2);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path3);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(res);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoData);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(randomStr);
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                    anonymousClass12.label = 3;
                    objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(videoData2, name, link, infer_type, anonymousClass2, anonymousClass12);
                    return objNewExtractorLink != obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
                }
                return null;
            case 1:
                java.lang.String referer4 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url4 = (java.lang.String) anonymousClass12.L$1;
                com.Gayxx.vvide0Extractor $this5 = (com.Gayxx.vvide0Extractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this5;
                obj = coroutine_suspended;
                referer2 = referer4;
                url2 = url4;
                i = 0;
                obj2 = $result;
                i2 = 2;
                response0 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("/pass_md5/[^'\"]+"), response0, i, i2, (java.lang.Object) null);
                if (matchResultFind$default == null) {
                    return null;
                }
                java.lang.String token22 = kotlin.text.StringsKt.substringAfterLast$default(passMd5Path, "/", (java.lang.String) null, i2, (java.lang.Object) null);
                java.lang.String md5Url2 = $this2.getMainUrl() + passMd5Path;
                com.lagradost.nicehttp.Requests app22 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this2;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = response0;
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path);
                anonymousClass12.L$5 = token22;
                anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url2);
                anonymousClass12.label = i2;
                com.Gayxx.vvide0Extractor.AnonymousClass1 anonymousClass132 = anonymousClass12;
                com.Gayxx.vvide0Extractor $this42 = $this2;
                passMd5Path2 = passMd5Path;
                obj3 = com.lagradost.nicehttp.Requests.get$default(app22, md5Url2, (java.util.Map) null, url2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass132, 4090, (java.lang.Object) null);
                anonymousClass12 = anonymousClass132;
                if (obj3 != obj) {
                }
                break;
            case 2:
                java.lang.String md5Url3 = (java.lang.String) anonymousClass12.L$6;
                java.lang.String token3 = (java.lang.String) anonymousClass12.L$5;
                java.lang.String passMd5Path4 = (java.lang.String) anonymousClass12.L$4;
                response02 = (java.lang.String) anonymousClass12.L$3;
                referer3 = (java.lang.String) anonymousClass12.L$2;
                url3 = (java.lang.String) anonymousClass12.L$1;
                com.Gayxx.vvide0Extractor $this6 = (com.Gayxx.vvide0Extractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this3 = $this6;
                obj = coroutine_suspended;
                passMd5Path2 = passMd5Path4;
                obj3 = $result;
                passMd5Path3 = token3;
                token = md5Url3;
                com.lagradost.nicehttp.NiceResponse res2 = (com.lagradost.nicehttp.NiceResponse) obj3;
                java.lang.String videoData3 = res2.getText();
                java.lang.Iterable $this$map$iv2 = new kotlin.ranges.IntRange(1, 10);
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv2, 10));
                java.lang.Iterable $this$mapTo$iv$iv2 = $this$map$iv2;
                it = $this$mapTo$iv$iv2.iterator();
                while (it.hasNext()) {
                }
                java.lang.String randomStr2 = kotlin.collections.CollectionsKt.joinToString$default((java.util.List) destination$iv$iv2, "", (java.lang.CharSequence) null, (java.lang.CharSequence) null, 0, (java.lang.CharSequence) null, (kotlin.jvm.functions.Function1) null, 62, (java.lang.Object) null);
                java.lang.String link2 = videoData3 + randomStr2 + "?token=" + passMd5Path3 + "&expiry=" + java.lang.System.currentTimeMillis();
                kotlin.text.MatchResult matchResultFind$default22 = kotlin.text.Regex.find$default(new kotlin.text.Regex("(\\d{3,4})[pP]"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response02, "<title>", (java.lang.String) null, 2, (java.lang.Object) null), "</title>", (java.lang.String) null, 2, (java.lang.Object) null), 0, 2, (java.lang.Object) null);
                if (matchResultFind$default22 != null) {
                    java.lang.String videoData22 = $this3.getName();
                    java.lang.String name2 = $this3.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                    com.Gayxx.vvide0Extractor.AnonymousClass2 anonymousClass22 = $this3.new AnonymousClass2(quality, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this3);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path2);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path3);
                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token);
                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(res2);
                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoData3);
                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(randomStr2);
                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link2);
                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                    anonymousClass12.label = 3;
                    objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(videoData22, name2, link2, infer_type2, anonymousClass22, anonymousClass12);
                    if (objNewExtractorLink != obj) {
                    }
                }
            case 3:
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Gayxx.vvide0Extractor$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.vvide0Extractor$getUrl$2", f = "Extractor.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ java.lang.String $quality;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(java.lang.String str, kotlin.coroutines.Continuation<? super com.Gayxx.vvide0Extractor.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$quality = str;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = com.Gayxx.vvide0Extractor.this.new AnonymousClass2(this.$quality, continuation);
            anonymousClass2.L$0 = obj;
            return anonymousClass2;
        }

        public final java.lang.Object invoke(com.lagradost.cloudstream3.utils.ExtractorLink extractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
            return create(extractorLink, continuation).invokeSuspend(kotlin.Unit.INSTANCE);
        }

        public final java.lang.Object invokeSuspend(java.lang.Object $result) {
            com.lagradost.cloudstream3.utils.ExtractorLink $this$newExtractorLink = (com.lagradost.cloudstream3.utils.ExtractorLink) this.L$0;
            kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
            switch (this.label) {
                case 0:
                    kotlin.ResultKt.throwOnFailure($result);
                    $this$newExtractorLink.setReferer(com.Gayxx.vvide0Extractor.this.getMainUrl());
                    $this$newExtractorLink.setQuality(com.lagradost.cloudstream3.utils.ExtractorApiKt.getQualityFromName(this.$quality));
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }
}
