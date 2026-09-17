package com.Gaypornvidsxxx;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0005\b\u0016\u0018\u00002\u00020\u0001:\u0001\u0014B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u00100\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0015"}, d2 = {"Lcom/Gaypornvidsxxx/VoeExtractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "VideoSource", "Gaypornvidsxxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractors.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractors.kt\ncom/Gaypornvidsxxx/VoeExtractor\n+ 2 AppUtils.kt\ncom/lagradost/cloudstream3/utils/AppUtils\n+ 3 Extensions.kt\ncom/fasterxml/jackson/module/kotlin/ExtensionsKt\n*L\n1#1,297:1\n23#2,2:298\n15#2:300\n25#2,2:303\n50#3:301\n43#3:302\n*S KotlinDebug\n*F\n+ 1 Extractors.kt\ncom/Gaypornvidsxxx/VoeExtractor\n*L\n86#1:298,2\n86#1:300\n86#1:303,2\n86#1:301\n86#1:302\n*E\n"})
public class VoeExtractor extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Voe";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://jilliandescribecompany.com";

    /* JADX INFO: renamed from: com.Gaypornvidsxxx.VoeExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gaypornvidsxxx.VoeExtractor", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {77, 89}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response", "jsonMatch", "source", "videoUrl", "$i$a$-let-VoeExtractor$getUrl$2", "$i$a$-let-VoeExtractor$getUrl$2$1"}, nl = {78, 88}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "I$0", "I$1"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        java.lang.Object L$6;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gaypornvidsxxx.VoeExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gaypornvidsxxx.VoeExtractor.getUrl$suspendImpl(com.Gaypornvidsxxx.VoeExtractor.this, null, null, (kotlin.coroutines.Continuation) this);
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

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(d1 = {"\u0000 \n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0000\n\u0002\u0010\b\n\u0002\b\f\n\u0002\u0010\u000b\n\u0002\b\u0004\b\u0082\b\u0018\u00002\u00020\u0001B\u001f\u0012\n\b\u0001\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0001\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\u0004\b\u0006\u0010\u0007J\u000b\u0010\r\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u0010\u0010\u000e\u001a\u0004\u0018\u00010\u0005HÆ\u0003¢\u0006\u0002\u0010\u000bJ&\u0010\u000f\u001a\u00020\u00002\n\b\u0003\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0003\u0010\u0004\u001a\u0004\u0018\u00010\u0005HÆ\u0001¢\u0006\u0002\u0010\u0010J\u0014\u0010\u0011\u001a\u00020\u00122\b\u0010\u0013\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0014\u001a\u00020\u0005HÖ\u0081\u0004J\n\u0010\u0015\u001a\u00020\u0003HÖ\u0081\u0004R\u0018\u0010\u0002\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u001a\u0010\u0004\u001a\u0004\u0018\u00010\u00058\u0006X\u0087\u0004¢\u0006\n\n\u0002\u0010\f\u001a\u0004\b\n\u0010\u000b¨\u0006\u0016"}, d2 = {"Lcom/Gaypornvidsxxx/VoeExtractor$VideoSource;", "", "url", "", "height", "", "<init>", "(Ljava/lang/String;Ljava/lang/Integer;)V", "getUrl", "()Ljava/lang/String;", "getHeight", "()Ljava/lang/Integer;", "Ljava/lang/Integer;", "component1", "component2", "copy", "(Ljava/lang/String;Ljava/lang/Integer;)Lcom/Gaypornvidsxxx/VoeExtractor$VideoSource;", "equals", "", "other", "hashCode", "toString", "Gaypornvidsxxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
    static final /* data */ class VideoSource {

        @com.fasterxml.jackson.annotation.JsonProperty("video_height")
        @org.jetbrains.annotations.Nullable
        private final java.lang.Integer height;

        @com.fasterxml.jackson.annotation.JsonProperty("hls")
        @org.jetbrains.annotations.Nullable
        private final java.lang.String url;

        public static /* synthetic */ com.Gaypornvidsxxx.VoeExtractor.VideoSource copy$default(com.Gaypornvidsxxx.VoeExtractor.VideoSource videoSource, java.lang.String str, java.lang.Integer num, int i, java.lang.Object obj) {
            if ((i & 1) != 0) {
                str = videoSource.url;
            }
            if ((i & 2) != 0) {
                num = videoSource.height;
            }
            return videoSource.copy(str, num);
        }

        @org.jetbrains.annotations.Nullable
        /* JADX INFO: renamed from: component1, reason: from getter */
        public final java.lang.String getUrl() {
            return this.url;
        }

        @org.jetbrains.annotations.Nullable
        /* JADX INFO: renamed from: component2, reason: from getter */
        public final java.lang.Integer getHeight() {
            return this.height;
        }

        @org.jetbrains.annotations.NotNull
        public final com.Gaypornvidsxxx.VoeExtractor.VideoSource copy(@com.fasterxml.jackson.annotation.JsonProperty("hls") @org.jetbrains.annotations.Nullable java.lang.String url, @com.fasterxml.jackson.annotation.JsonProperty("video_height") @org.jetbrains.annotations.Nullable java.lang.Integer height) {
            return new com.Gaypornvidsxxx.VoeExtractor.VideoSource(url, height);
        }

        public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
            if (this == other) {
                return true;
            }
            if (!(other instanceof com.Gaypornvidsxxx.VoeExtractor.VideoSource)) {
                return false;
            }
            com.Gaypornvidsxxx.VoeExtractor.VideoSource videoSource = (com.Gaypornvidsxxx.VoeExtractor.VideoSource) other;
            return kotlin.jvm.internal.Intrinsics.areEqual(this.url, videoSource.url) && kotlin.jvm.internal.Intrinsics.areEqual(this.height, videoSource.height);
        }

        public int hashCode() {
            return ((this.url == null ? 0 : this.url.hashCode()) * 31) + (this.height != null ? this.height.hashCode() : 0);
        }

        @org.jetbrains.annotations.NotNull
        public java.lang.String toString() {
            return "VideoSource(url=" + this.url + ", height=" + this.height + ')';
        }

        public VideoSource(@com.fasterxml.jackson.annotation.JsonProperty("hls") @org.jetbrains.annotations.Nullable java.lang.String url, @com.fasterxml.jackson.annotation.JsonProperty("video_height") @org.jetbrains.annotations.Nullable java.lang.Integer height) {
            this.url = url;
            this.height = height;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.String getUrl() {
            return this.url;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Integer getHeight() {
            return this.height;
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:20:0x00cb  */
    /* JADX WARN: Removed duplicated region for block: B:22:0x00d0  */
    /* JADX WARN: Removed duplicated region for block: B:45:0x01ab  */
    /* JADX WARN: Removed duplicated region for block: B:46:0x01b3  */
    /* JADX WARN: Removed duplicated region for block: B:56:? A[RETURN, SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gaypornvidsxxx.VoeExtractor $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gaypornvidsxxx.VoeExtractor.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        int i;
        java.lang.Object obj2;
        com.Gaypornvidsxxx.VoeExtractor $this2;
        java.lang.String url2;
        java.lang.String referer2;
        com.lagradost.nicehttp.NiceResponse response;
        java.util.List groupValues;
        java.lang.String str;
        java.lang.String jsonMatch;
        java.lang.Object value;
        java.lang.Object objNewExtractorLink$default;
        com.Gaypornvidsxxx.VoeExtractor.VideoSource source;
        com.Gaypornvidsxxx.VoeExtractor $this3;
        java.lang.String url3;
        java.lang.String referer3;
        com.lagradost.nicehttp.NiceResponse response2;
        java.lang.String jsonMatch2;
        int i2;
        java.util.List listEmptyList;
        if (continuation instanceof com.Gaypornvidsxxx.VoeExtractor.AnonymousClass1) {
            anonymousClass1 = (com.Gaypornvidsxxx.VoeExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Gaypornvidsxxx.VoeExtractor.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                obj = coroutine_suspended;
                i = 1;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                $this2 = $this;
                url2 = url;
                referer2 = referer;
                response = (com.lagradost.nicehttp.NiceResponse) obj2;
                if (response.getCode() != 404) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                kotlin.text.MatchResult matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("const\\s+sources\\s*=\\s*(\\{.*?\\});"), response.getText(), 0, 2, (java.lang.Object) null);
                if (matchResultFind$default == null || (groupValues = matchResultFind$default.getGroupValues()) == null || (str = (java.lang.String) groupValues.get(i)) == null || (jsonMatch = kotlin.text.StringsKt.replace$default(str, "0,", "0", false, 4, (java.lang.Object) null)) == null) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                com.lagradost.cloudstream3.utils.AppUtils appUtils = com.lagradost.cloudstream3.utils.AppUtils.INSTANCE;
                try {
                    com.fasterxml.jackson.databind.ObjectMapper $this$readValue$iv$iv$iv = com.lagradost.cloudstream3.MainAPIKt.getMapper();
                    value = $this$readValue$iv$iv$iv.readValue(jsonMatch, new com.fasterxml.jackson.core.type.TypeReference<com.Gaypornvidsxxx.VoeExtractor.VideoSource>() { // from class: com.Gaypornvidsxxx.VoeExtractor$getUrl$suspendImpl$$inlined$tryParseJson$1
                    });
                    break;
                } catch (java.lang.Exception e) {
                    value = null;
                }
                com.Gaypornvidsxxx.VoeExtractor.VideoSource source2 = (com.Gaypornvidsxxx.VoeExtractor.VideoSource) value;
                if (source2 != null) {
                    java.lang.String videoUrl = source2.getUrl();
                    if (videoUrl != null) {
                        java.lang.String name = $this2.getName();
                        java.lang.String name2 = $this2.getName();
                        com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                        anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                        anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                        anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                        anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                        anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(jsonMatch);
                        anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(source2);
                        anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl);
                        anonymousClass12.I$0 = 0;
                        anonymousClass12.I$1 = 0;
                        anonymousClass12.label = 2;
                        objNewExtractorLink$default = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name2, name, videoUrl, infer_type, (kotlin.jvm.functions.Function2) null, anonymousClass12, 16, (java.lang.Object) null);
                        if (objNewExtractorLink$default == obj) {
                            return obj;
                        }
                        source = source2;
                        $this3 = $this2;
                        url3 = url2;
                        referer3 = referer2;
                        response2 = response;
                        jsonMatch2 = jsonMatch;
                        i2 = 0;
                        listEmptyList = kotlin.collections.CollectionsKt.listOf(objNewExtractorLink$default);
                        if (listEmptyList != null) {
                            listEmptyList = kotlin.collections.CollectionsKt.emptyList();
                            if (listEmptyList != null) {
                                return listEmptyList;
                            }
                        } else if (listEmptyList != null) {
                        }
                    } else {
                        listEmptyList = kotlin.collections.CollectionsKt.emptyList();
                        if (listEmptyList != null) {
                        }
                    }
                }
                return kotlin.collections.CollectionsKt.emptyList();
            case 1:
                java.lang.String referer4 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url4 = (java.lang.String) anonymousClass12.L$1;
                com.Gaypornvidsxxx.VoeExtractor $this4 = (com.Gaypornvidsxxx.VoeExtractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                $this2 = $this4;
                obj = coroutine_suspended;
                referer2 = referer4;
                url2 = url4;
                i = 1;
                obj2 = $result;
                response = (com.lagradost.nicehttp.NiceResponse) obj2;
                if (response.getCode() != 404) {
                }
                break;
            case 2:
                int i3 = anonymousClass12.I$1;
                i2 = anonymousClass12.I$0;
                source = (com.Gaypornvidsxxx.VoeExtractor.VideoSource) anonymousClass12.L$5;
                jsonMatch2 = (java.lang.String) anonymousClass12.L$4;
                response2 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$3;
                referer3 = (java.lang.String) anonymousClass12.L$2;
                url3 = (java.lang.String) anonymousClass12.L$1;
                $this3 = (com.Gaypornvidsxxx.VoeExtractor) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink$default = $result;
                listEmptyList = kotlin.collections.CollectionsKt.listOf(objNewExtractorLink$default);
                if (listEmptyList != null) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
