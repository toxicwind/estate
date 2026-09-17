package com.Gayxx;

/* JADX INFO: compiled from: Extractor.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0007\b\u0016\u0018\u00002\u00020\u0001:\u0001\u0016B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u00100\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013J\u0010\u0010\u0014\u001a\u00020\u00052\u0006\u0010\u0015\u001a\u00020\u0005H\u0002R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0017"}, d2 = {"Lcom/Gayxx/Bingezove;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "fixJson", "json", "VideoSource", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractor.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractor.kt\ncom/Gayxx/Bingezove\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 AppUtils.kt\ncom/lagradost/cloudstream3/utils/AppUtils\n+ 4 Extensions.kt\ncom/fasterxml/jackson/module/kotlin/ExtensionsKt\n*L\n1#1,451:1\n1915#2:452\n1916#2:460\n23#3,2:453\n15#3:455\n25#3,2:458\n50#4:456\n43#4:457\n*S KotlinDebug\n*F\n+ 1 Extractor.kt\ncom/Gayxx/Bingezove\n*L\n186#1:452\n186#1:460\n196#1:453,2\n196#1:455\n196#1:458,2\n196#1:456\n196#1:457\n*E\n"})
public class Bingezove extends com.lagradost.cloudstream3.utils.ExtractorApi {

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Bingezove";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://bingezove.com";
    private final boolean requiresReferer = true;

    /* JADX INFO: renamed from: com.Gayxx.Bingezove$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Gayxx.Bingezove", f = "Extractor.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3}, l = {172, 179, 198, 211}, m = "getUrl$suspendImpl", n = {"$this", "url", "referer", "$this", "url", "referer", "response", "document", "m3u8", "$i$a$-let-Bingezove$getUrl$2", "$this", "url", "referer", "response", "document", "$this$forEach$iv", "element$iv", "script", "data", "patterns", "pattern", "match", "file", "$i$f$forEach", "$i$a$-forEach-Bingezove$getUrl$3", "$i$a$-let-Bingezove$getUrl$3$1", "$this", "url", "referer", "response", "document", "file", "$i$a$-let-Bingezove$getUrl$4"}, nl = {173, 178, 197, 210}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "I$0", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "L$11", "L$12", "I$0", "I$1", "I$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
        int I$2;
        java.lang.Object L$0;
        java.lang.Object L$1;
        java.lang.Object L$10;
        java.lang.Object L$11;
        java.lang.Object L$12;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Gayxx.Bingezove.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Gayxx.Bingezove.getUrl$suspendImpl(com.Gayxx.Bingezove.this, null, null, (kotlin.coroutines.Continuation) this);
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
    /* JADX INFO: compiled from: Extractor.kt */
    @kotlin.Metadata(d1 = {"\u0000\"\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u000e\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0082\b\u0018\u00002\u00020\u0001B+\u0012\n\b\u0001\u0010\u0002\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0001\u0010\u0004\u001a\u0004\u0018\u00010\u0003\u0012\n\b\u0001\u0010\u0005\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0006\u0010\u0007J\b\u0010\f\u001a\u0004\u0018\u00010\u0003J\u000b\u0010\r\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000e\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u000b\u0010\u000f\u001a\u0004\u0018\u00010\u0003HÆ\u0003J-\u0010\u0010\u001a\u00020\u00002\n\b\u0003\u0010\u0002\u001a\u0004\u0018\u00010\u00032\n\b\u0003\u0010\u0004\u001a\u0004\u0018\u00010\u00032\n\b\u0003\u0010\u0005\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\u0011\u001a\u00020\u00122\b\u0010\u0013\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0014\u001a\u00020\u0015HÖ\u0081\u0004J\n\u0010\u0016\u001a\u00020\u0003HÖ\u0081\u0004R\u0018\u0010\u0002\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u0018\u0010\u0004\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\tR\u0018\u0010\u0005\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\t¨\u0006\u0017"}, d2 = {"Lcom/Gayxx/Bingezove$VideoSource;", "", "file", "", "hls", "url", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V", "getFile", "()Ljava/lang/String;", "getHls", "getUrl", "getVideoUrl", "component1", "component2", "component3", "copy", "equals", "", "other", "hashCode", "", "toString", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
    static final /* data */ class VideoSource {

        @com.fasterxml.jackson.annotation.JsonProperty("file")
        @org.jetbrains.annotations.Nullable
        private final java.lang.String file;

        @com.fasterxml.jackson.annotation.JsonProperty("hls")
        @org.jetbrains.annotations.Nullable
        private final java.lang.String hls;

        @com.fasterxml.jackson.annotation.JsonProperty("url")
        @org.jetbrains.annotations.Nullable
        private final java.lang.String url;

        public static /* synthetic */ com.Gayxx.Bingezove.VideoSource copy$default(com.Gayxx.Bingezove.VideoSource videoSource, java.lang.String str, java.lang.String str2, java.lang.String str3, int i, java.lang.Object obj) {
            if ((i & 1) != 0) {
                str = videoSource.file;
            }
            if ((i & 2) != 0) {
                str2 = videoSource.hls;
            }
            if ((i & 4) != 0) {
                str3 = videoSource.url;
            }
            return videoSource.copy(str, str2, str3);
        }

        @org.jetbrains.annotations.Nullable
        /* JADX INFO: renamed from: component1, reason: from getter */
        public final java.lang.String getFile() {
            return this.file;
        }

        @org.jetbrains.annotations.Nullable
        /* JADX INFO: renamed from: component2, reason: from getter */
        public final java.lang.String getHls() {
            return this.hls;
        }

        @org.jetbrains.annotations.Nullable
        /* JADX INFO: renamed from: component3, reason: from getter */
        public final java.lang.String getUrl() {
            return this.url;
        }

        @org.jetbrains.annotations.NotNull
        public final com.Gayxx.Bingezove.VideoSource copy(@com.fasterxml.jackson.annotation.JsonProperty("file") @org.jetbrains.annotations.Nullable java.lang.String file, @com.fasterxml.jackson.annotation.JsonProperty("hls") @org.jetbrains.annotations.Nullable java.lang.String hls, @com.fasterxml.jackson.annotation.JsonProperty("url") @org.jetbrains.annotations.Nullable java.lang.String url) {
            return new com.Gayxx.Bingezove.VideoSource(file, hls, url);
        }

        public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
            if (this == other) {
                return true;
            }
            if (!(other instanceof com.Gayxx.Bingezove.VideoSource)) {
                return false;
            }
            com.Gayxx.Bingezove.VideoSource videoSource = (com.Gayxx.Bingezove.VideoSource) other;
            return kotlin.jvm.internal.Intrinsics.areEqual(this.file, videoSource.file) && kotlin.jvm.internal.Intrinsics.areEqual(this.hls, videoSource.hls) && kotlin.jvm.internal.Intrinsics.areEqual(this.url, videoSource.url);
        }

        public int hashCode() {
            return ((((this.file == null ? 0 : this.file.hashCode()) * 31) + (this.hls == null ? 0 : this.hls.hashCode())) * 31) + (this.url != null ? this.url.hashCode() : 0);
        }

        @org.jetbrains.annotations.NotNull
        public java.lang.String toString() {
            return "VideoSource(file=" + this.file + ", hls=" + this.hls + ", url=" + this.url + ')';
        }

        public VideoSource(@com.fasterxml.jackson.annotation.JsonProperty("file") @org.jetbrains.annotations.Nullable java.lang.String file, @com.fasterxml.jackson.annotation.JsonProperty("hls") @org.jetbrains.annotations.Nullable java.lang.String hls, @com.fasterxml.jackson.annotation.JsonProperty("url") @org.jetbrains.annotations.Nullable java.lang.String url) {
            this.file = file;
            this.hls = hls;
            this.url = url;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.String getFile() {
            return this.file;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.String getHls() {
            return this.hls;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.String getUrl() {
            return this.url;
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.String getVideoUrl() {
            java.lang.String str = this.hls;
            if (str != null) {
                return str;
            }
            java.lang.String str2 = this.file;
            return str2 == null ? this.url : str2;
        }
    }

    /* JADX WARN: Removed duplicated region for block: B:33:0x01ae  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    static /* synthetic */ java.lang.Object getUrl$suspendImpl(com.Gayxx.Bingezove $this, java.lang.String url, java.lang.String referer, kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.Gayxx.Bingezove.AnonymousClass1 anonymousClass1;
        java.lang.Object obj;
        char c;
        java.lang.Object obj2;
        java.lang.String url2;
        java.lang.String referer2;
        com.Gayxx.Bingezove $this2;
        org.jsoup.nodes.Document document;
        kotlin.text.MatchResult matchResultFind$default;
        java.util.Iterator it;
        org.jsoup.nodes.Element elementSelectFirst;
        java.lang.String file;
        java.lang.Object value;
        java.lang.String file2;
        java.lang.Object objNewExtractorLink;
        java.util.List groupValues;
        java.lang.String m3u8;
        java.lang.Object objNewExtractorLink2;
        if (continuation instanceof com.Gayxx.Bingezove.AnonymousClass1) {
            anonymousClass1 = (com.Gayxx.Bingezove.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
            } else {
                anonymousClass1 = $this.new AnonymousClass1(continuation);
            }
        }
        com.Gayxx.Bingezove.AnonymousClass1 anonymousClass12 = anonymousClass1;
        java.lang.Object $result = anonymousClass12.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass12.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                obj = coroutine_suspended;
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass12.L$0 = $this;
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass12.label = 1;
                c = 1;
                obj2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                anonymousClass12 = anonymousClass12;
                if (obj2 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                $this2 = $this;
                com.lagradost.nicehttp.NiceResponse response = (com.lagradost.nicehttp.NiceResponse) obj2;
                document = response.getDocument();
                boolean z = false;
                int i = 2;
                java.lang.String str = null;
                matchResultFind$default = kotlin.text.Regex.find$default(new kotlin.text.Regex("(https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*)"), response.getText(), 0, 2, (java.lang.Object) null);
                if (matchResultFind$default == null && (m3u8 = matchResultFind$default.getValue()) != null) {
                    java.lang.String name = $this2.getName();
                    java.lang.String name2 = $this2.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                    com.Gayxx.Bingezove$getUrl$2$1 bingezove$getUrl$2$1 = new com.Gayxx.Bingezove$getUrl$2$1($this2, null);
                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(m3u8);
                    anonymousClass12.I$0 = 0;
                    anonymousClass12.label = 2;
                    objNewExtractorLink2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name, name2, m3u8, infer_type, bingezove$getUrl$2$1, anonymousClass12);
                    return objNewExtractorLink2 == obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink2);
                }
                java.lang.Iterable $this$forEach$iv = document.select("script");
                it = $this$forEach$iv.iterator();
                while (it.hasNext()) {
                    java.lang.Object element$iv = it.next();
                    org.jsoup.nodes.Element script = (org.jsoup.nodes.Element) element$iv;
                    int i2 = 0;
                    java.lang.String data = script.data();
                    java.lang.Object $result2 = $result;
                    if (kotlin.text.StringsKt.contains$default(data, "sources", z, i, str)) {
                        kotlin.text.Regex[] regexArr = new kotlin.text.Regex[i];
                        regexArr[0] = new kotlin.text.Regex("sources\\s*:\\s*\\[\\s*(\\{.*?\\})\\s*\\]", kotlin.text.RegexOption.DOT_MATCHES_ALL);
                        regexArr[c] = new kotlin.text.Regex("sources\\s*:\\s*(\\{.*?\\})", kotlin.text.RegexOption.DOT_MATCHES_ALL);
                        java.util.List<kotlin.text.Regex> patterns = kotlin.collections.CollectionsKt.listOf(regexArr);
                        for (kotlin.text.Regex pattern : patterns) {
                            java.util.List patterns2 = patterns;
                            java.util.Iterator it2 = it;
                            kotlin.text.MatchResult matchResultFind$default2 = kotlin.text.Regex.find$default(pattern, data, 0, 2, str);
                            java.lang.String match = (matchResultFind$default2 == null || (groupValues = matchResultFind$default2.getGroupValues()) == null) ? str : (java.lang.String) groupValues.get(1);
                            java.lang.String str2 = match;
                            if (str2 == null || kotlin.text.StringsKt.isBlank(str2)) {
                                it = it2;
                                str = null;
                                patterns = patterns2;
                            } else {
                                com.lagradost.cloudstream3.utils.AppUtils appUtils = com.lagradost.cloudstream3.utils.AppUtils.INSTANCE;
                                java.lang.String value$iv = $this2.fixJson(match);
                                if (value$iv == null) {
                                    value = str;
                                } else {
                                    try {
                                        com.fasterxml.jackson.databind.ObjectMapper $this$readValue$iv$iv$iv = com.lagradost.cloudstream3.MainAPIKt.getMapper();
                                        value = $this$readValue$iv$iv$iv.readValue(value$iv, new com.fasterxml.jackson.core.type.TypeReference<com.Gayxx.Bingezove.VideoSource>() { // from class: com.Gayxx.Bingezove$getUrl$lambda$1$$inlined$tryParseJson$1
                                        });
                                    } catch (java.lang.Exception e) {
                                        value = null;
                                    }
                                }
                                com.Gayxx.Bingezove.VideoSource videoSource = (com.Gayxx.Bingezove.VideoSource) value;
                                if (videoSource != null && (file2 = videoSource.getVideoUrl()) != null) {
                                    java.lang.String name3 = $this2.getName();
                                    java.lang.String name4 = $this2.getName();
                                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type2 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                                    com.Gayxx.Bingezove$getUrl$3$1$1 bingezove$getUrl$3$1$1 = new com.Gayxx.Bingezove$getUrl$3$1$1($this2, null);
                                    anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                                    anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                                    anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                                    anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                                    anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                                    anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$forEach$iv);
                                    anonymousClass12.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(element$iv);
                                    anonymousClass12.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(script);
                                    anonymousClass12.L$8 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(data);
                                    anonymousClass12.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(patterns2);
                                    anonymousClass12.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(pattern);
                                    anonymousClass12.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(match);
                                    anonymousClass12.L$12 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(file2);
                                    anonymousClass12.I$0 = 0;
                                    anonymousClass12.I$1 = i2;
                                    anonymousClass12.I$2 = 0;
                                    anonymousClass12.label = 3;
                                    objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name3, name4, file2, infer_type2, bingezove$getUrl$3$1$1, anonymousClass12);
                                    return objNewExtractorLink == obj ? obj : kotlin.collections.CollectionsKt.listOf(objNewExtractorLink);
                                }
                                it = it2;
                                i2 = i2;
                                str = null;
                                patterns = patterns2;
                            }
                            break;
                        }
                    }
                    it = it;
                    $result = $result2;
                    i = 2;
                    z = false;
                    str = null;
                    c = 1;
                }
                elementSelectFirst = document.selectFirst("source[src]");
                if (elementSelectFirst != null || (file = elementSelectFirst.attr("src")) == null) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.lang.String name5 = $this2.getName();
                java.lang.String name6 = $this2.getName();
                com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type3 = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                com.Gayxx.Bingezove$getUrl$4$1 bingezove$getUrl$4$1 = new com.Gayxx.Bingezove$getUrl$4$1($this2, null);
                anonymousClass12.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this2);
                anonymousClass12.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url2);
                anonymousClass12.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer2);
                anonymousClass12.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(response);
                anonymousClass12.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(document);
                anonymousClass12.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(file);
                anonymousClass12.I$0 = 0;
                anonymousClass12.label = 4;
                $result = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name5, name6, file, infer_type3, bingezove$getUrl$4$1, anonymousClass12);
                return $result == obj ? obj : kotlin.collections.CollectionsKt.listOf($result);
            case 1:
                java.lang.String referer3 = (java.lang.String) anonymousClass12.L$2;
                java.lang.String url3 = (java.lang.String) anonymousClass12.L$1;
                com.Gayxx.Bingezove $this3 = (com.Gayxx.Bingezove) anonymousClass12.L$0;
                kotlin.ResultKt.throwOnFailure($result);
                referer2 = referer3;
                obj = coroutine_suspended;
                url2 = url3;
                c = 1;
                obj2 = $result;
                $this2 = $this3;
                com.lagradost.nicehttp.NiceResponse response2 = (com.lagradost.nicehttp.NiceResponse) obj2;
                document = response2.getDocument();
                boolean z2 = false;
                int i3 = 2;
                java.lang.String str3 = null;
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
                int i4 = anonymousClass12.I$0;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink2 = $result;
            case 3:
                int i5 = anonymousClass12.I$2;
                int i6 = anonymousClass12.I$1;
                int i7 = anonymousClass12.I$0;
                java.lang.Object obj3 = anonymousClass12.L$6;
                kotlin.ResultKt.throwOnFailure($result);
                objNewExtractorLink = $result;
            case 4:
                int i8 = anonymousClass12.I$0;
                kotlin.ResultKt.throwOnFailure($result);
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    private final java.lang.String fixJson(java.lang.String json) {
        return new kotlin.text.Regex(",\\s*\\]").replace(new kotlin.text.Regex(",\\s*\\}").replace(json, "}"), "]");
    }
}
