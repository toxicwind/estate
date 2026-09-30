package com.iGay69;

/* JADX INFO: compiled from: iGay69Provider.kt */
/* JADX INFO: loaded from: classes.dex */
@com.lagradost.cloudstream3.plugins.CloudstreamPlugin
@kotlin.Metadata(d1 = {"\u0000\u0018\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u00020\u00052\u0006\u0010\u0006\u001a\u00020\u0007H\u0016¨\u0006\b"}, d2 = {"Lcom/iGay69/iGay69Plugin;", "Lcom/lagradost/cloudstream3/plugins/Plugin;", "<init>", "()V", "load", "", "context", "Landroid/content/Context;", "iGay69"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final class iGay69Plugin extends com.lagradost.cloudstream3.plugins.Plugin {
    public void load(@org.jetbrains.annotations.NotNull android.content.Context context) {
        registerMainAPI(new com.iGay69.iGay69());
        registerExtractorAPI(new com.iGay69.Bigwarp());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Voe());
        registerExtractorAPI(new com.iGay69.VoeExtractor());
        registerExtractorAPI(new com.iGay69.dsio());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.DoodstreamCom());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.vide0());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.doodspro());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.doodyt());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.doodre());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.doodpm());
        registerExtractorAPI(new com.iGay69.Lulustream());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Lulustream1());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.Lulustream2());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.luluvid());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.StreamTape());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.watchadsontape());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.MxDrop());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.MixDropCv());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.MixDropIs());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.MixDropSn());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.lagradost.cloudstream3.extractors.MixDrop());
        registerExtractorAPI((com.lagradost.cloudstream3.utils.ExtractorApi) new com.iGay69.mdfx9dc8n());
        registerExtractorAPI(new com.iGay69.FileMoon());
        registerExtractorAPI(new com.iGay69.FilemoonV2());
        registerExtractorAPI(new com.iGay69.FileMoonSx());
        registerExtractorAPI(new com.iGay69.WaawExtractor());
    }
}
