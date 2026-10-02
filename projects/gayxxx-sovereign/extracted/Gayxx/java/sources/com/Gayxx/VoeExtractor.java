package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0006\u0018\u00002\u00020\u0001:\u0002\u0016\u0017B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u0010\u001a\b\u0012\u0004\u0012\u00020\u00120\u00112\u0006\u0010\u0013\u001a\u00020\u00052\b\u0010\u0014\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0015R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0094D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u0005X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\u0007R\u0014\u0010\f\u001a\u00020\rX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\u000f¨\u0006\u0018"}, d2 = {"Lcom/Gayxx/VoeExtractor;", "Lcom/Gayxx/BaseVideoExtractor;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "domain", "getDomain", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "VideoSource", "dsio", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/VoeExtractor\n+ 2 AppUtils.kt\ncom/lagradost/cloudstream3/utils/AppUtils\n+ 3 Extensions.kt\ncom/fasterxml/jackson/module/kotlin/ExtensionsKt\n*L\n1#1,451:1\n23#2,2:452\n15#2:454\n25#2,2:457\n50#3:455\n43#3:456\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/VoeExtractor\n*L\n50#1:452,2\n50#1:454\n50#1:457,2\n50#1:455\n50#1:456\n*E\n"})
public final class VoeExtractor extends com.Gayxx.BaseVideoExtractor {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Voe";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String domain = "jilliandescribecompany.com";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://" + getDomain() + "/e";

