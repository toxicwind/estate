package com.Gaypornvidsxxx;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\b\b\u0016\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u000e\u001a\n\u0012\u0004\u0012\u00020\u0010\u0018\u00010\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013J\u0010\u0010\u0014\u001a\u00020\u00052\u0006\u0010\u0015\u001a\u00020\u0005H\u0002J\u0014\u0010\u0016\u001a\u0004\u0018\u00010\u00052\b\u0010\u0017\u001a\u0004\u0018\u00010\u0005H\u0002R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0018"}, d2 = {"Lcom/Gaypornvidsxxx/Base64Extractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "customBase64Decoder", "encodedString", "getEncodedString", "json", "Gaypornvidsxxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
public class Base64Extractor extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Base64";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "base64";

    /* JADX INFO: renamed from: com.Gaypornvidsxxx.Base64Extractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaypornvidsxxx.Base64Extractor", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {184, 228}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "document", "script", "pattern", "matchResult", "jsonArray", "encodedString", "decodedString", "videos", "externalLinkList", "video", "quality", "format", "videoUrl", "isVHQ", "i", "isM3u8"}, nl = {189, 227}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$12", "L$13", "L$14", "L$15", "I$0", "I$1", "I$3"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
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
        java.lang.Object L$15;
        java.lang.Object L$16;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaypornvidsxxx.Base64Extractor.getUrl$suspendImpl(com.Gaypornvidsxxx.Base64Extractor.this, null, null, (kotlin.coroutines.Continuation) this);
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

    /* JADX WARN: Path cross not found for [B:33:0x0174, B:38:0x0186], limit reached: 70 */
    /* JADX WARN: Removed duplicated region for block: B:20:0x0146  */
    /* JADX WARN: Removed duplicated region for block: B:21:0x014b  */
    /* JADX WARN: Removed duplicated region for block: B:29:0x0168  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x016b  */
    /* JADX WARN: Removed duplicated region for block: B:42:0x018e A[RETURN] */
    /* JADX WARN: Removed duplicated region for block: B:43:0x018f  */
    /* JADX WARN: Removed duplicated region for block: B:45:0x01d4  */
    /* JADX WARN: Removed duplicated region for block: B:65:0x0329  */
    /* JADX WARN: Removed duplicated region for block: B:66:0x034d  */
    /* JADX WARN: Removed duplicated region for block: B:67:0x0361  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:62:0x0309 -> B:63:0x0324). Please report as a decompilation issue!!! */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gaypornvidsxxx.Base64Extractor $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) throws org.json.JSONException {
        com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1 anonymousClass1;
        java.lang.String str;
        java.lang.Object $result;
        com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1 anonymousClass12;
        java.lang.Object obj;
        int i;
        java.lang.String referer2;
        java.lang.String url2;
        java.lang.String referer3;
        java.lang.Object obj2;
        com.Gaypornvidsxxx.Base64Extractor $this2;
        java.lang.String script;
        int i2;
        kotlin.text.MatchResult matchResult;
        java.lang.String jsonArray;
        java.lang.String encodedString;
        org.json.JSONArray videos;
        kotlin.text.MatchGroupCollection groups;
        org.jsoup.nodes.Document document;
        kotlin.text.MatchResult matchResult2;
        java.lang.String script2;
        java.lang.String str2;
        kotlin.text.Regex pattern;
        int i3;
        java.lang.String jsonArray2;
        com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1 anonymousClass13;
        com.Gaypornvidsxxx.Base64Extractor $this3;
        java.lang.Object obj3;
        java.lang.String encodedString2;
        int i4;
        java.lang.Object $result2;
        java.util.List externalLinkList;
        java.util.List list;
        java.lang.String decodedString;
        int i5;
        int i6;
        kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation2;
        java.lang.String videoUrl;
        java.lang.String url3;
        if (continuation instanceof com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1) {
            anonymousClass1 = (com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result3 = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result3);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = $this;
                anonymousClass1.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass1.label = 1;
                str = "";
                $result = $result3;
                anonymousClass12 = anonymousClass1;
                obj = coroutine_suspended;
                i = 2;
                referer2 = null;
                java.lang.Object obj4 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                if (obj4 == obj) {
                    return obj;
                }
                url2 = url;
                referer3 = referer;
                obj2 = obj4;
                $this2 = $this;
                org.jsoup.nodes.Document document2 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementFirst = document2.selectXpath("//script[contains(text(),'let vpage_data')]").first();
                script = elementFirst == null ? elementFirst.html() : referer2;
                i2 = 0;
                if (script != null && kotlin.text.StringsKt.contains$default(script, "VHQ", false, i, referer2)) {
                    i2 = 1;
                }
                kotlin.text.Regex pattern2 = new kotlin.text.Regex("window\\.initPlayer\\((.*])\\);");
                matchResult = kotlin.text.Regex.find$default(pattern2, script != null ? str : script, 0, i, referer2);
                if (matchResult == null && (groups = matchResult.getGroups()) != null) {
                    kotlin.text.MatchGroup matchGroup = groups.get(1);
                    if (matchGroup != null) {
                        jsonArray = matchGroup.getValue();
                    }
                    encodedString = $this2.getEncodedString(jsonArray);
                    if (encodedString == null) {
                        return referer2;
                    }
                    java.lang.String decodedString2 = $this2.customBase64Decoder(encodedString);
                    org.json.JSONArray videos2 = new org.json.JSONObject("{ videos:" + decodedString2 + '}').getJSONArray("videos");
                    java.util.ArrayList externalLinkList2 = new java.util.ArrayList();
                    int length = videos2.length();
                    java.lang.Object obj5 = obj;
                    videos = videos2;
                    int i7 = i2;
                    java.lang.Object obj6 = obj5;
                    kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation3 = continuation;
                    java.lang.String url4 = url2;
                    int i8 = 0;
                    com.Gaypornvidsxxx.Base64Extractor.AnonymousClass1 anonymousClass14 = anonymousClass12;
                    int i9 = length;
                    if (i8 >= i9) {
                        java.lang.String referer4 = referer3;
                        org.json.JSONObject video = videos.getJSONObject(i8);
                        kotlin.jvm.internal.Ref.IntRef quality = new kotlin.jvm.internal.Ref.IntRef();
                        document = document2;
                        matchResult2 = matchResult;
                        quality.element = com.lagradost.cloudstream3.utils.Qualities.Unknown.getValue();
                        script2 = script;
                        java.lang.String script3 = str;
                        java.lang.String format = video.optString("format", script3);
                        str2 = script3;
                        pattern = pattern2;
                        if (kotlin.text.StringsKt.contains(format, "lq", true)) {
                            quality.element = com.lagradost.cloudstream3.utils.Qualities.P480.getValue();
                        } else if (kotlin.text.StringsKt.contains(format, "hq", true)) {
                            quality.element = com.lagradost.cloudstream3.utils.Qualities.P720.getValue();
                        }
                        java.lang.String videoUrl2 = $this2.customBase64Decoder(video.getString("video_url"));
                        if (i7 == 0) {
                            i3 = 0;
                        } else {
                            videoUrl2 = videoUrl2 + "&f=video.m3u8";
                            i3 = 1;
                            quality.element = com.lagradost.cloudstream3.utils.Qualities.Unknown.getValue();
                        }
                        jsonArray2 = jsonArray;
                        com.lagradost.api.Log.INSTANCE.d("Base64Extractor", "Decoded video URL = " + videoUrl2);
                        java.lang.String name = $this2.getName();
                        java.lang.String name2 = $this2.getName();
                        java.lang.String strFixUrl = com.lagradost.cloudstream3.utils.ExtractorApiKt.fixUrl($this2, videoUrl2);
                        com.lagradost.cloudstream3.utils.ExtractorLinkType extractorLinkType = i3 != 0 ? com.lagradost.cloudstream3.utils.ExtractorLinkType.M3U8 : com.lagradost.cloudstream3.utils.ExtractorLinkType.VIDEO;
                        com.Gaypornvidsxxx.Base64Extractor.AnonymousClass2 anonymousClass2 = $this2.new AnonymousClass2(quality, null);
                        anonymousClass14.L$0 = $this2;
                        anonymousClass14.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url4);
                        anonymousClass14.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer4);
                        anonymousClass14.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                        anonymousClass14.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(script2);
                        anonymousClass14.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pattern);
                        anonymousClass14.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(matchResult2);
                        anonymousClass14.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(jsonArray2);
                        anonymousClass14.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(encodedString);
                        anonymousClass14.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(decodedString2);
                        anonymousClass14.L$10 = videos;
                        anonymousClass14.L$11 = externalLinkList2;
                        anonymousClass14.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(video);
                        anonymousClass14.L$13 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                        anonymousClass14.L$14 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(format);
                        anonymousClass14.L$15 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl2);
                        anonymousClass14.L$16 = externalLinkList2;
                        anonymousClass14.I$0 = i7;
                        anonymousClass14.I$1 = i8;
                        anonymousClass14.I$2 = i9;
                        anonymousClass14.I$3 = i3;
                        anonymousClass14.label = 2;
                        anonymousClass13 = anonymousClass14;
                        java.lang.Object objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, name2, strFixUrl, extractorLinkType, anonymousClass2, anonymousClass13);
                        if (objNewExtractorLink == obj6) {
                            return obj6;
                        }
                        $this3 = $this2;
                        $result3 = objNewExtractorLink;
                        obj3 = obj6;
                        encodedString2 = encodedString;
                        i4 = i9;
                        $result2 = $result;
                        externalLinkList = externalLinkList2;
                        list = externalLinkList;
                        decodedString = decodedString2;
                        i5 = i8;
                        i6 = i7;
                        continuation2 = continuation3;
                        videoUrl = referer4;
                        url3 = url4;
                        list.add($result3);
                        if (i6 != 0) {
                            int i10 = i5 + 1;
                            continuation3 = continuation2;
                            url4 = url3;
                            referer3 = videoUrl;
                            externalLinkList2 = externalLinkList;
                            obj6 = obj3;
                            i7 = i6;
                            encodedString = encodedString2;
                            matchResult = matchResult2;
                            document2 = document;
                            decodedString2 = decodedString;
                            i9 = i4;
                            $result = $result2;
                            script = script2;
                            str = str2;
                            pattern2 = pattern;
                            jsonArray = jsonArray2;
                            i8 = i10;
                            $this2 = $this3;
                            anonymousClass14 = anonymousClass13;
                            if (i8 >= i9) {
                                return externalLinkList2;
                            }
                        } else {
                            return externalLinkList;
                        }
                    }
                }
                jsonArray = referer2;
                encodedString = $this2.getEncodedString(jsonArray);
                if (encodedString == null) {
                }
                break;
            case 1:
                java.lang.String referer5 = (java.lang.String) anonymousClass1.L$2;
                url2 = (java.lang.String) anonymousClass1.L$1;
                com.Gaypornvidsxxx.Base64Extractor $this4 = (com.Gaypornvidsxxx.Base64Extractor) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result3);
                anonymousClass12 = anonymousClass1;
                $result = $result3;
                obj = coroutine_suspended;
                str = "";
                $this2 = $this4;
                referer3 = referer5;
                obj2 = $result;
                i = 2;
                referer2 = null;
                org.jsoup.nodes.Document document22 = ((com.lagradost.nicehttp.NiceResponse) obj2).getDocument();
                org.jsoup.nodes.Element elementFirst2 = document22.selectXpath("//script[contains(text(),'let vpage_data')]").first();
                if (elementFirst2 == null) {
                }
                i2 = 0;
                if (script != null) {
                    i2 = 1;
                }
                kotlin.text.Regex pattern22 = new kotlin.text.Regex("window\\.initPlayer\\((.*])\\);");
                matchResult = kotlin.text.Regex.find$default(pattern22, script != null ? str : script, 0, i, referer2);
                if (matchResult == null) {
                }
                jsonArray = referer2;
                encodedString = $this2.getEncodedString(jsonArray);
                if (encodedString == null) {
                }
                break;
            case 2:
                int i11 = anonymousClass1.I$3;
                int i12 = anonymousClass1.I$2;
                int i13 = anonymousClass1.I$1;
                i6 = anonymousClass1.I$0;
                java.util.List list2 = (java.util.List) anonymousClass1.L$16;
                externalLinkList = (java.util.List) anonymousClass1.L$11;
                org.json.JSONArray videos3 = (org.json.JSONArray) anonymousClass1.L$10;
                decodedString = (java.lang.String) anonymousClass1.L$9;
                java.lang.String encodedString3 = (java.lang.String) anonymousClass1.L$8;
                java.lang.String jsonArray3 = (java.lang.String) anonymousClass1.L$7;
                kotlin.text.MatchResult matchResult3 = (kotlin.text.MatchResult) anonymousClass1.L$6;
                kotlin.text.Regex pattern3 = (kotlin.text.Regex) anonymousClass1.L$5;
                java.lang.String script4 = (java.lang.String) anonymousClass1.L$4;
                org.jsoup.nodes.Document document3 = (org.jsoup.nodes.Document) anonymousClass1.L$3;
                java.lang.String referer6 = (java.lang.String) anonymousClass1.L$2;
                java.lang.String url5 = (java.lang.String) anonymousClass1.L$1;
                com.Gaypornvidsxxx.Base64Extractor $this5 = (com.Gaypornvidsxxx.Base64Extractor) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result3);
                anonymousClass13 = anonymousClass1;
                str2 = "";
                videos = videos3;
                encodedString2 = encodedString3;
                jsonArray2 = jsonArray3;
                matchResult2 = matchResult3;
                pattern = pattern3;
                script2 = script4;
                document = document3;
                $result2 = $result3;
                i4 = i12;
                i5 = i13;
                obj3 = coroutine_suspended;
                list = list2;
                $this3 = $this5;
                continuation2 = continuation;
                url3 = url5;
                videoUrl = referer6;
                list.add($result3);
                if (i6 != 0) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: renamed from: com.Gaypornvidsxxx.Base64Extractor$getUrl$2, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;"}, k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaypornvidsxxx.Base64Extractor$getUrl$2", f = "Extractors.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, nl = {}, s = {}, v = 2)
    static final class AnonymousClass2 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<com.lagradost.cloudstream3.utils.ExtractorLink, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
        final /* synthetic */ kotlin.jvm.internal.Ref.IntRef $quality;
        private /* synthetic */ java.lang.Object L$0;
        int label;

        /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
        AnonymousClass2(kotlin.jvm.internal.Ref.IntRef intRef, kotlin.coroutines.Continuation<? super com.Gaypornvidsxxx.Base64Extractor.AnonymousClass2> continuation) {
            super(2, continuation);
            this.$quality = intRef;
        }

        public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
            kotlin.coroutines.Continuation<kotlin.Unit> anonymousClass2 = com.Gaypornvidsxxx.Base64Extractor.this.new AnonymousClass2(this.$quality, continuation);
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
                    $this$newExtractorLink.setReferer(com.Gaypornvidsxxx.Base64Extractor.this.getMainUrl());
                    $this$newExtractorLink.setQuality(this.$quality.element);
                    return kotlin.Unit.INSTANCE;
                default:
                    throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
            }
        }
    }

    private final java.lang.String customBase64Decoder(java.lang.String encodedString) {
        java.lang.String decodedString = "";
        int firstCharIndex = 0;
        java.lang.String sanitizedString = new kotlin.text.Regex("[^АВСЕМA-Za-z0-9.,~]").replace(encodedString, "");
        while (firstCharIndex + 3 < sanitizedString.length()) {
            int currentIndex = firstCharIndex + 1;
            int firstCharIndex2 = kotlin.text.StringsKt.indexOf$default("АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~", sanitizedString.charAt(firstCharIndex), 0, false, 6, (java.lang.Object) null);
            int currentIndex2 = currentIndex + 1;
            int secondCharIndex = kotlin.text.StringsKt.indexOf$default("АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~", sanitizedString.charAt(currentIndex), 0, false, 6, (java.lang.Object) null);
            int currentIndex3 = currentIndex2 + 1;
            int thirdCharIndex = kotlin.text.StringsKt.indexOf$default("АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~", sanitizedString.charAt(currentIndex2), 0, false, 6, (java.lang.Object) null);
            int currentIndex4 = currentIndex3 + 1;
            int fourthCharIndex = kotlin.text.StringsKt.indexOf$default("АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~", sanitizedString.charAt(currentIndex3), 0, false, 6, (java.lang.Object) null);
            int reconstructedFirstChar = (firstCharIndex2 << 2) | (secondCharIndex >> 4);
            int reconstructedSecondChar = ((secondCharIndex & 15) << 4) | (thirdCharIndex >> 2);
            int lastPart = ((thirdCharIndex & 3) << 6) | fourthCharIndex;
            decodedString = decodedString + ((char) reconstructedFirstChar);
            if (thirdCharIndex != 64) {
                decodedString = decodedString + ((char) reconstructedSecondChar);
            }
            if (fourthCharIndex == 64) {
                firstCharIndex = currentIndex4;
            } else {
                decodedString = decodedString + ((char) lastPart);
                firstCharIndex = currentIndex4;
            }
        }
        return java.net.URLDecoder.decode(decodedString, "UTF-8");
    }

    private final java.lang.String getEncodedString(java.lang.String json) {
        kotlin.text.MatchGroupCollection groups;
        kotlin.text.MatchGroup matchGroup;
        kotlin.text.Regex stringPattern = new kotlin.text.Regex("'([^']+)',");
        kotlin.text.MatchResult matchResultFind$default = kotlin.text.Regex.find$default(stringPattern, json == null ? "" : json, 0, 2, (java.lang.Object) null);
        if (matchResultFind$default == null || (groups = matchResultFind$default.getGroups()) == null || (matchGroup = groups.get(1)) == null) {
            return null;
        }
        return matchGroup.getValue();
    }
}
