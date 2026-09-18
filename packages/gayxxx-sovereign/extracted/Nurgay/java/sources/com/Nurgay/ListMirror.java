package com.Nurgay;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000(\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0002\b\u0005\n\u0002\u0010\u000b\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J&\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u00100\u000f2\u0006\u0010\u0011\u001a\u00020\u00052\b\u0010\u0012\u001a\u0004\u0018\u00010\u0005H\u0096@¢\u0006\u0002\u0010\u0013R\u0014\u0010\u0004\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007R\u0014\u0010\b\u001a\u00020\u0005X\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\t\u0010\u0007R\u0014\u0010\n\u001a\u00020\u000bX\u0096D¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\r¨\u0006\u0014"}, d2 = {"Lcom/Nurgay/ListMirror;", "Lcom/lagradost/cloudstream3/utils/ExtractorApi;", "<init>", "()V", "name", "", "getName", "()Ljava/lang/String;", "mainUrl", "getMainUrl", "requiresReferer", "", "getRequiresReferer", "()Z", "getUrl", "", "Lcom/lagradost/cloudstream3/utils/ExtractorLink;", "url", "referer", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "Nurgay"}, k = 1, mv = {2, 3, 0}, xi = 48)
@kotlin.jvm.internal.SourceDebugExtension({"SMAP\nExtractors.kt\nKotlin\n*S Kotlin\n*F\n+ 1 Extractors.kt\ncom/Nurgay/ListMirror\n+ 2 _Collections.kt\nkotlin/collections/CollectionsKt___CollectionsKt\n+ 3 fake.kt\nkotlin/jvm/internal/FakeKt\n*L\n1#1,409:1\n1642#2,10:410\n1915#2:420\n1916#2:422\n1652#2:423\n296#2,2:424\n1#3:421\n*S KotlinDebug\n*F\n+ 1 Extractors.kt\ncom/Nurgay/ListMirror\n*L\n31#1:410,10\n31#1:420\n31#1:422\n31#1:423\n32#1:424,2\n31#1:421\n*E\n"})
public final class ListMirror extends com.lagradost.cloudstream3.utils.ExtractorApi {
    private final boolean requiresReferer;

    @org.jetbrains.annotations.NotNull
    private final java.lang.String name = "ListMirror";

    @org.jetbrains.annotations.NotNull
    private final java.lang.String mainUrl = "https://listmirror.com";

    /* JADX INFO: renamed from: com.Nurgay.ListMirror$getUrl$1, reason: invalid class name */
    /* JADX INFO: compiled from: Extractors.kt */
    @kotlin.Metadata(k = 3, mv = {2, 3, 0}, xi = 48)
    @kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.Nurgay.ListMirror", f = "Extractors.kt", i = {0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1}, l = {28, 45}, m = "getUrl", n = {"url", "referer", "links", "url", "referer", "links", "doc", "script", "regex", "match", "json", "arr", "obj", "mirrorUrl", "i"}, nl = {31, 41}, s = {"L$0", "L$1", "L$2", "L$0", "L$1", "L$2", "L$3", "L$4", "L$5", "L$6", "L$7", "L$8", "L$9", "L$10", "I$0"}, v = 2)
    static final class AnonymousClass1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
        int I$0;
        int I$1;
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

        AnonymousClass1(kotlin.coroutines.Continuation<? super com.Nurgay.ListMirror.AnonymousClass1> continuation) {
            super(continuation);
        }

        @org.jetbrains.annotations.Nullable
        public final java.lang.Object invokeSuspend(@org.jetbrains.annotations.NotNull java.lang.Object obj) {
            this.result = obj;
            this.label |= Integer.MIN_VALUE;
            return com.Nurgay.ListMirror.this.getUrl(null, null, (kotlin.coroutines.Continuation) this);
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

    /* JADX WARN: Removed duplicated region for block: B:21:0x0110  */
    /* JADX WARN: Removed duplicated region for block: B:28:0x0144  */
    /* JADX WARN: Removed duplicated region for block: B:34:0x0161  */
    /* JADX WARN: Removed duplicated region for block: B:43:0x01a4  */
    /* JADX WARN: Removed duplicated region for block: B:52:0x023f  */
    /* JADX WARN: Removed duplicated region for block: B:58:0x015b A[SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:7:0x0018  */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:48:0x020f -> B:49:0x0221). Please report as a decompilation issue!!! */
    /* JADX WARN: Unsupported multi-entry loop pattern (BACK_EDGE: B:50:0x022e -> B:51:0x0237). Please report as a decompilation issue!!! */
    @org.jetbrains.annotations.Nullable
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public java.lang.Object getUrl(@org.jetbrains.annotations.NotNull java.lang.String url, @org.jetbrains.annotations.Nullable java.lang.String referer, @org.jetbrains.annotations.NotNull kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation) throws org.json.JSONException {
        com.Nurgay.ListMirror.AnonymousClass1 anonymousClass1;
        com.Nurgay.ListMirror listMirror;
        java.lang.Object $result;
        java.util.List links;
        com.Nurgay.ListMirror.AnonymousClass1 anonymousClass12;
        java.lang.Object obj;
        java.lang.String url2;
        java.lang.String referer2;
        java.util.Iterator it;
        java.lang.String json;
        java.lang.Object element$iv;
        java.lang.String script;
        int i;
        int length;
        kotlin.text.Regex regex;
        kotlin.text.MatchResult match;
        java.lang.String script2;
        java.lang.String json2;
        final java.util.List links2;
        kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation2;
        org.json.JSONArray arr;
        com.Nurgay.ListMirror.AnonymousClass1 anonymousClass13;
        com.Nurgay.ListMirror listMirror2;
        org.jsoup.nodes.Document doc;
        java.util.List groupValues;
        java.lang.String url3;
        com.Nurgay.ListMirror.AnonymousClass1 anonymousClass14;
        com.Nurgay.ListMirror listMirror3;
        java.lang.String url4;
        java.lang.String script3;
        kotlin.text.Regex regex2;
        kotlin.text.MatchResult match2;
        java.lang.String json3;
        org.json.JSONArray arr2;
        if (continuation instanceof com.Nurgay.ListMirror.AnonymousClass1) {
            anonymousClass1 = (com.Nurgay.ListMirror.AnonymousClass1) continuation;
            if ((anonymousClass1.label & Integer.MIN_VALUE) != 0) {
                anonymousClass1.label -= Integer.MIN_VALUE;
                listMirror = this;
            } else {
                listMirror = this;
                anonymousClass1 = listMirror.new AnonymousClass1(continuation);
            }
        }
        java.lang.Object $result2 = anonymousClass1.result;
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (anonymousClass1.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result2);
                java.util.List links3 = new java.util.ArrayList();
                com.lagradost.nicehttp.Requests app = com.lagradost.cloudstream3.MainActivityKt.getApp();
                anonymousClass1.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url);
                anonymousClass1.L$1 = referer;
                anonymousClass1.L$2 = links3;
                anonymousClass1.label = 1;
                $result = $result2;
                links = links3;
                anonymousClass12 = anonymousClass1;
                obj = coroutine_suspended;
                $result2 = com.lagradost.nicehttp.Requests.get$default(app, url, (java.util.Map) null, (java.lang.String) null, (java.util.Map) null, (java.util.Map) null, false, 0, (java.util.concurrent.TimeUnit) null, 0L, (okhttp3.Interceptor) null, false, (com.lagradost.nicehttp.ResponseParser) null, anonymousClass12, 4094, (java.lang.Object) null);
                if ($result2 == obj) {
                    return obj;
                }
                url2 = url;
                referer2 = referer;
                org.jsoup.nodes.Document doc2 = ((com.lagradost.nicehttp.NiceResponse) $result2).getDocument();
                java.lang.Iterable $this$mapNotNull$iv = doc2.select("script");
                java.util.Collection destination$iv$iv = new java.util.ArrayList();
                for (java.lang.Object element$iv$iv$iv : $this$mapNotNull$iv) {
                    org.jsoup.nodes.Element it2 = (org.jsoup.nodes.Element) element$iv$iv$iv;
                    java.lang.String strData = it2.data();
                    if (strData != null) {
                        destination$iv$iv.add(strData);
                    }
                }
                java.lang.Iterable $this$firstOrNull$iv = (java.util.List) destination$iv$iv;
                it = $this$firstOrNull$iv.iterator();
                while (true) {
                    json = null;
                    if (it.hasNext()) {
                        element$iv = null;
                    } else {
                        element$iv = it.next();
                        java.lang.String it3 = (java.lang.String) element$iv;
                        if (kotlin.text.StringsKt.contains$default(it3, "sources", false, 2, (java.lang.Object) null)) {
                        }
                    }
                }
                script = (java.lang.String) element$iv;
                if (script != null) {
                    kotlin.text.Regex regex3 = new kotlin.text.Regex("sources\\s*=\\s*(\\[.*?]);", kotlin.text.RegexOption.DOT_MATCHES_ALL);
                    kotlin.text.MatchResult match3 = kotlin.text.Regex.find$default(regex3, script, 0, 2, (java.lang.Object) null);
                    if (match3 != null && (groupValues = match3.getGroupValues()) != null) {
                        json = (java.lang.String) groupValues.get(1);
                    }
                    if (json != null) {
                        org.json.JSONArray arr3 = new org.json.JSONArray(json);
                        i = 0;
                        length = arr3.length();
                        regex = regex3;
                        match = match3;
                        script2 = script;
                        json2 = json;
                        links2 = links;
                        continuation2 = continuation;
                        coroutine_suspended = obj;
                        arr = arr3;
                        anonymousClass13 = anonymousClass12;
                        listMirror2 = listMirror;
                        doc = doc2;
                        $result2 = $result;
                        if (i >= length) {
                            org.json.JSONObject obj2 = arr.getJSONObject(i);
                            kotlin.coroutines.Continuation<? super java.util.List<? extends com.lagradost.cloudstream3.utils.ExtractorLink>> continuation3 = continuation2;
                            java.lang.String mirrorUrl = obj2.optString("url");
                            if (kotlin.text.StringsKt.isBlank(mirrorUrl)) {
                                continuation2 = continuation3;
                                url3 = url2;
                                i++;
                                url2 = url3;
                                if (i >= length) {
                                }
                            } else {
                                kotlin.jvm.functions.Function1 function1 = new kotlin.jvm.functions.Function1() { // from class: com.Nurgay.ListMirror$$ExternalSyntheticLambda0
                                    public final java.lang.Object invoke(java.lang.Object obj3) {
                                        return kotlin.Unit.INSTANCE;
                                    }
                                };
                                java.lang.Object $result3 = $result2;
                                kotlin.jvm.functions.Function1 function12 = new kotlin.jvm.functions.Function1() { // from class: com.Nurgay.ListMirror$$ExternalSyntheticLambda1
                                    public final java.lang.Object invoke(java.lang.Object obj3) {
                                        return com.Nurgay.ListMirror.getUrl$lambda$3(links2, (com.lagradost.cloudstream3.utils.ExtractorLink) obj3);
                                    }
                                };
                                java.lang.String url5 = url2;
                                anonymousClass13.L$0 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(url5);
                                anonymousClass13.L$1 = referer2;
                                anonymousClass13.L$2 = links2;
                                anonymousClass13.L$3 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(doc);
                                anonymousClass13.L$4 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(script2);
                                anonymousClass13.L$5 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(regex);
                                anonymousClass13.L$6 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(match);
                                anonymousClass13.L$7 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(json2);
                                anonymousClass13.L$8 = arr;
                                anonymousClass13.L$9 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(obj2);
                                anonymousClass13.L$10 = kotlin.coroutines.jvm.internal.SpillingKt.nullOutSpilledVariable(mirrorUrl);
                                anonymousClass13.I$0 = i;
                                anonymousClass13.I$1 = length;
                                anonymousClass13.label = 2;
                                if (com.lagradost.cloudstream3.utils.ExtractorApiKt.loadExtractor(mirrorUrl, referer2, function1, function12, anonymousClass13) == coroutine_suspended) {
                                    return coroutine_suspended;
                                }
                                $result2 = $result3;
                                anonymousClass14 = anonymousClass13;
                                listMirror3 = listMirror2;
                                url4 = url5;
                                script3 = script2;
                                regex2 = regex;
                                match2 = match;
                                json3 = json2;
                                arr2 = arr;
                                continuation2 = continuation3;
                                com.Nurgay.ListMirror.AnonymousClass1 anonymousClass15 = anonymousClass14;
                                url3 = url4;
                                anonymousClass13 = anonymousClass15;
                                arr = arr2;
                                json2 = json3;
                                match = match2;
                                regex = regex2;
                                script2 = script3;
                                listMirror2 = listMirror3;
                                i++;
                                url2 = url3;
                                if (i >= length) {
                                    return links2;
                                }
                            }
                        }
                    }
                }
                return links;
            case 1:
                java.util.List links4 = (java.util.List) anonymousClass1.L$2;
                referer2 = (java.lang.String) anonymousClass1.L$1;
                url2 = (java.lang.String) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result2);
                links = links4;
                anonymousClass12 = anonymousClass1;
                $result = $result2;
                obj = coroutine_suspended;
                org.jsoup.nodes.Document doc22 = ((com.lagradost.nicehttp.NiceResponse) $result2).getDocument();
                java.lang.Iterable $this$mapNotNull$iv2 = doc22.select("script");
                java.util.Collection destination$iv$iv2 = new java.util.ArrayList();
                while (r13.hasNext()) {
                }
                java.lang.Iterable $this$firstOrNull$iv2 = (java.util.List) destination$iv$iv2;
                it = $this$firstOrNull$iv2.iterator();
                while (true) {
                    json = null;
                    if (it.hasNext()) {
                    }
                }
                script = (java.lang.String) element$iv;
                if (script != null) {
                }
                return links;
            case 2:
                int i2 = anonymousClass1.I$1;
                int i3 = anonymousClass1.I$0;
                org.json.JSONArray arr4 = (org.json.JSONArray) anonymousClass1.L$8;
                java.lang.String json4 = (java.lang.String) anonymousClass1.L$7;
                kotlin.text.MatchResult match4 = (kotlin.text.MatchResult) anonymousClass1.L$6;
                kotlin.text.Regex regex4 = (kotlin.text.Regex) anonymousClass1.L$5;
                java.lang.String script4 = (java.lang.String) anonymousClass1.L$4;
                org.jsoup.nodes.Document doc3 = (org.jsoup.nodes.Document) anonymousClass1.L$3;
                java.util.List links5 = (java.util.List) anonymousClass1.L$2;
                java.lang.String referer3 = (java.lang.String) anonymousClass1.L$1;
                java.lang.String url6 = (java.lang.String) anonymousClass1.L$0;
                kotlin.ResultKt.throwOnFailure($result2);
                listMirror3 = listMirror;
                regex2 = regex4;
                script3 = script4;
                anonymousClass14 = anonymousClass1;
                json3 = json4;
                match2 = match4;
                url4 = url6;
                length = i2;
                arr2 = arr4;
                referer2 = referer3;
                continuation2 = continuation;
                i = i3;
                links2 = links5;
                doc = doc3;
                com.Nurgay.ListMirror.AnonymousClass1 anonymousClass152 = anonymousClass14;
                url3 = url4;
                anonymousClass13 = anonymousClass152;
                arr = arr2;
                json2 = json3;
                match = match2;
                regex = regex2;
                script2 = script3;
                listMirror2 = listMirror3;
                i++;
                url2 = url3;
                if (i >= length) {
                }
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }

    static final kotlin.Unit getUrl$lambda$3(java.util.List $links, com.lagradost.cloudstream3.utils.ExtractorLink link) {
        $links.add(link);
        return kotlin.Unit.INSTANCE;
    }
}
