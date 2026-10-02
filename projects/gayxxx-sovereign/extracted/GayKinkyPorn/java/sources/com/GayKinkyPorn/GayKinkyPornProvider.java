package com.GayKinkyPorn;

/* JADX INFO: compiled from: GayKinkyPornProvider.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/GayKinkyPorn/GayKinkyPornProvider;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "GayKinkyPorn"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class GayKinkyPornProvider extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.GayKinkyPorn.GayKinkyPorn());
        registerExtractorAPI(new com.GayKinkyPorn.Bigwarp());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI(new com.GayKinkyPorn.VoeExtractor());
        registerExtractorAPI(new com.GayKinkyPorn.dsio());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.DoodstreamCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Doodspro());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Doodyt());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Doodre());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Doodpm());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Dsvplay());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Vidply());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.Doply());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayKinkyPorn.vide0());
        registerExtractorAPI(new com.GayKinkyPorn.FilemoonV2());
    }
}
