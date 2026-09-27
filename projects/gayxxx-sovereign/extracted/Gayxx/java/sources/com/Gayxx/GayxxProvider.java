package com.Gayxx;

/* JADX INFO: compiled from: GayxxProvider.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/Gayxx/GayxxProvider;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "Gayxx"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class GayxxProvider extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.Gayxx.Gayxx());
        registerExtractorAPI(new com.Gayxx.VoeExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.DoodLaExtractor());
        registerExtractorAPI(new com.Gayxx.vvide0Extractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Gayxx.dsio());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Gayxx.Doply());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI(new com.Gayxx.Bingezove());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.Gayxx.luluvid());
        registerExtractorAPI(new com.Gayxx.Lulustream());
        registerExtractorAPI(new com.Gayxx.FilemoonV2());
        registerExtractorAPI(new com.Gayxx.FileMoon());
        registerExtractorAPI(new com.Gayxx.AbyssExtractor());
        registerExtractorAPI(new com.Gayxx.GaybbExtractor());
    }
}
