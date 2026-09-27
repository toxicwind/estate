package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000V\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\b\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010\u0012\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0011\u001a\u00020\u00122\u0006\u0010\u0013\u001a\u00020\u0005H\u0002J\u0010\u0010\u0014\u001a\u00020\u00052\u0006\u0010\u0015\u001a\u00020\u0005H\u0002J\u0010\u0010\u0016\u001a\u00020\u00052\u0006\u0010\u0015\u001a\u00020\u0005H\u0002J\u0018\u0010\u0017\u001a\u0004\u0018\u00010\u00182\u0006\u0010\n\u001a\u00020\u0005H\u0082@¢\u0006\u0002\u0010\u0019J\u0018\u0010\u001a\u001a\u0004\u0018\u00010\u001b2\u0006\u0010\n\u001a\u00020\u0005H\u0082@¢\u0006\u0002\u0010\u0019J\u0010\u0010\u001c\u001a\u00020\u00122\u0006\u0010\u001d\u001a\u00020\u001eH\u0002J\u0012\u0010\u001f\u001a\u0004\u0018\u00010\u00052\u0006\u0010\u001d\u001a\u00020\u001eH\u0002JH\u0010 \u001a\u00020!2\u0006\u0010\u0015\u001a\u00020\u00052\b\u0010\"\u001a\u0004\u0018\u00010\u00052\u0012\u0010#\u001a\u000e\u0012\u0004\u0012\u00020%\u0012\u0004\u0012\u00020!0$2\u0012\u0010&\u001a\u000e\u0012\u0004\u0012\u00020'\u0012\u0004\u0012\u00020!0$H\u0096@¢\u0006\u0002\u0010(R\u001a\u0010\u0004\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u0006\u0010\u0007\"\u0004\b\b\u0010\tR\u001a\u0010\n\u001a\u00020\u0005X\u0096\u000e¢\u0006\u000e\n\u0000\u001a\u0004\b\u000b\u0010\u0007\"\u0004\b\f\u0010\tR\u0014\u0010\r\u001a\u00020\u000eX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\u0010¨\u0006)"}, d2 = {"Lcom/Jayboys/ByseSX;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "setName", "(Ljava/lang/String;)V", "mainUrl", "getMainUrl", "setMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "b64UrlDecode", "", "s", "getBaseUrl", "url", "getCodeFromUrl", "getDetails", "Lcom/Jayboys/DetailsRoot;", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "getPlayback", "Lcom/Jayboys/PlaybackRoot;", "buildAesKey", "playback", "Lcom/Jayboys/Playback;", "decryptPlayback", "getUrl", "", "referer", "subtitleCallback", "Lkotlin/Function1;", "Lcom/lagradost/cloudstream3/SubtitleFile;", "callback", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractors.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractors.kt\ncom/Jayboys/ByseSX\n+ 2 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 3 NiceResponse.kt\ncom/lagradost/nicehttp/NiceResponse\n+ 4 AppUtils.kt\ncom/lagradost/cloudstream3/utils/AppUtils\n+ 5 Extensions.kt\ncom/fasterxml/jackson/module/kotlin/ExtensionsKt\n+ 6 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,504:1\n1#2:505\n73#3,5:506\n73#3,5:511\n73#3,5:516\n23#4,2:521\n15#4:523\n25#4,2:526\n50#5:524\n43#5:525\n1915#6,2:528\n*S KotlinDebug\n*F\n+ 1 Extractors.kt\ncom/Jayboys/ByseSX\n*L\n356#1:506,5\n387#1:511,5\n393#1:516,5\n419#1:521,2\n419#1:523\n419#1:526,2\n419#1:524\n419#1:525\n445#1:528,2\n*E\n"})
public class ByseSX extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private java.lang.String name = "Byse";

    @org.jetbrains.annotations.NotNull
    private java.lang.String mainUrl = "https://byse.sx";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.Jayboys.ByseSX$getDetails$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.ByseSX", f = "Extractors.kt", i = {0, 0, 0, 0}, l = {356}, m = "getDetails", n = {"mainUrl", "base", "code", "url"}, nl = {505}, s = {"L$0", "L$1", "L$2", "L$3"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Jayboys.ByseSX.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.ByseSX.this.getDetails(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.ByseSX$getPlayback$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.ByseSX", f = "Extractors.kt", i = {0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2}, l = {360, 384, 392}, m = "getPlayback", n = {"mainUrl", "mainUrl", "details", "embedFrameUrl", "embedBase", "code", "playbackUrl", "headers", "postheaders", "mainUrl", "details", "embedFrameUrl", "embedBase", "code", "playbackUrl", "headers", "postheaders", "response", "json"}, nl = {361, 386, 393}, s = {"L$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9"}, v = 2)
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

        C00001(kotlin.coroutines.Continuation<? super com.Jayboys.ByseSX.C00001> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.ByseSX.this.getPlayback(null, (kotlin.coroutines.Continuation) this);
        }
    }

    /* JADX INFO: renamed from: com.Jayboys.ByseSX$getUrl$1, reason: invalid class name and case insensitive filesystem */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Jayboys.ByseSX", f = "Extractors.kt", i = {0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {435, 440}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "subtitleCallback", "callback", "refererUrl", "$this", "url", "referer", "subtitleCallback", "callback", "refererUrl", "playbackRoot", "streamUrl", "headers"}, nl = {436, 445}, s = {"L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8"}, v = 2)
    static final class C00011 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
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

        C00011(kotlin.coroutines.Continuation<? super com.Jayboys.ByseSX.C00011> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Jayboys.ByseSX.getUrl$suspendImpl(com.Jayboys.ByseSX.this, null, null, null, null, (kotlin.coroutines.Continuation) this);
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

    private final byte[] b64UrlDecode(java.lang.String s) {
        java.lang.String fixed = kotlin.text.StringsKt.replace$default(kotlin.text.StringsKt.replace$default(s, '-', '+', false, 4, (java.lang.Object) null), '_', '/', false, 4, (java.lang.Object) null);
        int pad = (4 - (fixed.length() % 4)) % 4;
        return com.lagradost.cloudstream3.MainAPIKt.base64DecodeArray(fixed + kotlin.text.StringsKt.repeat("=", pad));
    }

    private final java.lang.String getBaseUrl(java.lang.String url) {
        java.net.URI it = new java.net.URI(url);
        return it.getScheme() + "://" + it.getHost();
    }

    private final java.lang.String getCodeFromUrl(java.lang.String url) {
        java.lang.String path = new java.net.URI(url).getPath();
        if (path == null) {
            path = "";
        }
        return kotlin.text.StringsKt.substringAfterLast$default(kotlin.text.StringsKt.trimEnd(path, new char[]{'/'}), '/', (java.lang.String) null, 2, (java.lang.Object) null);
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public final java.lang.Object getDetails(java.lang.String mainUrl, kotlin.coroutines.Continuation<? super com.Jayboys.DetailsRoot> continuation) {
        com.Jayboys.ByseSX.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        if (continuation instanceof com.Jayboys.ByseSX.AnonymousClass1) {
            anonymousClass1 = (com.Jayboys.ByseSX.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = new com.Jayboys.ByseSX.AnonymousClass1(continuation);
            }
        }
        com.Jayboys.ByseSX.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String base = getBaseUrl(mainUrl);
                java.lang.String code = getCodeFromUrl(mainUrl);
                java.lang.String url = base + "/api/videos/" + code + "/embed/details";
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mainUrl);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(base);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(code);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.label = 1;
                obj = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                if (obj == coroutine_suspended) {
                    return coroutine_suspended;
                }
                break;
            case 1:
                kotlin.ResultKt.throwOnFailure($result);
                obj = $result;
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        com.lagradost.nicehttp.NiceResponse this_$iv = (com.lagradost.nicehttp.NiceResponse) obj;
        try {
            com.lagradost.nicehttp.ResponseParser parser = this_$iv.getParser();
            kotlin.jvm.internal.Intrinsics.checkNotNull(parser);
            return parser.parseSafe(this_$iv.getText(), kotlin.jvm.internal.Reflection.getOrCreateKotlinClass(com.Jayboys.DetailsRoot.class));
        } catch (java.lang.Exception e$iv) {
            e$iv.printStackTrace();
            return null;
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX WARN: Removed duplicated region for block: B:20:0x00ca A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:21:0x00cb  */
    /* JADX WARN: Removed duplicated region for block: B:27:0x01fe  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x0224  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x001a  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public final java.lang.Object getPlayback(java.lang.String mainUrl, kotlin.coroutines.Continuation<? super com.Jayboys.PlaybackRoot> continuation) {
        com.Jayboys.ByseSX.C00001 c00001;
        char c;
        java.lang.Object details;
        com.Jayboys.DetailsRoot details2;
        java.lang.String playbackUrl;
        java.util.Map postheaders;
        java.lang.String mainUrl2;
        java.lang.Object obj;
        int i;
        com.Jayboys.ByseSX.C00001 c000012;
        com.Jayboys.DetailsRoot details3;
        java.lang.String embedFrameUrl;
        java.lang.String embedBase;
        java.lang.String code;
        java.util.Map headers;
        com.lagradost.nicehttp.NiceResponse response;
        java.lang.Object obj2;
        java.lang.String playbackUrl2;
        java.util.Map postheaders2;
        java.util.Map headers2;
        java.lang.String code2;
        java.lang.String embedBase2;
        java.lang.String embedFrameUrl2;
        com.Jayboys.DetailsRoot details4;
        com.lagradost.nicehttp.NiceResponse response2;
        java.lang.Object safe;
        java.lang.Object safe2;
        java.lang.String mainUrl3 = mainUrl;
        if (continuation instanceof com.Jayboys.ByseSX.C00001) {
            c00001 = (com.Jayboys.ByseSX.C00001) continuation;
            if ((c00001.label & Integer.MIN_VALUE) != 0) {
                c00001.label -= Integer.MIN_VALUE;
            } else {
                c00001 = new com.Jayboys.ByseSX.C00001(continuation);
            }
        }
        java.lang.Object $result = c00001.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c00001.label) {
            case 0:
                c = 3;
                kotlin.ResultKt.throwOnFailure($result);
                c00001.L$0 = mainUrl3;
                c00001.label = 1;
                details = getDetails(mainUrl3, c00001);
                if (details == coroutine_suspended) {
                    return coroutine_suspended;
                }
                details2 = (com.Jayboys.DetailsRoot) details;
                if (details2 != null) {
                    return null;
                }
                java.lang.String embedFrameUrl3 = details2.getEmbedFrameUrl();
                java.lang.String embedBase3 = getBaseUrl(embedFrameUrl3);
                java.lang.String code3 = getCodeFromUrl(embedFrameUrl3);
                java.lang.String playbackUrl3 = embedBase3 + "/api/videos/" + code3 + "/embed/playback";
                kotlin.Pair[] pairArr = new kotlin.Pair[5];
                pairArr[0] = kotlin.TuplesKt.to("accept", "*/*");
                pairArr[1] = kotlin.TuplesKt.to("accept-language", "en-US,en;q=0.5");
                pairArr[2] = kotlin.TuplesKt.to("priority", "u=1, i");
                pairArr[c] = kotlin.TuplesKt.to("referer", embedFrameUrl3);
                pairArr[4] = kotlin.TuplesKt.to("x-embed-parent", embedFrameUrl3);
                java.util.Map headers3 = kotlin.collections.MapsKt.mapOf(pairArr);
                kotlin.Pair[] pairArr2 = new kotlin.Pair[6];
                pairArr2[0] = kotlin.TuplesKt.to("Accept", "*/*");
                pairArr2[1] = kotlin.TuplesKt.to("Accept-Language", "en-US,en;q=0.9");
                pairArr2[2] = kotlin.TuplesKt.to("Content-Type", "application/json");
                pairArr2[c] = kotlin.TuplesKt.to("Referer", embedFrameUrl3);
                pairArr2[4] = kotlin.TuplesKt.to("X-Embed-Parent", mainUrl3);
                pairArr2[5] = kotlin.TuplesKt.to("Priority", "u=4");
                java.util.Map postheaders3 = kotlin.collections.MapsKt.mapOf(pairArr2);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                c00001.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mainUrl3);
                c00001.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(details2);
                c00001.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedFrameUrl3);
                c00001.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedBase3);
                c00001.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(code3);
                c00001.L$5 = playbackUrl3;
                c00001.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(headers3);
                c00001.L$7 = postheaders3;
                c00001.label = 2;
                playbackUrl = playbackUrl3;
                postheaders = postheaders3;
                mainUrl2 = mainUrl3;
                com.Jayboys.ByseSX.C00001 c000013 = c00001;
                obj = coroutine_suspended;
                i = 1;
                $result = com.lagradost.nicehttp.Requests.get$default(app, playbackUrl, headers3, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000013, 4092, (java.lang.Object) null);
                c000012 = c000013;
                if ($result == obj) {
                    return obj;
                }
                details3 = details2;
                embedFrameUrl = embedFrameUrl3;
                embedBase = embedBase3;
                code = code3;
                headers = headers3;
                response = (com.lagradost.nicehttp.NiceResponse) $result;
                if (response.getCode() != 200) {
                    try {
                        com.lagradost.nicehttp.ResponseParser parser = response.getParser();
                        kotlin.jvm.internal.Intrinsics.checkNotNull(parser);
                        safe = parser.parseSafe(response.getText(), kotlin.jvm.internal.Reflection.getOrCreateKotlinClass(com.Jayboys.PlaybackRoot.class));
                        break;
                    } catch (java.lang.Exception e$iv) {
                        e$iv.printStackTrace();
                        safe = null;
                    }
                    return (com.Jayboys.PlaybackRoot) safe;
                }
                com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                okhttp3.RequestBody requestBodyCreate$default = okhttp3.RequestBody.Companion.create$default(okhttp3.RequestBody.Companion, "{\n  \"fingerprint\": {}\n}", (okhttp3.MediaType) null, i, (java.lang.Object) null);
                c000012.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mainUrl2);
                c000012.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(details3);
                c000012.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedFrameUrl);
                c000012.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(embedBase);
                c000012.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(code);
                c000012.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(playbackUrl);
                c000012.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(headers);
                c000012.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(postheaders);
                c000012.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                c000012.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable("{\n  \"fingerprint\": {}\n}");
                c000012.label = 3;
                obj2 = null;
                java.util.Map postheaders4 = postheaders;
                $result = com.lagradost.nicehttp.Requests.post$default(app2, playbackUrl, postheaders4, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, (java.util.Map) null, (java.util.List) null, (java.lang.Object) null, requestBodyCreate$default, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, c000012, 65276, (java.lang.Object) null);
                if ($result == obj) {
                    return obj;
                }
                playbackUrl2 = playbackUrl;
                postheaders2 = postheaders4;
                headers2 = headers;
                code2 = code;
                embedBase2 = embedBase;
                embedFrameUrl2 = embedFrameUrl;
                details4 = details3;
                response2 = response;
                com.lagradost.nicehttp.NiceResponse this_$iv = (com.lagradost.nicehttp.NiceResponse) $result;
                try {
                    com.lagradost.nicehttp.ResponseParser parser2 = this_$iv.getParser();
                    kotlin.jvm.internal.Intrinsics.checkNotNull(parser2);
                    safe2 = parser2.parseSafe(this_$iv.getText(), kotlin.jvm.internal.Reflection.getOrCreateKotlinClass(com.Jayboys.PlaybackRoot.class));
                    break;
                } catch (java.lang.Exception e$iv2) {
                    e$iv2.printStackTrace();
                    safe2 = obj2;
                }
                return (com.Jayboys.PlaybackRoot) safe2;
            case 1:
                c = 3;
                mainUrl3 = (java.lang.String) c00001.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                details = $result;
                details2 = (com.Jayboys.DetailsRoot) details;
                if (details2 != null) {
                }
                break;
            case 2:
                java.util.Map postheaders5 = (java.util.Map) c00001.L$7;
                java.util.Map headers4 = (java.util.Map) c00001.L$6;
                java.lang.String playbackUrl4 = (java.lang.String) c00001.L$5;
                java.lang.String code4 = (java.lang.String) c00001.L$4;
                java.lang.String embedBase4 = (java.lang.String) c00001.L$3;
                java.lang.String embedFrameUrl4 = (java.lang.String) c00001.L$2;
                com.Jayboys.DetailsRoot details5 = (com.Jayboys.DetailsRoot) c00001.L$1;
                java.lang.String mainUrl4 = (java.lang.String) c00001.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                mainUrl2 = mainUrl4;
                postheaders = postheaders5;
                headers = headers4;
                code = code4;
                embedBase = embedBase4;
                embedFrameUrl = embedFrameUrl4;
                details3 = details5;
                i = 1;
                c000012 = c00001;
                obj = coroutine_suspended;
                playbackUrl = playbackUrl4;
                response = (com.lagradost.nicehttp.NiceResponse) $result;
                if (response.getCode() != 200) {
                }
                break;
            case 3:
                response2 = (com.lagradost.nicehttp.NiceResponse) c00001.L$8;
                postheaders2 = (java.util.Map) c00001.L$7;
                headers2 = (java.util.Map) c00001.L$6;
                playbackUrl2 = (java.lang.String) c00001.L$5;
                code2 = (java.lang.String) c00001.L$4;
                embedBase2 = (java.lang.String) c00001.L$3;
                embedFrameUrl2 = (java.lang.String) c00001.L$2;
                details4 = (com.Jayboys.DetailsRoot) c00001.L$1;
                kotlin.ResultKt.throwOnFailure($result);
                obj2 = null;
                com.lagradost.nicehttp.NiceResponse this_$iv2 = (com.lagradost.nicehttp.NiceResponse) $result;
                com.lagradost.nicehttp.ResponseParser parser22 = this_$iv2.getParser();
                kotlin.jvm.internal.Intrinsics.checkNotNull(parser22);
                safe2 = parser22.parseSafe(this_$iv2.getText(), kotlin.jvm.internal.Reflection.getOrCreateKotlinClass(com.Jayboys.PlaybackRoot.class));
                return (com.Jayboys.PlaybackRoot) safe2;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private final byte[] buildAesKey(com.Jayboys.Playback playback) {
        byte[] p1 = b64UrlDecode(playback.getKeyParts().get(0));
        byte[] p2 = b64UrlDecode(playback.getKeyParts().get(1));
        return kotlin.collections.ArraysKt.plus(p1, p2);
    }

    private final java.lang.String decryptPlayback(com.Jayboys.Playback playback) throws javax.crypto.BadPaddingException, javax.crypto.NoSuchPaddingException, javax.crypto.IllegalBlockSizeException, java.security.NoSuchAlgorithmException, java.security.InvalidKeyException, java.security.InvalidAlgorithmParameterException {
        java.lang.String jsonStr;
        java.lang.String str;
        com.fasterxml.jackson.databind.ObjectMapper $this$readValue$iv$iv$iv;
        java.util.List<com.Jayboys.PlaybackDecryptSource> sources;
        com.Jayboys.PlaybackDecryptSource playbackDecryptSource;
        byte[] keyBytes = buildAesKey(playback);
        byte[] ivBytes = b64UrlDecode(playback.getIv());
        byte[] cipherBytes = b64UrlDecode(playback.getPayload());
        javax.crypto.Cipher cipher = javax.crypto.Cipher.getInstance("AES/GCM/NoPadding");
        javax.crypto.spec.GCMParameterSpec spec = new javax.crypto.spec.GCMParameterSpec(128, ivBytes);
        javax.crypto.spec.SecretKeySpec secretKey = new javax.crypto.spec.SecretKeySpec(keyBytes, "AES");
        cipher.init(2, secretKey, spec);
        byte[] plainBytes = cipher.doFinal(cipherBytes);
        java.lang.String jsonStr2 = new java.lang.String(plainBytes, java.nio.charset.StandardCharsets.UTF_8);
        java.lang.Object value = null;
        if (kotlin.text.StringsKt.startsWith$default(jsonStr2, "\ufeff", false, 2, (java.lang.Object) null)) {
            jsonStr = jsonStr2.substring(1);
            kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(jsonStr, "substring(...)");
        } else {
            jsonStr = jsonStr2;
        }
        try {
            com.lagradost.cloudstream3.utils.AppUtils appUtils = com.lagradost.cloudstream3.utils.AppUtils.INSTANCE;
            java.lang.String value$iv = jsonStr;
            if (value$iv == null) {
                str = null;
            } else {
                try {
                    $this$readValue$iv$iv$iv = com.lagradost.cloudstream3.MainAPIKt.getMapper();
                    str = null;
                } catch (java.lang.Exception e) {
                    str = null;
                }
                try {
                    value = $this$readValue$iv$iv$iv.readValue(value$iv, new com.fasterxml.jackson.core.type.TypeReference<com.Jayboys.PlaybackDecrypt>() { // from class: com.Jayboys.ByseSX$decryptPlayback$$inlined$tryParseJson$1
                    });
                } catch (java.lang.Exception e2) {
                    value = str;
                }
            }
            try {
                com.Jayboys.PlaybackDecrypt root = (com.Jayboys.PlaybackDecrypt) value;
                return (root == null || (sources = root.getSources()) == null || (playbackDecryptSource = (com.Jayboys.PlaybackDecryptSource) kotlin.collections.CollectionsKt.firstOrNull(sources)) == null) ? str : playbackDecryptSource.getUrl();
            } catch (java.lang.Exception e3) {
                return str;
            }
        } catch (java.lang.Exception e4) {
            return null;
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:28:0x0133 A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0134  */
    /* JADX WARN: Removed duplicated region for block: B:33:0x014b A[LOOP:0: B:31:0x0145->B:33:0x014b, LOOP_END] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Jayboys.ByseSX $this, java.lang.String url, java.lang.String referer, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function1, kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function12, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        com.Jayboys.ByseSX.C00011 c00011;
        java.lang.Object playback;
        java.lang.String refererUrl;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function13;
        java.lang.String referer2;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function14;
        java.lang.String url2;
        com.Jayboys.PlaybackRoot playbackRoot;
        java.lang.String streamUrl;
        java.lang.Object objGenerateM3u8$default;
        kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function15;
        com.Jayboys.ByseSX $this2 = $this;
        if (continuation instanceof com.Jayboys.ByseSX.C00011) {
            c00011 = (com.Jayboys.ByseSX.C00011) continuation;
            if ((c00011.label & Integer.MIN_VALUE) != 0) {
                c00011.label -= Integer.MIN_VALUE;
            } else {
                c00011 = $this2.new C00011(continuation);
            }
        }
        com.Jayboys.ByseSX.C00011 c000112 = c00011;
        java.lang.Object $result = c000112.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (c000112.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                java.lang.String refererUrl2 = $this.getBaseUrl(url);
                c000112.L$0 = $this2;
                c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function1);
                c000112.L$4 = function12;
                c000112.L$5 = refererUrl2;
                c000112.label = 1;
                playback = $this2.getPlayback(url, c000112);
                if (playback == coroutine_suspended) {
                    return coroutine_suspended;
                }
                refererUrl = refererUrl2;
                function13 = function12;
                referer2 = referer;
                function14 = function1;
                url2 = url;
                playbackRoot = (com.Jayboys.PlaybackRoot) playback;
                if (playbackRoot == null && (streamUrl = $this2.decryptPlayback(playbackRoot.getPlayback())) != null) {
                    java.util.Map headers = kotlin.collections.MapsKt.mapOf(kotlin.TuplesKt.to("Referer", refererUrl));
                    com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                    java.lang.String refererUrl3 = refererUrl;
                    java.lang.String refererUrl4 = $this2.getName();
                    java.lang.String mainUrl = $this2.getMainUrl();
                    c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                    c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                    c000112.L$4 = function13;
                    c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(refererUrl3);
                    c000112.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(playbackRoot);
                    c000112.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(streamUrl);
                    c000112.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(headers);
                    c000112.label = 2;
                    kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function16 = function13;
                    objGenerateM3u8$default = com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion, refererUrl4, streamUrl, mainUrl, (java.lang.Integer) null, headers, (java.lang.String) null, c000112, 40, (java.lang.Object) null);
                    if (objGenerateM3u8$default != coroutine_suspended) {
                        return coroutine_suspended;
                    }
                    function15 = function16;
                    java.lang.Iterable $this$forEach$iv = (java.lang.Iterable) objGenerateM3u8$default;
                    for (java.lang.Object element$iv : $this$forEach$iv) {
                        function15.invoke(element$iv);
                    }
                    return kotlin.Unit.INSTANCE;
                }
                return kotlin.Unit.INSTANCE;
            case 1:
                java.lang.String refererUrl5 = (java.lang.String) c000112.L$5;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function17 = (kotlin.jvm.functions.Function1) c000112.L$4;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.SubtitleFile, kotlin.Unit> function18 = (kotlin.jvm.functions.Function1) c000112.L$3;
                java.lang.String referer3 = (java.lang.String) c000112.L$2;
                java.lang.String url3 = (java.lang.String) c000112.L$1;
                $this2 = (com.Jayboys.ByseSX) c000112.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                refererUrl = refererUrl5;
                function13 = function17;
                function14 = function18;
                referer2 = referer3;
                url2 = url3;
                playback = $result;
                playbackRoot = (com.Jayboys.PlaybackRoot) playback;
                if (playbackRoot == null) {
                    return kotlin.Unit.INSTANCE;
                }
                java.util.Map headers2 = kotlin.collections.MapsKt.mapOf(kotlin.TuplesKt.to("Referer", refererUrl));
                com.lagradost.cloudstream3.utils.M3u8Helper.Companion companion2 = com.lagradost.cloudstream3.utils.M3u8Helper.Companion;
                java.lang.String refererUrl32 = refererUrl;
                java.lang.String refererUrl42 = $this2.getName();
                java.lang.String mainUrl2 = $this2.getMainUrl();
                c000112.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                c000112.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                c000112.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                c000112.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(function14);
                c000112.L$4 = function13;
                c000112.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(refererUrl32);
                c000112.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(playbackRoot);
                c000112.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(streamUrl);
                c000112.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(headers2);
                c000112.label = 2;
                kotlin.jvm.functions.Function1<? super com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.Unit> function162 = function13;
                objGenerateM3u8$default = com.lagradost.cloudstream3.utils.M3u8Helper.Companion.generateM3u8$default(companion2, refererUrl42, streamUrl, mainUrl2, (java.lang.Integer) null, headers2, (java.lang.String) null, c000112, 40, (java.lang.Object) null);
                if (objGenerateM3u8$default != coroutine_suspended) {
                }
                break;
            case 2:
                function15 = (kotlin.jvm.functions.Function1) c000112.L$4;
                kotlin.ResultKt.throwOnFailure($result);
                objGenerateM3u8$default = $result;
                java.lang.Iterable $this$forEach$iv2 = (java.lang.Iterable) objGenerateM3u8$default;
                while (r13.hasNext()) {
                }
                return kotlin.Unit.INSTANCE;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