    /* JADX INFO: renamed from: com.Gayxx.VoeExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.VoeExtractor", f = "Extractor.kt", i = {0, 0, 1, 1, 1, 1, 1, 1, 1, 1}, l = {41, 53}, m = "getUrl", n = {"url", "referer", "url", "referer", "response", "jsonMatch", "source", "videoUrl", "$i$a$-let-VoeExtractor$getUrl$2", "$i$a$-let-VoeExtractor$getUrl$2$1"}, nl = {42, 52}, s = {"L$0", "L$1", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "I$0", "I$1"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$2;
        java.lang.Object L$3;
        java.lang.Object L$4;
        java.lang.Object L$5;
        int label;
        /* synthetic */ java.lang.Object result;

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.VoeExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.VoeExtractor.this.getUrl(null, null, (kotlin.coroutines.Continuation) this);
        }
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String getName() {
        return this.name;
    }

    @Override // com.Gayxx.BaseVideoExtractor
    @org.jetbrains.annotations.NotNull
    protected java.lang.String getDomain() {
        return this.domain;
    }

    @Override // com.Gayxx.BaseVideoExtractor
    @org.jetbrains.annotations.NotNull
    public java.lang.String getMainUrl() {
        return this.mainUrl;
    }

    public boolean getRequiresReferer() {
        return this.requiresReferer;
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(d1 = {"\u0000 \n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0000\n\u0002\u0010\b\n\u0002\b\f\n\u0002\u0010\u000b\n\u0002\b\u0004\b\u0082\b\u0018\u00002\u00020\u0001B\u001f\u0012\n\b\u0001\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0001\u0010\u0004\u001a\u0004\u0018\u00010\u0005¢\u0006\u0004\b\u0006\u0010\u0007J\u000b\u0010\r\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u0010\u0010\u000e\u001a\u0004\u0018\u00010\u0005HÆ\u0003¢\u0006\u0002\u0010\u000bJ&\u0010\u000f\u001a\u00020\u00002\n\b\u0003\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0003\u0010\u0004\u001a\u0004\u0018\u00010\u0005HÆ\u0001¢\u0006\u0002\u0010\u0010J\u0014\u0010\u0011\u001a\u00020\u00122\b\u0010\u0013\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0014\u001a\u00020\u0005HÖ\u0081\u0004J\n\u0010\u0015\u001a\u00020\u0003HÖ\u0081\u0004R\u0018\u0010\u0002\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u001a\u0010\u0004\u001a\u0004\u0018\u00010\u00058\u0006X\u0087\u0004¢\u0006\n\n\u0002\u0010\f\u001a\u0004\b\n\u0010\u000b¨\u0006\u0016"}, d2 = {"Lcom/Gayxx/VoeExtractor$VideoSource;", "", "url", "", "height", "", "<init>", "(Ljava/lang/String;Ljava/lang/Integer;)V", "getUrl", "()Ljava/lang/String;", "getHeight", "()Ljava/lang/Integer;", "Ljava/lang/Integer;", "component1", "component2", "copy", "(Ljava/lang/String;Ljava/lang/Integer;)Lcom/Gayxx/VoeExtractor$VideoSource;", "equals", "", "other", "hashCode", "toString", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
    static final /* data */ class VideoSource {

        @com.fasterxml.jackson.annotation.JsonProperty("video_height")
        @org.jetbrains.annotations.Nullable
        private final java.lang.Integer height;

        @com.fasterxml.jackson.annotation.JsonProperty("hls")
        @org.jetbrains.annotations.Nullable
        private final java.lang.String url;

        public static /* synthetic */ com.Gayxx.VoeExtractor.VideoSource copy$default(com.Gayxx.VoeExtractor.VideoSource videoSource, java.lang.String str, java.lang.Integer num, int i, java.lang.Object obj) {
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
        public final com.Gayxx.VoeExtractor.VideoSource copy(@com.fasterxml.jackson.annotation.JsonProperty("hls") @org.jetbrains.annotations.Nullable java.lang.String url, @com.fasterxml.jackson.annotation.JsonProperty("video_height") @org.jetbrains.annotations.Nullable java.lang.Integer height) {
            return new com.Gayxx.VoeExtractor.VideoSource(url, height);
        }

        public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
            if (this == other) {
                return true;
            }
            if (!(other instanceof com.Gayxx.VoeExtractor.VideoSource)) {
                return false;
            }
            com.Gayxx.VoeExtractor.VideoSource videoSource = (com.Gayxx.VoeExtractor.VideoSource) other;
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

    /* JADX WARN: Removed duplicated region for block: B:20:0x00bf  */
    /* JADX WARN: Removed duplicated region for block: B:22:0x00c4  */
    /* JADX WARN: Removed duplicated region for block: B:45:0x0192  */
    /* JADX WARN: Removed duplicated region for block: B:46:0x0198  */
    /* JADX WARN: Removed duplicated region for block: B:61:? A[RETURN, SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gayxx.VoeExtractor.AnonymousClass1 anonymousClass1;
        com.Gayxx.VoeExtractor voeExtractor;
        int i;
        java.lang.Object obj;
        java.lang.String url2;
        java.lang.String referer2;
        com.lagradost.nicehttp.NiceResponse response;
        java.util.List groupValues;
        java.lang.String str;
        java.lang.String jsonMatch;
        java.lang.Object value;
        com.Gayxx.VoeExtractor.VideoSource source;
        java.lang.String referer3;
        com.lagradost.nicehttp.NiceResponse response2;
        java.lang.String jsonMatch2;
        int i2;
        java.util.List listEmptyList;
        if (continuation instanceof com.Gayxx.VoeExtractor.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.VoeExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                voeExtractor = this;
            } else {
                voeExtractor = this;
                anonymousClass1 = voeExtractor.new AnonymousClass1(continuation);
            }
        }
        com.Gayxx.VoeExtractor.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                i = 1;
                obj = coroutine_suspended;
                $result = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if ($result == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                response = (com.lagradost.nicehttp.NiceResponse) $result;
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
                    value = $this$readValue$iv$iv$iv.readValue(jsonMatch, new com.fasterxml.jackson.core.type.TypeReference<com.Gayxx.VoeExtractor.VideoSource>() { // from class: com.Gayxx.VoeExtractor$getUrl$$inlined$tryParseJson$1
                    });
                    break;
                } catch (java.lang.Exception e) {
                    value = null;
                }
                com.Gayxx.VoeExtractor.VideoSource source2 = (com.Gayxx.VoeExtractor.VideoSource) value;
                if (source2 == null) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.lang.String videoUrl = source2.getUrl();
                if (videoUrl == null) {
                    listEmptyList = kotlin.collections.CollectionsKt.emptyList();
                    if (listEmptyList != null) {
                    }
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.lang.String name = voeExtractor.getName();
                java.lang.String name2 = voeExtractor.getName();
                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(jsonMatch);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(source2);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoUrl);
                anonymousClass12.I$0 = 0;
                anonymousClass12.I$1 = 0;
                anonymousClass12.label = 2;
                $result = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink$default(name2, name, videoUrl, infer_type, (kotlin.jvm.functions.Function2) null, anonymousClass12, 16, (java.lang.Object) null);
                if ($result == obj) {
                    return obj;
                }
                source = source2;
                referer3 = referer2;
                response2 = response;
                jsonMatch2 = jsonMatch;
                i2 = 0;
                listEmptyList = kotlin.collections.CollectionsKt.listOf($result);
                if (listEmptyList == null) {
                    if (listEmptyList != null) {
                    }
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                listEmptyList = kotlin.collections.CollectionsKt.emptyList();
                if (listEmptyList != null) {
                    return listEmptyList;
                }
                return kotlin.collections.CollectionsKt.emptyList();
            case 1:
                java.lang.String referer4 = (java.lang.String) anonymousClass12.L$1;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                referer2 = referer4;
                obj = coroutine_suspended;
                url2 = url3;
                i = 1;
                response = (com.lagradost.nicehttp.NiceResponse) $result;
                if (response.getCode() != 404) {
                }
                break;
            case 2:
                int i3 = anonymousClass12.I$1;
                i2 = anonymousClass12.I$0;
                source = (com.Gayxx.VoeExtractor.VideoSource) anonymousClass12.L$4;
                jsonMatch2 = (java.lang.String) anonymousClass12.L$3;
                response2 = (com.lagradost.nicehttp.NiceResponse) anonymousClass12.L$2;
                referer3 = (java.lang.String) anonymousClass12.L$1;
                kotlin.ResultKt.throwOnFailure($result);
                listEmptyList = kotlin.collections.CollectionsKt.listOf($result);
                if (listEmptyList == null) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u0010\u001a\n\u0012\u0004\u0012\u00020\u0012\u0018\u00010\u00112\u0006\u0010\u0013\u001a\u00020\u00052\b\u0010\u0014\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0015R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0094D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u0005X\u0096\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\u0007R\u0014\u0010\f\u001a\u00020\rX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\u000f¨\u0006\u0016"}, d2 = {"Lcom/Gayxx/VoeExtractor$dsio;", "Lcom/Gayxx/BaseVideoExtractor;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "domain", "getDomain", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
    @kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/VoeExtractor$dsio\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n*L\n1#1,451:1\n1586#2:452\n1661#2,3:453\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/VoeExtractor$dsio\n*L\n81#1:452\n81#1:453,3\n*E\n"})
    public static final class dsio extends com.Gayxx.BaseVideoExtractor {

        @org.jetbrains.annotations.NotNull
        private final java.lang.String name = "dsio";

        @org.jetbrains.annotations.NotNull
        private final java.lang.String domain = "d-s.io";

        @org.jetbrains.annotations.NotNull
        private final java.lang.String mainUrl = "https://" + getDomain();
        private final boolean requiresReferer = true;

        @org.jetbrains.annotations.NotNull
        public java.lang.String getName() {
            return this.name;
        }

        @Override // com.Gayxx.BaseVideoExtractor
        @org.jetbrains.annotations.NotNull
        protected java.lang.String getDomain() {
            return this.domain;
        }

        @Override // com.Gayxx.BaseVideoExtractor
        @org.jetbrains.annotations.NotNull
        public java.lang.String getMainUrl() {
            return this.mainUrl;
        }

        public boolean getRequiresReferer() {
            return this.requiresReferer;
        }

        /* JADX WARN: Removed duplicated region for block: B:26:0x018a A[RETURN] */
        /* JADX WARN: Removed duplicated region for block: B:27:0x018b  */
        /* JADX WARN: Removed duplicated region for block: B:31:0x01c0 A[LOOP:0: B:29:0x01ba->B:31:0x01c0, LOOP_END] */
        /* JADX WARN: Removed duplicated region for block: B:37:0x0298  */
        /* JADX WARN: Removed duplicated region for block: B:40:0x0308 A[RETURN] */
        /* JADX WARN: Removed duplicated region for block: B:41:0x0309  */
        /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
        @org.jetbrains.annotations.Nullable
        /*
            Code decompiled incorrectly, please refer to instructions dump.
        */
        public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
            com.Gayxx.VoeExtractor$dsio$getUrl$1 voeExtractor$dsio$getUrl$1;
            java.lang.Object obj;
            int i;
            int i2;
            java.lang.Object obj2;
            java.lang.String url2;
            java.lang.String referer2;
            java.lang.String response0;
            kotlin.text.MatchResult matchResultFind$default;
            java.lang.String passMd5Path;
            java.lang.Object obj3;
            java.lang.String url3;
            java.lang.String referer3;
            java.lang.String token;
            java.lang.String passMd5Path2;
            java.lang.String response02;
            java.lang.String md5Url;
            kotlin.collections.IntIterator it;
            java.lang.Object objNewExtractorLink;
            java.util.List groupValues;
            if (continuation instanceof com.Gayxx.VoeExtractor$dsio$getUrl$1) {
                voeExtractor$dsio$getUrl$1 = (com.Gayxx.VoeExtractor$dsio$getUrl$1) continuation;
                if ((voeExtractor$dsio$getUrl$1.label & Integer.MIN_VALUE) != 0) {
                    voeExtractor$dsio$getUrl$1.label -= Integer.MIN_VALUE;
                } else {
                    voeExtractor$dsio$getUrl$1 = new com.Gayxx.VoeExtractor$dsio$getUrl$1(this, continuation);
                }
            }
            com.Gayxx.VoeExtractor$dsio$getUrl$1 voeExtractor$dsio$getUrl$12 = voeExtractor$dsio$getUrl$1;
            java.lang.Object $result = voeExtractor$dsio$getUrl$12.result;
            java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
            switch (voeExtractor$dsio$getUrl$12.label) {
                case 0:
                    kotlin.ResultKt.throwOnFailure($result);
                    com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    voeExtractor$dsio$getUrl$12.L$0 = url;
                    voeExtractor$dsio$getUrl$12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                    voeExtractor$dsio$getUrl$12.label = 1;
                    obj = coroutine_suspended;
                    i = 2;
                    i2 = 0;
                    obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, voeExtractor$dsio$getUrl$12, 4094, (java.lang.Object) null);
                    voeExtractor$dsio$getUrl$12 = voeExtractor$dsio$getUrl$12;
                    if (obj2 == obj) {
                        return obj;
                    }
                    url2 = url;
                    referer2 = referer;
                    response0 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                    matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("/pass_md5/[^'\"]+"), response0, i2, i, (java.lang.Object) null);
                    if (matchResultFind$default == null && (passMd5Path = matchResultFind$default.getValue()) != null) {
                        java.lang.String token2 = kotlin.text.StringsKt.substringAfterLast$default(passMd5Path, "/", (java.lang.String) null, i, (java.lang.Object) null);
                        java.lang.String md5Url2 = getMainUrl() + passMd5Path;
                        com.lagradost.nicehttp.Requests app2 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                        voeExtractor$dsio$getUrl$12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                        voeExtractor$dsio$getUrl$12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                        voeExtractor$dsio$getUrl$12.L$2 = response0;
                        voeExtractor$dsio$getUrl$12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path);
                        voeExtractor$dsio$getUrl$12.L$4 = token2;
                        voeExtractor$dsio$getUrl$12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url2);
                        voeExtractor$dsio$getUrl$12.label = i;
                        com.Gayxx.VoeExtractor$dsio$getUrl$1 voeExtractor$dsio$getUrl$13 = voeExtractor$dsio$getUrl$12;
                        obj3 = com.lagradost.nicehttp.Requests.get$default(app2, md5Url2, (java.util.Map) null, url2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, voeExtractor$dsio$getUrl$13, 4090, (java.lang.Object) null);
                        voeExtractor$dsio$getUrl$12 = voeExtractor$dsio$getUrl$13;
                        if (obj3 != obj) {
                            return obj;
                        }
                        url3 = url2;
                        referer3 = referer2;
                        token = token2;
                        passMd5Path2 = passMd5Path;
                        response02 = response0;
                        md5Url = md5Url2;
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
                        java.lang.String link = videoData + randomStr + "?token=" + token + "&expiry=" + java.lang.System.currentTimeMillis();
                        kotlin.text.MatchResult matchResultFind$default2 = kotlin.text.Regex.find$default(new kotlin.text.Regex("(\\d{3,4})[pP]"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response02, "<title>", (java.lang.String) null, 2, (java.lang.Object) null), "</title>", (java.lang.String) null, 2, (java.lang.Object) null), 0, 2, (java.lang.Object) null);
                        java.lang.String quality = (matchResultFind$default2 != null || (groupValues = matchResultFind$default2.getGroupValues()) == null) ? null : (java.lang.String) groupValues.get(1);
                        java.lang.String videoData2 = getName();
                        java.lang.String name = getName();
                        com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                        com.Gayxx.VoeExtractor$dsio$getUrl$2 voeExtractor$dsio$getUrl$2 = new com.Gayxx.VoeExtractor$dsio$getUrl$2(this, quality, null);
                        voeExtractor$dsio$getUrl$12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                        voeExtractor$dsio$getUrl$12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                        voeExtractor$dsio$getUrl$12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                        voeExtractor$dsio$getUrl$12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path2);
                        voeExtractor$dsio$getUrl$12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token);
                        voeExtractor$dsio$getUrl$12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url);
                        voeExtractor$dsio$getUrl$12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(res);
                        voeExtractor$dsio$getUrl$12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoData);
                        voeExtractor$dsio$getUrl$12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(randomStr);
                        voeExtractor$dsio$getUrl$12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                        voeExtractor$dsio$getUrl$12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                        voeExtractor$dsio$getUrl$12.label = 3;
                        objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(videoData2, name, link, infer_type, voeExtractor$dsio$getUrl$2, voeExtractor$dsio$getUrl$12);
                        return objNewExtractorLink != obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
                    }
                    return null;
                case 1:
                    java.lang.String referer4 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$1;
                    java.lang.String url4 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$0;
                    kotlin.ResultKt.throwOnFailure($result);
                    obj = coroutine_suspended;
                    referer2 = referer4;
                    url2 = url4;
                    i = 2;
                    obj2 = $result;
                    i2 = 0;
                    response0 = ((com.lagradost.nicehttp.NiceResponse) obj2).getText();
                    matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("/pass_md5/[^'\"]+"), response0, i2, i, (java.lang.Object) null);
                    if (matchResultFind$default == null) {
                        return null;
                    }
                    java.lang.String token22 = kotlin.text.StringsKt.substringAfterLast$default(passMd5Path, "/", (java.lang.String) null, i, (java.lang.Object) null);
                    java.lang.String md5Url22 = getMainUrl() + passMd5Path;
                    com.lagradost.nicehttp.Requests app22 = com.lagradost.cloudstream3.MainActivityKt.getApp();
                    voeExtractor$dsio$getUrl$12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    voeExtractor$dsio$getUrl$12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    voeExtractor$dsio$getUrl$12.L$2 = response0;
                    voeExtractor$dsio$getUrl$12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path);
                    voeExtractor$dsio$getUrl$12.L$4 = token22;
                    voeExtractor$dsio$getUrl$12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url22);
                    voeExtractor$dsio$getUrl$12.label = i;
                    com.Gayxx.VoeExtractor$dsio$getUrl$1 voeExtractor$dsio$getUrl$132 = voeExtractor$dsio$getUrl$12;
                    obj3 = com.lagradost.nicehttp.Requests.get$default(app22, md5Url22, (java.util.Map) null, url2, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, voeExtractor$dsio$getUrl$132, 4090, (java.lang.Object) null);
                    voeExtractor$dsio$getUrl$12 = voeExtractor$dsio$getUrl$132;
                    if (obj3 != obj) {
                    }
                    break;
                case 2:
                    java.lang.String md5Url3 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$5;
                    token = (java.lang.String) voeExtractor$dsio$getUrl$12.L$4;
                    passMd5Path2 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$3;
                    response02 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$2;
                    referer3 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$1;
                    url3 = (java.lang.String) voeExtractor$dsio$getUrl$12.L$0;
                    kotlin.ResultKt.throwOnFailure($result);
                    obj = coroutine_suspended;
                    obj3 = $result;
                    md5Url = md5Url3;
                    com.lagradost.nicehttp.NiceResponse res2 = (com.lagradost.nicehttp.NiceResponse) obj3;
                    java.lang.String videoData3 = res2.getText();
                    java.lang.Iterable $this$map$iv2 = new kotlin.ranges.IntRange(1, 10);
                    java.util.Collection destination$iv$iv2 = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv2, 10));
                    java.lang.Iterable $this$mapTo$iv$iv2 = $this$map$iv2;
                    it = $this$mapTo$iv$iv2.iterator();
                    while (it.hasNext()) {
                    }
                    java.lang.String randomStr2 = kotlin.collections.CollectionsKt.joinToString$default((java.util.List) destination$iv$iv2, "", (java.lang.CharSequence) null, (java.lang.CharSequence) null, 0, (java.lang.CharSequence) null, (kotlin.jvm.functions.Function1) null, 62, (java.lang.Object) null);
                    java.lang.String link2 = videoData3 + randomStr2 + "?token=" + token + "&expiry=" + java.lang.System.currentTimeMillis();
                    kotlin.text.MatchResult matchResultFind$default22 = kotlin.text.Regex.find$default(new kotlin.text.Regex("(\\d{3,4})[pP]"), kotlin.text.StringsKt.substringBefore$default(kotlin.text.StringsKt.substringAfter$default(response02, "<title>", (java.lang.String) null, 2, (java.lang.Object) null), "</title>", (java.lang.String) null, 2, (java.lang.Object) null), 0, 2, (java.lang.Object) null);
                    if (matchResultFind$default22 != null) {
                        java.lang.String videoData22 = getName();
                        java.lang.String name2 = getName();
                        com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                        com.Gayxx.VoeExtractor$dsio$getUrl$2 voeExtractor$dsio$getUrl$22 = new com.Gayxx.VoeExtractor$dsio$getUrl$2(this, quality, null);
                        voeExtractor$dsio$getUrl$12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url3);
                        voeExtractor$dsio$getUrl$12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                        voeExtractor$dsio$getUrl$12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response02);
                        voeExtractor$dsio$getUrl$12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(passMd5Path2);
                        voeExtractor$dsio$getUrl$12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(token);
                        voeExtractor$dsio$getUrl$12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(md5Url);
                        voeExtractor$dsio$getUrl$12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(res2);
                        voeExtractor$dsio$getUrl$12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(videoData3);
                        voeExtractor$dsio$getUrl$12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(randomStr2);
                        voeExtractor$dsio$getUrl$12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link2);
                        voeExtractor$dsio$getUrl$12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(quality);
                        voeExtractor$dsio$getUrl$12.label = 3;
                        objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(videoData22, name2, link2, infer_type2, voeExtractor$dsio$getUrl$22, voeExtractor$dsio$getUrl$12);
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
    }
}
