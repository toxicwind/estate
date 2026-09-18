package com.iGay69;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J(\u0010\u000e\u001a\n\u0012\u0004\u0012\u00020\u0010\u0018\u00010\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0014"}, d2 = {"Lcom/iGay69/WaawExtractor;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "iGay69"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractors.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractors.kt\ncom/iGay69/WaawExtractor\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n+ 4 _Sequences.kt\nkotlin/sequences/SequencesKt___SequencesKt\n*L\n1#1,404:1\n1915#2:405\n1916#2:407\n1915#2:408\n1915#2,2:409\n1916#2:411\n1915#2:412\n1916#2:425\n1586#2:430\n1661#2,3:431\n1#3:406\n1342#4,2:413\n1342#4,2:415\n1342#4:417\n1342#4,2:418\n1343#4:420\n1342#4,2:421\n1342#4,2:423\n1342#4,2:426\n1342#4,2:428\n*S KotlinDebug\n*F\n+ 1 Extractors.kt\ncom/iGay69/WaawExtractor\n*L\n352#1:405\n352#1:407\n357#1:408\n358#1:409,2\n357#1:411\n365#1:412\n365#1:425\n391#1:430\n391#1:431,3\n370#1:413,2\n371#1:415,2\n373#1:417\n376#1:418,2\n373#1:420\n381#1:421,2\n382#1:423,2\n386#1:426,2\n387#1:428,2\n*E\n"})
public final class WaawExtractor extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "Waaw";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://waaw.to";

    /* JADX INFO: renamed from: com.iGay69.WaawExtractor$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.iGay69.WaawExtractor", f = "Extractors.kt", i = {0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {343, 392}, m = "getUrl", n = {"url", "referer", "url", "referer", "res", "text", "doc", "found", "$this$map$iv", "$this$mapTo$iv$iv", "destination$iv$iv", "item$iv$iv", "link", "$i$f$map", "$i$f$mapTo", "$i$a$-map-WaawExtractor$getUrl$7"}, nl = {344, 400}, s = {"L$0", "L$1", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$10", "L$11", "I$0", "I$1", "I$2"}, v = 2)
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.iGay69.WaawExtractor.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.iGay69.WaawExtractor.this.getUrl(null, null, (kotlin.coroutines.Continuation) this);
        }
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

    /* JADX WARN: Removed duplicated region for block: B:158:0x048e  */
    /* JADX WARN: Removed duplicated region for block: B:163:0x053c  */
    /* JADX WARN: Removed duplicated region for block: B:20:0x00ff  */
    /* JADX WARN: Removed duplicated region for block: B:22:0x0104  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:161:0x050e -> B:162:0x0526). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) {
        com.iGay69.WaawExtractor.AnonymousClass1 anonymousClass1;
        com.iGay69.WaawExtractor waawExtractor;
        com.iGay69.WaawExtractor.AnonymousClass1 anonymousClass12;
        java.lang.Object $result;
        java.lang.Object obj;
        java.lang.String url2;
        java.lang.String referer2;
        com.lagradost.nicehttp.NiceResponse res;
        org.jsoup.nodes.Document doc;
        java.lang.Object obj2;
        java.lang.String referer3;
        com.lagradost.nicehttp.NiceResponse res2;
        java.lang.Object text;
        java.lang.String url3;
        org.jsoup.nodes.Document doc2;
        java.lang.Iterable item$iv$iv;
        int $i$f$map;
        java.util.Collection destination$iv$iv;
        int $i$f$mapTo;
        java.util.Iterator it;
        java.util.Collection found;
        com.iGay69.WaawExtractor.AnonymousClass1 anonymousClass13;
        java.lang.Object obj3;
        java.lang.String url4;
        com.iGay69.WaawExtractor waawExtractor2;
        com.lagradost.nicehttp.NiceResponse res3;
        kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation2;
        java.lang.Iterable $this$mapTo$iv$iv;
        java.lang.Object text2;
        java.lang.Iterable iterableSelect;
        com.lagradost.nicehttp.NiceResponse res4;
        java.lang.Object text3;
        java.lang.String url5;
        org.jsoup.nodes.Document doc3;
        kotlin.sequences.Sequence $this$forEach$iv;
        int $i$f$forEach;
        java.util.Iterator it2;
        org.jsoup.nodes.Document doc4;
        java.lang.Iterable iterableSelect2;
        java.lang.Iterable iterableSelect3;
        java.lang.Object obj4;
        int $i$f$mapTo2;
        java.lang.Iterable $this$map$iv;
        java.lang.Object $result2;
        java.lang.String url6;
        java.lang.Object $result3;
        java.lang.Object obj5;
        java.util.Collection collection;
        kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation3;
        com.lagradost.nicehttp.NiceResponse res5;
        int $i$f$map2;
        java.util.Collection destination$iv$iv2;
        java.util.Iterator it3;
        java.util.Collection destination$iv$iv3;
        if (continuation instanceof com.iGay69.WaawExtractor.AnonymousClass1) {
            anonymousClass1 = (com.iGay69.WaawExtractor.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                waawExtractor = this;
            } else {
                waawExtractor = this;
                anonymousClass1 = waawExtractor.new AnonymousClass1(continuation);
            }
        }
        com.iGay69.WaawExtractor.AnonymousClass1 anonymousClass14 = anonymousClass1;
        java.lang.Object $result4 = anonymousClass14.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass14.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result4);
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass14.L$0 = url;
                anonymousClass14.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer);
                anonymousClass14.label = 1;
                anonymousClass12 = anonymousClass14;
                $result = $result4;
                obj = coroutine_suspended;
                java.lang.Object obj6 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                if (obj6 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                $result4 = obj6;
                res = (com.lagradost.nicehttp.NiceResponse) $result4;
                if (res.getCode() != 404) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.lang.Object text4 = res.getText();
                try {
                    doc = res.getDocument();
                } catch (java.lang.Exception e) {
                    doc = null;
                }
                java.util.LinkedHashSet found2 = new java.util.LinkedHashSet();
                if (doc != null && (iterableSelect3 = doc.select("iframe[src]")) != null) {
                    java.lang.Iterable $this$forEach$iv2 = iterableSelect3;
                    for (java.lang.Object element$iv : $this$forEach$iv2) {
                        java.lang.String it4 = ((org.jsoup.nodes.Element) element$iv).attr("abs:src");
                        if (it4 != null) {
                            if (kotlin.text.StringsKt.isBlank(it4)) {
                                it4 = null;
                            }
                            if (it4 != null) {
                                found2.add(it4);
                            }
                        }
                    }
                }
                if (doc == null || (iterableSelect2 = doc.select("[data-src],[data-video],[data-url]")) == null) {
                    obj2 = obj;
                    referer3 = referer2;
                } else {
                    java.lang.Iterable $this$forEach$iv3 = iterableSelect2;
                    for (java.lang.Object element$iv2 : $this$forEach$iv3) {
                        org.jsoup.nodes.Element el = (org.jsoup.nodes.Element) element$iv2;
                        java.lang.Object obj7 = obj;
                        java.lang.Iterable $this$forEach$iv4 = kotlin.collections.CollectionsKt.listOf(new java.lang.String[]{"data-src", "data-video", "data-url"});
                        int $i$f$forEach2 = 0;
                        for (java.lang.Object element$iv3 : $this$forEach$iv4) {
                            java.lang.Iterable $this$forEach$iv5 = $this$forEach$iv4;
                            java.lang.String attr = (java.lang.String) element$iv3;
                            int $i$f$forEach3 = $i$f$forEach2;
                            java.lang.String referer4 = referer2;
                            java.lang.String it5 = el.attr("abs:" + attr);
                            if (it5 != null) {
                                if (kotlin.text.StringsKt.isBlank(it5)) {
                                    it5 = null;
                                }
                                if (it5 != null) {
                                    found2.add(it5);
                                }
                            }
                            $this$forEach$iv4 = $this$forEach$iv5;
                            $i$f$forEach2 = $i$f$forEach3;
                            referer2 = referer4;
                        }
                        java.lang.String referer5 = referer2;
                        java.lang.String it6 = el.attr("abs:src");
                        if (it6 != null) {
                            if (kotlin.text.StringsKt.isBlank(it6)) {
                                it6 = null;
                            }
                            if (it6 != null) {
                                found2.add(it6);
                            }
                        }
                        obj = obj7;
                        referer2 = referer5;
                    }
                    obj2 = obj;
                    referer3 = referer2;
                }
                int i = 0;
                if (doc == null || (iterableSelect = doc.select("script")) == null) {
                    res2 = res;
                    text = text4;
                    url3 = url2;
                    doc2 = doc;
                } else {
                    java.lang.Iterable $this$forEach$iv6 = iterableSelect;
                    for (java.lang.Object element$iv4 : $this$forEach$iv6) {
                        org.jsoup.nodes.Element s = (org.jsoup.nodes.Element) element$iv4;
                        java.lang.String data = s.data();
                        java.lang.String str = data;
                        if (str == null || kotlin.text.StringsKt.isBlank(str)) {
                            res4 = res;
                            text3 = text4;
                            url5 = url2;
                            doc3 = doc;
                        } else {
                            java.lang.String unpacked = new com.lagradost.cloudstream3.utils.JsUnpacker(data).unpack();
                            if (unpacked != null) {
                                res4 = res;
                                text3 = text4;
                                url5 = url2;
                                kotlin.sequences.Sequence $this$forEach$iv7 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*"), unpacked, i, 2, (java.lang.Object) null);
                                for (java.lang.Object element$iv5 : $this$forEach$iv7) {
                                    kotlin.text.MatchResult it7 = (kotlin.text.MatchResult) element$iv5;
                                    found2.add(it7.getValue());
                                }
                                kotlin.sequences.Sequence $this$forEach$iv8 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.mp4[^\\s'\"]*"), unpacked, 0, 2, (java.lang.Object) null);
                                for (java.lang.Object element$iv6 : $this$forEach$iv8) {
                                    kotlin.text.MatchResult it8 = (kotlin.text.MatchResult) element$iv6;
                                    found2.add(it8.getValue());
                                    $this$forEach$iv8 = $this$forEach$iv8;
                                }
                                kotlin.sequences.Sequence $this$forEach$iv9 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("[\"']([A-Za-z0-9+/=]{40,})[\"']"), unpacked, 0, 2, (java.lang.Object) null);
                                int $i$f$forEach4 = 0;
                                java.util.Iterator it9 = $this$forEach$iv9.iterator();
                                while (it9.hasNext()) {
                                    java.lang.Object element$iv7 = it9.next();
                                    kotlin.text.MatchResult m = (kotlin.text.MatchResult) element$iv7;
                                    try {
                                        $this$forEach$iv = $this$forEach$iv9;
                                        try {
                                            $i$f$forEach = $i$f$forEach4;
                                            try {
                                                it2 = it9;
                                            } catch (java.lang.Exception e2) {
                                                it2 = it9;
                                            }
                                            try {
                                                java.lang.String decoded = new java.lang.String(java.util.Base64.getDecoder().decode((java.lang.String) m.getGroupValues().get(1)), kotlin.text.Charsets.UTF_8);
                                                doc4 = doc;
                                                try {
                                                    kotlin.sequences.Sequence $this$forEach$iv10 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+"), decoded, 0, 2, (java.lang.Object) null);
                                                    for (java.lang.Object element$iv8 : $this$forEach$iv10) {
                                                        kotlin.text.MatchResult it10 = (kotlin.text.MatchResult) element$iv8;
                                                        java.lang.String decoded2 = decoded;
                                                        found2.add(it10.getValue());
                                                        decoded = decoded2;
                                                        break;
                                                    }
                                                } catch (java.lang.Exception e3) {
                                                }
                                            } catch (java.lang.Exception e4) {
                                                doc4 = doc;
                                            }
                                        } catch (java.lang.Exception e5) {
                                            $i$f$forEach = $i$f$forEach4;
                                            it2 = it9;
                                            doc4 = doc;
                                        }
                                    } catch (java.lang.Exception e6) {
                                        $this$forEach$iv = $this$forEach$iv9;
                                        $i$f$forEach = $i$f$forEach4;
                                        it2 = it9;
                                        doc4 = doc;
                                    }
                                    $this$forEach$iv9 = $this$forEach$iv;
                                    $i$f$forEach4 = $i$f$forEach;
                                    it9 = it2;
                                    doc = doc4;
                                }
                                doc3 = doc;
                            } else {
                                res4 = res;
                                text3 = text4;
                                url5 = url2;
                                doc3 = doc;
                            }
                            kotlin.sequences.Sequence $this$forEach$iv11 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*"), data, 0, 2, (java.lang.Object) null);
                            for (java.lang.Object element$iv9 : $this$forEach$iv11) {
                                kotlin.text.MatchResult it11 = (kotlin.text.MatchResult) element$iv9;
                                found2.add(it11.getValue());
                                $this$forEach$iv11 = $this$forEach$iv11;
                            }
                            kotlin.sequences.Sequence $this$forEach$iv12 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.mp4[^\\s'\"]*"), data, 0, 2, (java.lang.Object) null);
                            for (java.lang.Object element$iv10 : $this$forEach$iv12) {
                                kotlin.text.MatchResult it12 = (kotlin.text.MatchResult) element$iv10;
                                found2.add(it12.getValue());
                                $this$forEach$iv12 = $this$forEach$iv12;
                            }
                        }
                        res = res4;
                        text4 = text3;
                        url2 = url5;
                        doc = doc3;
                        i = 0;
                    }
                    res2 = res;
                    text = text4;
                    url3 = url2;
                    doc2 = doc;
                }
                kotlin.sequences.Sequence $this$forEach$iv13 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.m3u8[^\\s'\"]*"), (java.lang.CharSequence) text, 0, 2, (java.lang.Object) null);
                for (java.lang.Object element$iv11 : $this$forEach$iv13) {
                    kotlin.text.MatchResult it13 = (kotlin.text.MatchResult) element$iv11;
                    found2.add(it13.getValue());
                }
                kotlin.sequences.Sequence $this$forEach$iv14 = kotlin.text.Regex.findAll$default(new kotlin.text.Regex("https?://[^\\s'\"]+\\.mp4[^\\s'\"]*"), (java.lang.CharSequence) text, 0, 2, (java.lang.Object) null);
                for (java.lang.Object element$iv12 : $this$forEach$iv14) {
                    kotlin.text.MatchResult it14 = (kotlin.text.MatchResult) element$iv12;
                    found2.add(it14.getValue());
                }
                if (found2.isEmpty()) {
                    return kotlin.collections.CollectionsKt.emptyList();
                }
                java.util.LinkedHashSet $this$map$iv2 = found2;
                java.util.Collection destination$iv$iv4 = new java.util.ArrayList(kotlin.collections.CollectionsKt.collectionSizeOrDefault($this$map$iv2, 10));
                item$iv$iv = $this$map$iv2;
                $i$f$map = 0;
                destination$iv$iv = destination$iv$iv4;
                $i$f$mapTo = 0;
                it = $this$map$iv2.iterator();
                found = found2;
                anonymousClass13 = anonymousClass12;
                obj3 = obj2;
                url4 = url3;
                waawExtractor2 = this;
                res3 = res2;
                continuation2 = continuation;
                $this$mapTo$iv$iv = $this$map$iv2;
                text2 = text;
                if (it.hasNext()) {
                    java.lang.Object item$iv$iv2 = it.next();
                    java.lang.String link = (java.lang.String) item$iv$iv2;
                    java.lang.String name = waawExtractor2.getName();
                    java.lang.String name2 = waawExtractor2.getName();
                    com.lagradost.cloudstream3.utils.ExtractorLinkType infer_type = com.lagradost.cloudstream3.utils.ExtractorApiKt.getINFER_TYPE();
                    kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation4 = continuation2;
                    com.lagradost.nicehttp.NiceResponse res6 = res3;
                    com.iGay69.WaawExtractor$getUrl$7$1 waawExtractor$getUrl$7$1 = new com.iGay69.WaawExtractor$getUrl$7$1(url4, null);
                    anonymousClass13.L$0 = url4;
                    anonymousClass13.L$1 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(referer3);
                    anonymousClass13.L$2 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(res6);
                    anonymousClass13.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(text2);
                    anonymousClass13.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(doc2);
                    anonymousClass13.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(found);
                    anonymousClass13.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(item$iv$iv);
                    anonymousClass13.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable($this$mapTo$iv$iv);
                    anonymousClass13.L$8 = destination$iv$iv;
                    anonymousClass13.L$9 = it;
                    anonymousClass13.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(item$iv$iv2);
                    anonymousClass13.L$11 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(link);
                    anonymousClass13.L$12 = destination$iv$iv;
                    anonymousClass13.I$0 = $i$f$map;
                    anonymousClass13.I$1 = $i$f$mapTo;
                    anonymousClass13.I$2 = 0;
                    anonymousClass13.label = 2;
                    java.util.Iterator it15 = it;
                    java.lang.Object objNewExtractorLink = com.lagradost.cloudstream3.utils.ExtractorApiKt.newExtractorLink(name2, name, link, infer_type, waawExtractor$getUrl$7$1, anonymousClass13);
                    if (objNewExtractorLink == obj3) {
                        return obj3;
                    }
                    obj4 = objNewExtractorLink;
                    $i$f$mapTo2 = $i$f$mapTo;
                    $this$map$iv = item$iv$iv;
                    $result2 = $result;
                    url6 = url4;
                    $result3 = text2;
                    obj5 = obj3;
                    collection = destination$iv$iv;
                    continuation3 = continuation4;
                    res5 = res6;
                    $i$f$map2 = $i$f$map;
                    destination$iv$iv2 = found;
                    it3 = it15;
                    destination$iv$iv3 = collection;
                    collection.add((com.lagradost.cloudstream3.utils.ExtractorLink) obj4);
                    continuation2 = continuation3;
                    res3 = res5;
                    url4 = url6;
                    obj3 = obj5;
                    $i$f$mapTo = $i$f$mapTo2;
                    item$iv$iv = $this$map$iv;
                    it = it3;
                    found = destination$iv$iv2;
                    $i$f$map = $i$f$map2;
                    destination$iv$iv = destination$iv$iv3;
                    text2 = $result3;
                    $result = $result2;
                    if (it.hasNext()) {
                        return (java.util.List) destination$iv$iv;
                    }
                }
                break;
                break;
            case 1:
                java.lang.String referer6 = (java.lang.String) anonymousClass14.L$1;
                url2 = (java.lang.String) anonymousClass14.L$0;
                kotlin.ResultKt.throwOnFailure($result4);
                anonymousClass12 = anonymousClass14;
                $result = $result4;
                obj = coroutine_suspended;
                referer2 = referer6;
                res = (com.lagradost.nicehttp.NiceResponse) $result4;
                if (res.getCode() != 404) {
                }
                break;
            case 2:
                int i2 = anonymousClass14.I$2;
                int $i$f$mapTo3 = anonymousClass14.I$1;
                int $i$f$map3 = anonymousClass14.I$0;
                collection = (java.util.Collection) anonymousClass14.L$12;
                java.lang.Object obj8 = anonymousClass14.L$10;
                it3 = (java.util.Iterator) anonymousClass14.L$9;
                java.util.Collection destination$iv$iv5 = (java.util.Collection) anonymousClass14.L$8;
                java.lang.Iterable $this$mapTo$iv$iv2 = (java.lang.Iterable) anonymousClass14.L$7;
                java.lang.Iterable $this$map$iv3 = (java.lang.Iterable) anonymousClass14.L$6;
                java.util.Collection found3 = (java.util.LinkedHashSet) anonymousClass14.L$5;
                org.jsoup.nodes.Document doc5 = (org.jsoup.nodes.Document) anonymousClass14.L$4;
                $result3 = (java.lang.String) anonymousClass14.L$3;
                com.lagradost.nicehttp.NiceResponse res7 = (com.lagradost.nicehttp.NiceResponse) anonymousClass14.L$2;
                java.lang.String referer7 = (java.lang.String) anonymousClass14.L$1;
                java.lang.String url7 = (java.lang.String) anonymousClass14.L$0;
                kotlin.ResultKt.throwOnFailure($result4);
                referer3 = referer7;
                destination$iv$iv3 = destination$iv$iv5;
                $this$mapTo$iv$iv = $this$mapTo$iv$iv2;
                doc2 = doc5;
                $result2 = $result4;
                destination$iv$iv2 = found3;
                $i$f$map2 = $i$f$map3;
                url6 = url7;
                anonymousClass13 = anonymousClass14;
                $this$map$iv = $this$map$iv3;
                res5 = res7;
                waawExtractor2 = waawExtractor;
                $i$f$mapTo2 = $i$f$mapTo3;
                continuation3 = continuation;
                obj5 = coroutine_suspended;
                obj4 = $result2;
                collection.add((com.lagradost.cloudstream3.utils.ExtractorLink) obj4);
                continuation2 = continuation3;
                res3 = res5;
                url4 = url6;
                obj3 = obj5;
                $i$f$mapTo = $i$f$mapTo2;
                item$iv$iv = $this$map$iv;
                it = it3;
                found = destination$iv$iv2;
                $i$f$map = $i$f$map2;
                destination$iv$iv = destination$iv$iv3;
                text2 = $result3;
                $result = $result2;
                if (it.hasNext()) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
