package com.GayStream;

/* JADX INFO: compiled from: GayStreamProvider.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/GayStream/GayStreamProvider;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "GayStream"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class GayStreamProvider extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.GayStream.GayStream());
        registerExtractorAPI(new com.GayStream.Bigwarp());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI(new com.GayStream.VoeExtractor());
        registerExtractorAPI(new com.GayStream.dsio());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayStream.DoodstreamCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayStream.vide0());
        registerExtractorAPI(new com.GayStream.ListMirror());
        registerExtractorAPI(new com.GayStream.FilemoonV2());
        registerExtractorAPI(new com.GayStream.FileMoonSx());
        registerExtractorAPI(new com.GayStream.byseqekaho());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.VidhideExtractor());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.GayStream.Space());
    }
}
